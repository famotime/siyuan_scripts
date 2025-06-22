"""
Markdown文件导入器
"""
import os
import re
from pathlib import Path
from urllib.parse import unquote
from typing import Optional
from .common import logger


class MarkdownImporter:
    """Markdown文件导入器"""

    def __init__(self, api_client):
        self.api = api_client
        # 延迟导入避免循环依赖
        from .notebook import NotebookManager
        from .document import DocumentManager
        from .media_manager import MediaManager

        self.notebook_manager = NotebookManager(api_client)
        self.document_manager = DocumentManager(api_client)
        self.media_manager = MediaManager(api_client)

    def convert_soft_breaks_to_hard_breaks(self, content: str) -> str:
        """
        将Markdown文档中的软回车转换为硬回车

        软回车：单个换行符（\n），在Markdown中通常不产生换行效果
        硬回车：两个换行符（\n\n）或行末加两个空格+换行符，在Markdown中产生真正的换行

        :param content: 原始Markdown内容
        :return: 转换后的Markdown内容
        """
        # logger.info("开始转换软回车为硬回车")

        # 按行分割内容
        lines = content.split('\n')
        processed_lines = []

        i = 0
        in_code_block = False

        while i < len(lines):
            current_line = lines[i]

            # 检查是否进入或退出代码块
            stripped_line = current_line.strip()
            if stripped_line.startswith('```'):
                in_code_block = not in_code_block
                processed_lines.append(current_line)
                i += 1
                continue

            # 如果在代码块内，直接添加行，不做任何转换
            if in_code_block:
                processed_lines.append(current_line)
                i += 1
                continue

            # 跳过空行（已经是硬回车）
            if not current_line.strip():
                processed_lines.append(current_line)
                i += 1
                continue

            # 跳过特殊Markdown语法行，这些不需要转换
            # 标题行（# ## ### 等）
            if stripped_line.startswith('#'):
                processed_lines.append(current_line)
                i += 1
                continue

            # 列表项（- * + 或数字列表）
            if (stripped_line.startswith(('- ', '* ', '+ ')) or
                (stripped_line and stripped_line[0].isdigit() and '. ' in stripped_line[:10])):
                processed_lines.append(current_line)
                i += 1
                continue

            # 引用行（>）
            if stripped_line.startswith('>'):
                processed_lines.append(current_line)
                i += 1
                continue

            # 表格行（包含 |）
            if '|' in stripped_line:
                processed_lines.append(current_line)
                i += 1
                continue

            # 水平分割线（--- 或 ***）
            if stripped_line in ('---', '***', '___') or all(c in '-*_' for c in stripped_line):
                processed_lines.append(current_line)
                i += 1
                continue

            # 普通文本行，检查是否需要转换软回车
            # 如果当前行不是空行，且下一行也不是空行，且下一行不是特殊语法行
            # 则在当前行后添加空行（转换为硬回车）
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()

                # 如果下一行是空行，说明已经是硬回车，不需要处理
                if not next_line:
                    processed_lines.append(current_line)
                    i += 1
                    continue

                # 检查下一行是否是特殊语法行
                next_is_special = (
                    next_line.startswith('#') or  # 标题
                    next_line.startswith(('- ', '* ', '+ ')) or  # 列表
                    (next_line and next_line[0].isdigit() and '. ' in next_line[:10]) or  # 数字列表
                    next_line.startswith('```') or  # 代码块
                    next_line.startswith('>') or  # 引用
                    '|' in next_line or  # 表格
                    next_line in ('---', '***', '___') or  # 分割线
                    all(c in '-*_' for c in next_line if next_line)  # 分割线
                )

                # 如果下一行是特殊语法行，不添加空行
                if next_is_special:
                    processed_lines.append(current_line)
                else:
                    # 普通文本行之间添加空行（转换为硬回车）
                    processed_lines.append(current_line)
                    processed_lines.append('')  # 添加空行

            else:
                # 最后一行，直接添加
                processed_lines.append(current_line)

            i += 1

        result = '\n'.join(processed_lines)

        # 统计转换的数量
        original_line_count = len(content.split('\n'))
        new_line_count = len(result.split('\n'))
        added_lines = new_line_count - original_line_count

        # if added_lines > 0:
        #     logger.info(f"✅ 软回车转换完成，添加了 {added_lines} 个硬回车")
        # else:
        #     logger.info("📝 未发现需要转换的软回车")

        return result

    def process_markdown_media(self, content: str, md_file_path: Path) -> str:
        """
        处理Markdown文件中的媒体文件引用，上传到思源笔记并更新链接

        :param content: Markdown内容
        :param md_file_path: MD文件的路径（用于解析相对路径）
        :return: 处理后的Markdown内容
        """
        processed_content = content
        md_dir = md_file_path.parent
        upload_count = 0

        # logger.info(f"开始处理文件中的媒体链接: {md_file_path.name}")

        # 使用贪婪匹配，正确处理路径中的括号
        patterns = [
            # 图片格式：![alt](path) - 贪婪匹配到最后的)
            (r'!\[([^\]]*)\]\((.+\.(?:png|jpg|jpeg|gif|svg|webp|bmp|ico))\)', 'image'),
            # 媒体文件链接格式
            (r'(?<!)!\[([^\]]*)\]\((.+\.(?:mp3|mp4|mov|avi|wav|m4a|aac|ogg|flac|mkv|webm|wmv|flv))\)', 'media'),
        ]

        for pattern, media_type_hint in patterns:
            matches = list(re.finditer(pattern, processed_content, re.IGNORECASE | re.MULTILINE))
            # logger.info(f"找到 {len(matches)} 个 {media_type_hint} 链接匹配")

            # 从后往前替换，避免位置偏移
            for match in reversed(matches):
                try:
                    full_match = match.group(0)
                    alt_text = match.group(1) if len(match.groups()) >= 1 and match.group(1) else ""
                    media_path = match.group(2) if len(match.groups()) >= 2 and match.group(2) else ""

                    if not media_path:
                        logger.debug(f"跳过无效匹配: {full_match}")
                        continue

                    logger.debug(f"处理链接: {full_match}")
                    logger.debug(f"Alt文本: '{alt_text}'")
                    logger.debug(f"媒体路径: {media_path}")
                except IndexError as e:
                    logger.warning(f"正则表达式匹配组错误: {e}")
                    continue

                # 跳过明显是表格内容的匹配（通过检查前后文）
                match_start = max(0, match.start() - 50)
                match_end = min(len(processed_content), match.end() + 50)

                # 更安全的表格检查方法
                try:
                    before_context = processed_content[match_start:match.start()]
                    after_context = processed_content[match.end():match_end]

                    # 如果周围有表格标记，跳过
                    if '|' in before_context[-10:] or '|' in after_context[:10]:
                        logger.debug(f"跳过表格中的引用: {media_path}")
                        continue
                except Exception as e:
                    logger.debug(f"表格检查失败，继续处理: {e}")
                    # 如果检查失败，继续处理

                # 解码URL编码的路径
                try:
                    media_path = unquote(media_path)
                except Exception as e:
                    logger.warning(f"URL解码失败: {media_path}, 错误: {e}")

                # 跳过网络链接
                if media_path.startswith(('http://', 'https://', 'ftp://')):
                    logger.debug(f"跳过网络链接: {media_path}")
                    continue

                # 处理相对路径
                if not os.path.isabs(media_path):
                    full_media_path = md_dir / media_path
                else:
                    full_media_path = Path(media_path)

                # 标准化路径
                try:
                    full_media_path = full_media_path.resolve()
                    # logger.info(f"解析后的完整路径: {full_media_path}")
                except Exception as e:
                    logger.warning(f"路径解析失败: {media_path}, 错误: {e}")
                    continue

                # 检查文件是否存在且是媒体文件
                if full_media_path.exists() and self.media_manager.is_media_file(str(full_media_path)):
                    # logger.info(f"发现媒体文件: {full_media_path.name}")

                    # 上传媒体文件
                    uploaded_path = self.media_manager.upload_asset(str(full_media_path))

                    if uploaded_path:
                        # 替换链接
                        media_type = self.media_manager.get_media_type(str(full_media_path))

                        if media_type == 'image':
                            # 保持原有的格式，只替换路径部分
                            new_link = f'![{alt_text}]({uploaded_path})'
                        else:
                            # 音频和视频文件
                            new_link = f'[{alt_text or full_media_path.name}]({uploaded_path})'

                        # 执行替换 - 使用简单字符串替换而不是正则表达式
                        try:
                            processed_content = processed_content.replace(full_match, new_link)
                            upload_count += 1
                            # logger.info(f"✅ 已更新媒体链接: {media_path} -> {uploaded_path}")
                        except Exception as replace_error:
                            logger.error(f"字符串替换失败: {replace_error}")
                            logger.debug(f"原始匹配: {repr(full_match)}")
                            logger.debug(f"新链接: {repr(new_link)}")
                            continue
                    else:
                        logger.warning(f"❌ 媒体文件上传失败: {full_media_path}\n")
                else:
                    if not full_media_path.exists():
                        logger.warning(f"⚠️ 媒体文件不存在: {full_media_path}\n")
                    elif not self.media_manager.is_media_file(str(full_media_path)):
                        logger.debug(f"跳过非媒体文件: {full_media_path}\n")

        # if upload_count > 0:
        #     logger.info(f"🎉 成功上传并更新了 {upload_count} 个媒体文件的链接")
        # else:
        #     logger.info("未找到需要上传的媒体文件")

        return processed_content

    def import_md_files(self, md_folder: str, notebook_name: str, parent_folder: str = None, upload_media: bool = True, convert_soft_breaks: bool = True) -> dict:
        """
        批量导入MD文件到思源笔记

        :param md_folder: MD文件夹路径
        :param notebook_name: 目标笔记本名称
        :param parent_folder: 父文件夹名称（可选）
        :param upload_media: 是否上传媒体文件
        :param convert_soft_breaks: 是否将软回车转换为硬回车
        :return: 导入结果统计
        """
        md_path = Path(md_folder)
        if not md_path.exists():
            logger.error(f"MD文件夹不存在: {md_folder}")
            return {"success": 0, "error": 1, "message": "文件夹不存在"}

        # 获取或创建笔记本
        notebook_id = self.notebook_manager.find_or_create_notebook(notebook_name)
        if not notebook_id:
            logger.error(f"无法获取或创建笔记本: {notebook_name}")
            return {"success": 0, "error": 1, "message": "笔记本创建失败"}

        # logger.info(f"使用笔记本: {notebook_name} ({notebook_id})")

        # 如果指定了父文件夹，先检查是否已存在，若不存在则创建父文档
        if parent_folder:
            self._create_parent_folder(notebook_id, parent_folder)

        # 获取所有MD文件
        md_files = list(md_path.glob("*.md"))
        if not md_files:
            logger.warning(f"在 {md_folder} 中未找到任何MD文件")
            return {"success": 0, "error": 0, "message": "未找到MD文件"}

        logger.info(f"找到 {len(md_files)} 个MD文件")
        # if upload_media:
        #     logger.info("启用媒体文件上传功能")

        success_count = 0
        error_count = 0
        total_media_uploaded = 0

        for md_file in md_files:
            try:
                # 读取MD文件内容
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # 转换软回车为硬回车（如果启用）
                if convert_soft_breaks:
                    content = self.convert_soft_breaks_to_hard_breaks(content)

                # 处理媒体文件（如果启用）
                if upload_media:
                    original_content = content
                    content = self.process_markdown_media(content, md_file)
                    # 简单统计媒体文件数量变化
                    if content != original_content:
                        total_media_uploaded += content.count('assets/') - original_content.count('assets/')

                # 使用文件名作为文档标题
                title = md_file.stem

                # 构建文档路径
                if parent_folder:
                    # 处理多级路径，确保路径格式正确
                    clean_parent_folder = parent_folder.strip().strip('/')
                    doc_path = f"/{clean_parent_folder}/{title}"
                else:
                    doc_path = f"/{title}"

                # 创建文档
                doc_id = self.document_manager.create_doc_with_md(
                    notebook_id=notebook_id,
                    path=doc_path,
                    markdown=content
                )

                if doc_id:
                    logger.info(f"成功导入: {title}\n")
                    success_count += 1
                else:
                    logger.error(f"导入失败: {title}")
                    error_count += 1

            except Exception as e:
                logger.error(f"导入失败 {md_file.name}: {e}")
                error_count += 1

        result = {
            "success": success_count,
            "error": error_count,
            "total": len(md_files),
            "media_uploaded": total_media_uploaded if upload_media else 0,
            "message": f"导入完成！成功: {success_count}, 失败: {error_count}"
        }

        if upload_media and total_media_uploaded > 0:
            result["message"] += f", 媒体文件: {total_media_uploaded}"

        logger.info(result["message"])
        return result

    def _create_parent_folder(self, notebook_id: str, parent_folder: str) -> Optional[str]:
        """检查父文件夹是否存在，如果不存在则创建（支持多级路径）"""
        # 标准化路径，确保以/开头，去掉末尾的/
        parent_path = parent_folder.strip()
        if not parent_path.startswith('/'):
            parent_path = f"/{parent_path}"
        parent_path = parent_path.rstrip('/')

        # 先检查完整路径的父文档是否已存在
        existing_ids = self.document_manager.get_ids_by_hpath(parent_path, notebook_id)

        if existing_ids:
            logger.info(f"父文档已存在: {parent_path} -> {existing_ids[0]}")
            return existing_ids[0]

        # 如果路径包含多级，需要递归创建父级目录
        path_parts = [part for part in parent_path.split('/') if part]

        if len(path_parts) > 1:
            # 递归创建上级目录
            parent_path_parts = path_parts[:-1]
            upper_parent_path = '/' + '/'.join(parent_path_parts)

            # logger.info(f"检查上级路径: {upper_parent_path}")
            self._create_parent_folder(notebook_id, upper_parent_path)

        # 创建当前级别的文档
        try:
            # 获取当前级别的文件夹名
            folder_name = path_parts[-1] if path_parts else parent_folder

            doc_id = self.document_manager.create_doc_with_md(
                notebook_id=notebook_id,
                path=parent_path,
                markdown=f"# {folder_name}\n\n这是导入文档的集合文件夹。"
            )

            if doc_id:
                logger.info(f"创建父文档: {parent_path} -> {doc_id}")
                return doc_id
            else:
                logger.error(f"创建父文档失败: {parent_path}")
                return None

        except Exception as e:
            logger.warning(f"创建父文档时出错: {e}")
            # 再次尝试检查是否已存在（可能是并发创建或API延迟）
            existing_ids = self.document_manager.get_ids_by_hpath(parent_path, notebook_id)
            if existing_ids:
                logger.info(f"父文档已存在（重新检查）: {parent_path} -> {existing_ids[0]}")
                return existing_ids[0]
            return None