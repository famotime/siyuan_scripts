"""从剪贴板文本中分离提取出微信公众号、头条号、小红书、网页文章链接和其他内容，批量保存到为知笔记"""
import time
import re
import requests
import pyperclip
import yagmail
from pathlib import Path
from dotenv import load_dotenv
import os
import logging
from typing import Tuple, List


def setup_logging():
    """设置日志记录"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('mail_sender.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)


def check_env_file():
    """检查.env文件是否存在，如果不存在则提示用户创建"""
    env_path = Path('.env')
    example_path = Path('.env.example')

    if not env_path.exists():
        print("❌ 未找到 .env 配置文件")
        if example_path.exists():
            print(f"💡 请将 {example_path} 复制为 .env 并填入您的邮箱配置信息")
        else:
            print("💡 请创建 .env 文件并配置邮箱信息，参考格式：")
            print("MAIL_189_HOST=smtp.189.cn")
            print("MAIL_189_USER=your_email@189.cn")
            print("MAIL_189_PASSWORD=your_password")
            print("MAIL_RECEIVER=your_wiznote_email@mywiz.cn")
        return False
    return True


def read_mail_account(mailhost: str) -> Tuple[str, str, str, str]:
    """从.env文件读取邮箱帐号信息，mailhost可取['189', '163', '139', 'qq']之一"""
    if not check_env_file():
        raise FileNotFoundError("配置文件 .env 不存在")

    load_dotenv()

    # 根据mailhost构建环境变量名
    host_key = f'MAIL_{mailhost.upper()}_HOST'
    user_key = f'MAIL_{mailhost.upper()}_USER'
    password_key = f'MAIL_{mailhost.upper()}_PASSWORD'
    receiver_key = 'MAIL_RECEIVER'

    host = os.getenv(host_key)
    user = os.getenv(user_key)
    password = os.getenv(password_key)
    receiver = os.getenv(receiver_key)

    if not all([host, user, password, receiver]):
        missing_vars = []
        if not host: missing_vars.append(host_key)
        if not user: missing_vars.append(user_key)
        if not password: missing_vars.append(password_key)
        if not receiver: missing_vars.append(receiver_key)
        raise ValueError(f"❌ 缺少环境变量: {', '.join(missing_vars)}")

    return host, user, password, receiver


def get_redirect_url(url: str) -> str:
    """获取重定向后的URL"""
    try:
        response = requests.get(url, timeout=10, allow_redirects=True)
        return response.url
    except requests.RequestException as e:
        logging.warning(f"获取重定向URL失败: {url}, 错误: {e}")
        return url


def split_notes(clipboard_notes: str) -> Tuple[List[str], str]:
    """分离微信、头条、小红书文章链接和其他笔记内容

    这个函数用于处理剪贴板中的文本内容,将其分成三类:
    1. article_links: 存储各类文章链接(微信公众号、头条号、小红书等)
    2. other_notes: 存储其他文本内容

    处理逻辑:
    - 首先按 %%% 或换行符分割文本块
    - 对每个文本块:
      - 如果是单行文本,则根据URL特征判断类型:
        * 微信公众号链接(https://mp.weixin.qq.com开头)
        * 头条号链接(https://m.toutiao.com开头,去掉参数)
        * 小红书链接(包含xhslink,获取重定向后的真实URL)
        * 其他https链接
        * 普通文本(添加到other_notes)
      - 如果是多行文本,直接添加到other_notes

    Args:
        clipboard_notes: 剪贴板中的文本内容

    Returns:
        tuple: (article_links, other_notes)
        - article_links: 文章链接列表
        - other_notes: 其他文本内容
    """
    article_links = []
    other_notes = ''
    splitter = '%%%' if '%%%' in clipboard_notes else '\n'

    for block in clipboard_notes.split(splitter):
        block = block.strip()
        if not block:
            continue

        if '\n' not in block:
            if (block.startswith("https://mp.weixin.qq.com") or
                block.startswith("http://mp.weixin.qq.com")) and block not in article_links:
                article_links.append(block)
            elif block.startswith("https://m.toutiao.com") and block not in article_links:
                # 清理头条链接参数
                clean_url = re.sub(r"\?.*", "", block)
                article_links.append(f'"{clean_url}"')
            elif "http://xhslink" in block and block not in article_links:
                # 处理小红书链接
                match = re.search(r"(http://xhslink[^\s，,]*)", block)
                if match:
                    xhs_url = match.group(1)
                    real_url = get_redirect_url(xhs_url)
                    article_links.append(real_url)
            elif block.startswith("https://") and block not in article_links:
                article_links.append(block)
            elif block and block not in other_notes:
                other_notes += block + '\n%%%\n'
        else:
            other_notes += block + '\n%%%\n'

    return article_links, other_notes


def send_mail(mailhost: str, mailuser: str, mailpassword: str, mailreceiver: str, clipboard_notes: str) -> bool:
    """
    将笔记内容和链接发送邮件到为知笔记

    Returns:
        bool: 是否发送成功
    """
    logger = logging.getLogger(__name__)

    try:
        article_links, other_notes = split_notes(clipboard_notes)

        logger.info(f'发现{len(article_links)}条文章链接。')
        if other_notes.strip():
            article_links.append(other_notes)

        if not article_links:
            logger.warning("没有发现有效的文章链接或笔记内容")
            return False

        # 将文章链接和其他文本分批发送到为知笔记
        date = time.strftime("%Y%m%d", time.localtime())

        try:
            yag_server = yagmail.SMTP(user=mailuser, password=mailpassword, host=mailhost)
            logger.info(f"✅ 成功连接到邮件服务器: {mailhost}")
        except Exception as e:
            logger.error(f"❌ 连接邮件服务器失败: {e}")
            return False

        success_count = 0
        total_count = len(article_links)

        for index, content in enumerate(article_links, 1):
            if not content.strip():
                continue

            try:
                yag_server.send(
                    to=mailreceiver,
                    subject=f'碎笔记{date}',
                    contents=[content]
                )
                success_count += 1
                content_preview = content[:50] + "..." if len(content) > 50 else content
                logger.info(f'✅ 已发送{index}/{total_count}封邮件到为知笔记({content_preview})')
                time.sleep(0.5)  # 避免发送过快
            except Exception as e:
                logger.error(f"❌ 发送第{index}封邮件失败: {e}")
                logger.error(f"失败内容预览: {content[:100]}")

        yag_server.close()

        # 备份到剪贴板
        if article_links and other_notes.strip():
            try:
                pyperclip.copy(other_notes)
                logger.info(f'📋 已将碎笔记文本内容复制到剪贴板作为备份')
            except Exception as e:
                logger.warning(f"复制到剪贴板失败: {e}")

        if success_count > 0:
            logger.info(f'✅ 成功发送{success_count}/{total_count}封邮件')
            return True
        else:
            logger.error("❌ 所有邮件发送失败")
            return False

    except Exception as e:
        logger.error(f"❌ 发送邮件过程中出现错误: {e}")
        return False


def main():
    """主函数"""
    logger = setup_logging()

    try:
        # 配置邮件服务商
        mailhost = '189'    # mailhost可取['189', 'qq', '139', '163']之一

        # 获取剪贴板内容
        clipboard_notes = pyperclip.paste()
        if not clipboard_notes.strip():
            logger.warning("⚠️  剪贴板为空，没有内容可发送")
            return

        logger.info(f"📋 从剪贴板获取内容，长度: {len(clipboard_notes)} 字符")

        # 读取邮箱配置
        mailhost, mailuser, mailpassword, mailreceiver = read_mail_account(mailhost)
        logger.info(f"📧 使用邮箱: {mailuser} -> {mailreceiver}")

        # 发送邮件
        success = send_mail(mailhost, mailuser, mailpassword, mailreceiver, clipboard_notes)

        if success:
            print("\n🎉 邮件发送完成！")
        else:
            print("\n❌ 邮件发送失败，请检查日志文件 mail_sender.log")

    except FileNotFoundError:
        print("❌ 配置文件不存在，请先创建 .env 文件")
    except ValueError as e:
        print(f"❌ 配置错误: {e}")
    except Exception as e:
        logger.error(f"❌ 程序运行出错: {e}")
        print(f"❌ 运行出错: {e}")


if __name__ == "__main__":
    main()
