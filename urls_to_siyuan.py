"""
结合 urls_to_markdown.py 和 create_notes_from_md.py：
1. 将剪贴板中的URL或本地批处理文件转换为markdown文件；
2. 将MD目录下markdown文件导入到思源笔记；
3. 将MD目录下的md文件移动到"已转思源"目录

支持多种HTML转Markdown转换方式：
- markdownify: 使用markdownify库转换
- html2text: 使用html2text库转换
- builtin: 使用内置转换器
- all: 使用所有三种方式各生成一份，文件名添加后缀区分
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
import shutil
import asyncio
from typing import Dict, List, Optional
from urllib import error, request

# 导入相关脚本的main函数
import urls_to_markdown
import create_notes_from_md

# 导入日志模块和转换器
from utilities import setup_logging, URLToMarkdownConverter, DEFAULT_API_URL

# 导入配置模块
from config import get_config, get_urls_path

# 获取配置
config = get_config()

# markdown文件导出目录
DEFAULT_MD_FOLDER = str(get_urls_path())
# 默认转换方式, 可选: markdownify, html2text, builtin, all; all 表示使用所有三种方式各生成一份，文件名添加后缀区分
DEFAULT_CONVERTER_LIB = "markdownify"

# 支持的转换方式
SUPPORTED_CONVERTERS = ["markdownify", "html2text", "builtin", "all"]
DEFAULT_DISCOVERY_TIMEOUT = 2.0
DEFAULT_EXCLUDE_WORKSPACE_KEYWORDS = ("test",)
logger = setup_logging()


def parse_args():
    parser = argparse.ArgumentParser(description="将URL批量转换并导入SiYuan")
    parser.add_argument("--url-batch-file", help="包含 URL 或 {title,url} 列表的本地 JSON/TXT 文件")
    return parser.parse_args()


def get_converter_config():
    """从环境变量或配置获取转换器设置"""
    converter_lib = os.getenv("CONVERTER_LIB", DEFAULT_CONVERTER_LIB)

    # 验证转换器选项
    if converter_lib not in SUPPORTED_CONVERTERS:
        logger.warning(f"不支持的转换器: {converter_lib}，使用默认: {DEFAULT_CONVERTER_LIB}")
        converter_lib = DEFAULT_CONVERTER_LIB

    return converter_lib


async def convert_urls_with_multiple_converters(output_dir, download_media=True, url_batch_file=None):
    """使用多种转换器转换URL"""
    converters_to_use = ["markdownify", "html2text", "builtin"]
    converter_suffixes = {
        "markdownify": "_markdownify",
        "html2text": "_html2text",
        "builtin": "_builtin"
    }

    all_successful_files = []

    for converter_lib in converters_to_use:
        logger.info(f"\n--- 使用 {converter_lib} 转换器 ---")

        # 创建转换器
        converter = URLToMarkdownConverter(
            output_dir=output_dir,
            converter_lib=converter_lib
        )

        # 检查输入源
        if not url_batch_file and not converter.is_clipboard_available():
            logger.error("❌ 错误: pyperclip库未安装，请运行: pip install pyperclip")
            continue

        try:
            if url_batch_file:
                successful_files = await converter.convert_urls_from_file(url_batch_file, download_media=download_media)
            else:
                successful_files = await converter.convert_urls_from_clipboard(download_media=download_media)

            # 为文件添加转换器后缀
            if successful_files:
                suffix = converter_suffixes[converter_lib]
                renamed_files = []

                for file_path in successful_files:
                    # 生成新文件名（添加转换器后缀）
                    new_name = file_path.stem + suffix + file_path.suffix
                    new_path = file_path.parent / new_name

                    # 重命名文件
                    if new_path.exists():
                        new_path.unlink()  # 删除已存在的文件
                    file_path.rename(new_path)
                    renamed_files.append(new_path)

                    logger.info(f"  ✓ 生成文件: {new_path.name}")

                all_successful_files.extend(renamed_files)
                logger.info(f"✅ {converter_lib} 转换完成，生成 {len(renamed_files)} 个文件")
            else:
                logger.warning(f"⚠️ {converter_lib} 转换器没有生成任何文件")

        except Exception as e:
            logger.error(f"❌ {converter_lib} 转换器执行失败: {e}")

    return all_successful_files


def step1_urls_to_markdown(url_batch_file=None):
    """步骤1：调用urls_to_markdown转换功能，支持多种转换方式"""
    logger.info("=== 步骤1：URL转换为Markdown文件 ===")

    # 获取转换器配置
    converter_lib = get_converter_config()
    logger.info(f"使用转换器: {converter_lib}")

    try:
        if converter_lib == "all":
            # 使用所有三种转换器
            logger.info("使用所有转换器各生成一份文件...")
            output_dir = DEFAULT_MD_FOLDER
            successful_files = asyncio.run(
                convert_urls_with_multiple_converters(output_dir, url_batch_file=url_batch_file)
            )

            if successful_files:
                logger.info(f"✅ 总共生成 {len(successful_files)} 个文件")
                return True
            else:
                logger.error("❌ 没有成功生成任何文件")
                return False
        else:
            # 使用指定的单一转换器
            # 创建自定义转换器实例
            converter = URLToMarkdownConverter(
                output_dir=DEFAULT_MD_FOLDER,
                converter_lib=converter_lib
            )

            if not url_batch_file and not converter.is_clipboard_available():
                logger.error("❌ 错误: pyperclip库未安装，请运行: pip install pyperclip")
                return False

            # 异步转换
            async def convert():
                if url_batch_file:
                    return await converter.convert_urls_from_file(url_batch_file, download_media=True)
                return await converter.convert_urls_from_clipboard(download_media=True)

            successful_files = asyncio.run(convert())

            if successful_files:
                logger.info(f"✅ 使用 {converter_lib} 转换完成，生成 {len(successful_files)} 个文件")
                return True
            else:
                logger.error("❌ 没有成功转换任何文件")
                return False

    except SystemExit as e:
        # 处理sys.exit()调用
        if e.code == 0:
            return True
        else:
            logger.error(f"❌ URL转换执行失败，退出码: {e.code}")
            return False

    except Exception as e:
        logger.error(f"调用URL转换时发生异常: {e}")
        return False


def normalize_api_url(api_url: Optional[str]) -> str:
    """标准化 API 地址格式。"""
    if not api_url:
        return ""
    return str(api_url).rstrip("/")


def parse_bool_env(env_name: str, default: bool = False) -> bool:
    """读取布尔型环境变量。"""
    value = os.getenv(env_name)
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def get_workspace_leaf_name(workspace_path: str) -> str:
    """获取工作空间路径的最后一级目录名。"""
    if not workspace_path:
        return ""
    return os.path.basename(str(workspace_path).rstrip("/\\"))


def matches_workspace(workspace_path: str, workspace_name: str) -> bool:
    """判断工作空间是否匹配指定名称。"""
    if not workspace_path or not workspace_name:
        return False

    normalized_expected = workspace_name.lower()
    normalized_workspace = workspace_path.lower()
    workspace_leaf = get_workspace_leaf_name(workspace_path).lower()
    return workspace_leaf == normalized_expected or normalized_expected in normalized_workspace


def is_excluded_workspace(workspace_path: str, exclude_workspace_keywords: List[str]) -> bool:
    """判断工作空间是否命中过滤关键字。"""
    if not workspace_path:
        return False

    normalized_workspace = workspace_path.lower()
    workspace_leaf = get_workspace_leaf_name(workspace_path).lower()
    return any(
        keyword in normalized_workspace or keyword in workspace_leaf
        for keyword in exclude_workspace_keywords
    )


def get_discovery_settings() -> Dict[str, object]:
    """从环境变量读取实例发现设置。"""
    workspace_name = (os.getenv("SIYUAN_WORKSPACE_NAME") or "").strip()
    raw_keywords = os.getenv("SIYUAN_EXCLUDE_WORKSPACE_KEYWORDS", "")
    exclude_keywords = [
        keyword.strip().lower()
        for keyword in raw_keywords.split(",")
        if keyword.strip()
    ]
    probe_timeout = DEFAULT_DISCOVERY_TIMEOUT
    raw_timeout = os.getenv("SIYUAN_DISCOVERY_TIMEOUT")
    if raw_timeout:
        try:
            probe_timeout = float(raw_timeout)
        except ValueError:
            logger.warning("SIYUAN_DISCOVERY_TIMEOUT=%s 不是有效数字，使用默认值 %s", raw_timeout, DEFAULT_DISCOVERY_TIMEOUT)

    return {
        "workspace_name": workspace_name,
        "strict_workspace_match": parse_bool_env("SIYUAN_STRICT_WORKSPACE_MATCH", default=False),
        "exclude_workspace_keywords": exclude_keywords or list(DEFAULT_EXCLUDE_WORKSPACE_KEYWORDS),
        "probe_timeout": probe_timeout,
    }


def get_kernel_process_command_lines() -> List[str]:
    """获取本机 SiYuan-Kernel 进程的命令行参数。"""
    try:
        if sys.platform == "win32":
            script = " ".join(
                [
                    "$ErrorActionPreference = 'Stop';",
                    "Get-CimInstance Win32_Process",
                    "| Where-Object { $_.Name -eq 'SiYuan-Kernel.exe' }",
                    "| Select-Object -ExpandProperty CommandLine",
                ]
            )
            output = subprocess.check_output(
                ["powershell", "-NoProfile", "-Command", script],
                encoding="utf-8",
                errors="ignore",
            )
            return [line.strip() for line in output.splitlines() if line.strip()]

        output = subprocess.check_output(
            ["ps", "-ax", "-o", "command="],
            encoding="utf-8",
            errors="ignore",
        )
        return [
            line.strip()
            for line in output.splitlines()
            if line.strip() and "SiYuan-Kernel" in line
        ]
    except Exception:
        return []


def parse_kernel_command_line(command_line: str) -> Dict[str, object]:
    """从命令行中提取 port 和 workspace。"""
    port_match = re.search(r"--port(?:=|\s+)(\d+)", command_line, flags=re.IGNORECASE)
    workspace_match = re.search(
        r"--workspace(?:=|\s+)(?:\"([^\"]+)\"|'([^']+)'|(\S+))",
        command_line,
        flags=re.IGNORECASE,
    )
    return {
        "port": int(port_match.group(1)) if port_match else None,
        "workspace": (
            workspace_match.group(1)
            or workspace_match.group(2)
            or workspace_match.group(3)
            or ""
        ) if workspace_match else "",
    }


def post_siyuan_api(api_url: str, api_path: str, api_token: str = "", timeout: float = DEFAULT_DISCOVERY_TIMEOUT) -> Optional[dict]:
    """以轻量方式调用思源 API，用于实例探测。"""
    normalized_url = normalize_api_url(api_url)
    if not normalized_url:
        return None

    def send_request(use_token: bool) -> Optional[dict]:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "siyuan-scripts/urls_to_siyuan",
        }
        if use_token and api_token:
            headers["Authorization"] = "Token {token}".format(token=api_token)

        req = request.Request(
            "{base}{path}".format(base=normalized_url, path=api_path),
            data=b"{}",
            headers=headers,
            method="POST",
        )
        with request.urlopen(req, timeout=timeout) as response:
            if response.status < 200 or response.status >= 300:
                return None
            payload = json.loads(response.read().decode("utf-8", errors="replace"))
            return payload if isinstance(payload, dict) else None

    try:
        return send_request(use_token=True)
    except error.HTTPError as exc:
        if api_token and exc.code in (400, 401, 403):
            try:
                return send_request(use_token=False)
            except (error.URLError, error.HTTPError, TimeoutError, ValueError, OSError):
                return None
        return None
    except (error.URLError, error.HTTPError, TimeoutError, ValueError, OSError):
        return None


def fetch_siyuan_instance_info(api_url: str, api_token: str = "", timeout: float = DEFAULT_DISCOVERY_TIMEOUT) -> Dict[str, object]:
    """探测思源实例是否可访问，并优先读取工作空间信息。"""
    workspace_payload = post_siyuan_api(
        api_url,
        "/api/system/getWorkspaceInfo",
        api_token=api_token,
        timeout=timeout,
    )
    workspace_dir = ""
    if workspace_payload and workspace_payload.get("code") == 0:
        data = workspace_payload.get("data") or {}
        if isinstance(data, dict):
            workspace_dir = str(data.get("workspaceDir") or "").strip()
        return {
            "ok": True,
            "workspace": workspace_dir,
            "source": "workspace-info",
        }

    version_payload = post_siyuan_api(
        api_url,
        "/api/system/version",
        api_token=api_token,
        timeout=timeout,
    )
    return {
        "ok": bool(version_payload and version_payload.get("code") == 0),
        "workspace": workspace_dir,
        "source": "version",
    }


def resolve_siyuan_api_url(
    configured_api_url: Optional[str] = None,
    api_token: str = "",
    workspace_name: str = "",
    strict_workspace_match: bool = False,
    exclude_workspace_keywords: Optional[List[str]] = None,
    probe_timeout: float = DEFAULT_DISCOVERY_TIMEOUT,
) -> str:
    """自动选择一个可连接的正式思源实例。"""
    configured_api_url = normalize_api_url(
        configured_api_url or os.getenv("SIYUAN_API_URL") or DEFAULT_API_URL
    )
    exclude_workspace_keywords = [
        keyword.strip().lower()
        for keyword in (exclude_workspace_keywords or list(DEFAULT_EXCLUDE_WORKSPACE_KEYWORDS))
        if keyword and keyword.strip()
    ] or list(DEFAULT_EXCLUDE_WORKSPACE_KEYWORDS)

    command_lines = get_kernel_process_command_lines()
    process_candidates = []
    seen_urls = set()
    instance_infos = {}

    for command_line in command_lines:
        parsed = parse_kernel_command_line(command_line)
        if not parsed["port"]:
            continue

        api_url = "http://127.0.0.1:{port}".format(port=parsed["port"])
        if api_url in seen_urls:
            continue
        seen_urls.add(api_url)
        process_candidates.append(
            {
                "api_url": api_url,
                "workspace": parsed["workspace"],
            }
        )

    if configured_api_url and configured_api_url not in seen_urls:
        process_candidates.append(
            {
                "api_url": configured_api_url,
                "workspace": "",
            }
        )

    if not process_candidates:
        return configured_api_url

    for candidate in process_candidates:
        try:
            instance_info = fetch_siyuan_instance_info(
                candidate["api_url"],
                api_token=api_token,
                timeout=probe_timeout,
            )
        except OSError as exc:
            logger.warning("探测思源实例失败，已跳过 %s: %s", candidate["api_url"], exc)
            instance_info = {
                "ok": False,
                "workspace": candidate.get("workspace", ""),
                "source": "probe-error",
            }
        instance_infos[candidate["api_url"]] = instance_info
        workspace = str(instance_info.get("workspace") or candidate.get("workspace") or "")
        candidate["workspace"] = workspace
        candidate["excluded"] = is_excluded_workspace(workspace, exclude_workspace_keywords)
        candidate["matches_workspace"] = matches_workspace(workspace, workspace_name)
        candidate["reachable"] = bool(instance_info.get("ok"))

    reachable_candidates = [
        candidate for candidate in process_candidates if candidate["reachable"]
    ]
    if not reachable_candidates:
        raise RuntimeError("未找到可连接的思源实例，请确认正式工作空间对应的思源已启动且 API 可访问")

    matching_candidates = [
        candidate
        for candidate in reachable_candidates
        if candidate["matches_workspace"] and not candidate["excluded"]
    ]
    if matching_candidates:
        preferred_candidates = matching_candidates
    elif workspace_name and strict_workspace_match:
        raise RuntimeError("未找到工作空间匹配 {name} 的正式思源实例".format(name=workspace_name))
    else:
        preferred_candidates = [
            candidate for candidate in reachable_candidates if not candidate["excluded"]
        ]

    if not preferred_candidates:
        excluded_workspaces = sorted(
            {
                get_workspace_leaf_name(candidate["workspace"])
                or candidate["workspace"]
                or candidate["api_url"]
                for candidate in reachable_candidates
                if candidate["excluded"]
            }
        )
        joined = ", ".join(excluded_workspaces) if excluded_workspaces else "未知工作空间"
        raise RuntimeError("仅发现工作空间名称包含 test 的思源实例，已停止导入: {workspaces}".format(workspaces=joined))

    for candidate in preferred_candidates:
        if instance_infos[candidate["api_url"]].get("ok"):
            return candidate["api_url"]

    raise RuntimeError("未找到可连接的正式思源实例，请确认正式工作空间对应的思源已启动且 API 可访问")


def step2_import_to_siyuan(md_folder=DEFAULT_MD_FOLDER):
    """步骤2：调用create_notes_from_md.py的main函数将md文件导入到思源笔记"""
    logger.info("\n=== 步骤2：导入Markdown文件到思源笔记 ===")

    try:
        discovery_settings = get_discovery_settings()
        api_token = os.getenv("SIYUAN_API_TOKEN", "")
        resolved_api_url = resolve_siyuan_api_url(
            configured_api_url=os.getenv("SIYUAN_API_URL") or DEFAULT_API_URL,
            api_token=api_token,
            workspace_name=discovery_settings["workspace_name"],
            strict_workspace_match=discovery_settings["strict_workspace_match"],
            exclude_workspace_keywords=discovery_settings["exclude_workspace_keywords"],
            probe_timeout=discovery_settings["probe_timeout"],
        )
        logger.info("将使用思源实例: %s", resolved_api_url)

        # 直接调用create_notes_from_md的main函数
        result = create_notes_from_md.main(
            md_folder,
            api_url=resolved_api_url,
            api_token=api_token,
        )
        if not isinstance(result, dict):
            logger.error("❌ create_notes_from_md.py 未返回结构化结果")
            return False
        if result.get("error", 0) > 0:
            logger.error("❌ create_notes_from_md.py 导入失败: %s", result.get("message", "未知错误"))
            return False
        if result.get("success", 0) <= 0:
            logger.error("❌ create_notes_from_md.py 未成功导入任何文件")
            return False
        return True

    except SystemExit as e:
        # 处理sys.exit()调用
        if e.code == 0:
            return True
        else:
            logger.error(f"❌ create_notes_from_md.py 执行失败，退出码: {e.code}")
            return False

    except Exception as e:
        logger.error(f"思源实例探测或导入过程中发生异常: {e}")
        return False


def step3_move_files():
    """步骤3：将MD目录下的所有文件和目录移动到"已转思源"目录"""
    logger.info("\n=== 步骤3：移动已导入笔记到\"已转思源\"目录 ===")

    # 获取MD文件夹路径
    md_folder = os.getenv("MD_FOLDER", DEFAULT_MD_FOLDER)
    md_path = Path(md_folder)

    if not md_path.exists():
        logger.warning(f"MD文件夹不存在: {md_folder}")
        return True  # 不算失败，可能没有文件需要移动

    try:
        # 确保目标目录存在
        target_dir = md_path.parent / "已转思源"
        target_dir.mkdir(parents=True, exist_ok=True)

        # 获取所有文件和目录
        items = list(md_path.iterdir())
        moved_count = 0

        # 逐个移动文件和目录
        for item in items:
            target_item = target_dir / item.name

            # 如果目标已存在，先删除
            if target_item.exists():
                if target_item.is_dir():
                    shutil.rmtree(target_item)
                else:
                    target_item.unlink()

            # 移动文件或目录
            item.rename(target_item)
            moved_count += 1

        if moved_count > 0:
            logger.info(f"✅ 已将 {moved_count} 个文件移动到: {target_dir}")
        else:
            logger.info("📁 没有文件需要移动")

        return True

    except Exception as move_error:
        logger.error(f"移动MD文件失败: {move_error}")
        return False

def main(argv=None):
    """主函数：执行完整的转换流程"""
    global logger

    if argv is None:
        args = parse_args()
    else:
        parser = argparse.ArgumentParser(description="将URL批量转换并导入SiYuan")
        parser.add_argument("--url-batch-file", help="包含 URL 或 {title,url} 列表的本地 JSON/TXT 文件")
        args = parser.parse_args(argv)
    # 设置日志
    logger = setup_logging()

    # 显示当前配置
    converter_lib = get_converter_config()
    print(f"\n🔧 当前转换器设置: {converter_lib}")
    print(f"📁 输出目录: {DEFAULT_MD_FOLDER}")

    try:
        # 步骤1：URL转换为Markdown
        if not step1_urls_to_markdown(url_batch_file=args.url_batch_file):
            logger.error("❌ 步骤1失败，终止流程")
            return 1

        # 步骤2：导入到思源笔记
        if not step2_import_to_siyuan():
            logger.error("❌ 步骤2失败，终止流程")
            return 1

        # 步骤3：移动文件到已转思源目录
        if not step3_move_files():
            logger.error("❌ 步骤3失败，但前面步骤已完成")
            return 1

        logger.info("🎉 完整转换流程执行成功！")
        return 0

    except KeyboardInterrupt:
        logger.info("程序被用户中断")
        return 0
    except Exception as e:
        logger.error(f"程序执行失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
