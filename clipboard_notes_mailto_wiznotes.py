"""从剪贴板文本中分离提取出微信公众号、头条号、小红书、网页文章链接和其他内容，批量保存到为知笔记"""
import json
import time
import re
import requests
import pyperclip
import yagmail
import pathlib
import os
from dotenv import load_dotenv


def read_mail_account(mailhost):
    """从.env文件读取邮箱帐号信息，mailhost可取['189', '163', '139', 'qq']之一"""
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
        raise ValueError(f"缺少环境变量: {', '.join(missing_vars)}")

    return host, user, password, receiver


def split_notes(clipboard_notes):
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
        if '\n' not in block:
            if block.startswith("https://mp.weixin.qq.com") or block.startswith("http://mp.weixin.qq.com") and block not in article_links:
                article_links.append(block)
            elif block.startswith("https://m.toutiao.com") and block not in article_links:
                block = '"' + re.sub(r"\?=.*", "", block) + '"'
                article_links.append(block)
            elif "http://xhslink" in block and block not in article_links:
                block = re.search(r"(http://xhslink.*?)，", block).group(1)
                url = requests.get(block).url    # 获取重定向后网址
                article_links.append(url)
            elif block.startswith("https://") and block not in article_links:
                article_links.append(block)
            elif block and block not in other_notes:
                other_notes += block + '\n%%%\n'
        else:
            other_notes += block + '\n%%%\n'
    return article_links, other_notes


def send_mail(mailhost, mailuser, mailpassword, mailreceiver, clipboard_notes):
    """
    将笔记内容和链接发送邮件到为知笔记
    """
    article_links, other_notes = split_notes(clipboard_notes)

    print(f'发现{len(article_links)}条文章链接。')
    if other_notes.strip():
        article_links.append(other_notes)

    # 将文章链接和其他文本分批发送到为知笔记
    date = time.strftime("%Y%m%d", time.localtime())
    yag_server = yagmail.SMTP(user=mailuser, password=mailpassword, host=mailhost)
    count = 1
    while count <= len(article_links):
        try:
            if article_links[count-1].strip():
                yag_server.send(to=mailreceiver, subject=f'碎笔记{date}', contents=[article_links[count-1]])
                print(f'已发送{count}/{len(article_links)}封邮件到为知笔记({article_links[count-1].strip()})……')
                time.sleep(0.5)
                count += 1
        except Exception as e:
            print(e)
    yag_server.close()

    try:
        pyperclip.copy(article_links[-1])  # 文本内容复制到剪贴板作为备份，规避敏感词等问题导致邮件发送不成功
        print(f'碎笔记内容如下：\n{article_links[-1]}')
        print(f'已发送全部{len(article_links)}封邮件，并将碎笔记文本内容复制到剪贴板。')
    except Exception as e:
        print('没有发现有效笔记。')


if __name__ == "__main__":
    mailhost = '189'    # mailhost可取['189', 'qq', '139']之一
    clipboard_notes = pyperclip.paste()

    mailhost, mailuser, mailpassword, mailreceiver = read_mail_account(mailhost)
    send_mail(mailhost, mailuser, mailpassword, mailreceiver, clipboard_notes)
