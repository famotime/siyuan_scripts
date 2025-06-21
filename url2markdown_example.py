"""
url2markdown 使用示例
演示如何使用 AdvancedWebToMarkdownConverter 类
"""

import asyncio
from url2markdown import AdvancedWebToMarkdownConverter
from pathlib import Path


async def example_basic_usage():
    """基本使用示例"""
    print("=== 基本使用示例 ===")

    # 创建转换器
    converter = AdvancedWebToMarkdownConverter(output_dir="example_output")

    # 示例URL（可以替换为任何你想转换的网页）
    test_urls = [
        "https://www.python.org/",
        "https://github.com/",
        "https://stackoverflow.com/questions/tagged/python"
    ]

    for url in test_urls:
        print(f"\n正在转换: {url}")
        try:
            result_path = await converter.convert_url_to_markdown(url)
            if result_path:
                print(f"✓ 转换成功: {result_path}")
                # 显示文件大小
                file_size = result_path.stat().st_size
                print(f"  文件大小: {file_size} 字节")
            else:
                print(f"✗ 转换失败")
        except Exception as e:
            print(f"✗ 转换出错: {e}")


async def example_custom_filename():
    """自定义文件名示例"""
    print("\n=== 自定义文件名示例 ===")

    converter = AdvancedWebToMarkdownConverter(output_dir="example_output")

    url = "https://docs.python.org/3/"
    custom_filename = "python_docs.md"

    print(f"转换 {url} 并保存为 {custom_filename}")
    result_path = await converter.convert_url_to_markdown(url, custom_filename)

    if result_path:
        print(f"✓ 成功保存为: {result_path}")
    else:
        print("✗ 转换失败")


async def example_without_media():
    """不下载媒体文件的示例"""
    print("\n=== 不下载媒体文件示例 ===")

    converter = AdvancedWebToMarkdownConverter(output_dir="example_output")

    url = "https://www.python.org/about/"
    print(f"转换页面但不下载媒体文件: {url}")

    result_path = await converter.convert_url_to_markdown(url, download_media=False)
    if result_path:
        print(f"✓ 转换成功: {result_path}")
    else:
        print("✗ 转换失败")


async def example_different_converters():
    """使用不同转换库的示例"""
    print("\n=== 不同转换库示例 ===")

    url = "https://www.python.org/downloads/"

    # 测试不同的转换器
    converters = [
        ("markdownify", "markdownify转换器"),
        ("html2text", "html2text转换器"),
        ("auto", "自动选择转换器")
    ]

    for converter_lib, description in converters:
        print(f"\n使用 {description}: {converter_lib}")

        converter = AdvancedWebToMarkdownConverter(
            output_dir="converter_test",
            converter_lib=converter_lib
        )

        filename = f"python_downloads_{converter_lib}.md"
        result_path = await converter.convert_url_to_markdown(url, filename)

        if result_path:
            print(f"✓ 转换成功: {result_path}")
            file_size = result_path.stat().st_size
            print(f"  文件大小: {file_size} 字节")
        else:
            print("✗ 转换失败")


async def example_batch_conversion():
    """批量转换示例"""
    print("\n=== 批量转换示例 ===")

    converter = AdvancedWebToMarkdownConverter(output_dir="batch_output")

    # 批量转换的URL列表
    urls_to_convert = [
        ("https://www.python.org/downloads/", "python_downloads.md"),
        ("https://docs.python.org/3/tutorial/", "python_tutorial.md"),
        ("https://pypi.org/", "pypi_homepage.md"),
    ]

    successful_conversions = 0
    total_conversions = len(urls_to_convert)

    for url, filename in urls_to_convert:
        print(f"\n转换 {url} -> {filename}")
        try:
            result_path = await converter.convert_url_to_markdown(url, filename)
            if result_path:
                print(f"✓ 成功")
                successful_conversions += 1

                # 显示媒体文件信息
                media_dir = converter.output_dir / "media"
                if media_dir.exists():
                    media_files = list(media_dir.glob("*"))
                    if media_files:
                        print(f"  下载了 {len(media_files)} 个媒体文件")
            else:
                print(f"✗ 失败")
        except Exception as e:
            print(f"✗ 出错: {e}")

    print(f"\n批量转换完成: {successful_conversions}/{total_conversions} 成功")


async def example_media_rich_page():
    """转换包含大量媒体的页面示例"""
    print("\n=== 媒体丰富页面转换示例 ===")

    converter = AdvancedWebToMarkdownConverter(output_dir="media_test")

    # 使用一个包含图片的页面作为测试
    url = "https://github.com/features"
    print(f"转换包含媒体的页面: {url}")

    result_path = await converter.convert_url_to_markdown(url, "github_features.md")

    if result_path:
        print(f"✓ 转换成功: {result_path}")

        # 检查媒体文件
        media_dir = converter.output_dir / "media"
        if media_dir.exists():
            media_files = list(media_dir.glob("*"))
            print(f"  下载的媒体文件数量: {len(media_files)}")

            if media_files:
                print("  媒体文件列表:")
                for i, media_file in enumerate(media_files[:10], 1):  # 只显示前10个
                    file_size = media_file.stat().st_size
                    print(f"    {i}. {media_file.name} ({file_size} bytes)")

                if len(media_files) > 10:
                    print(f"    ... 还有 {len(media_files) - 10} 个文件")
        else:
            print("  没有下载媒体文件")
    else:
        print("✗ 转换失败")


def view_converted_file(file_path: Path):
    """查看转换后的文件内容（前几行）"""
    if file_path.exists():
        print(f"\n=== {file_path.name} 文件内容预览 ===")
        try:
            content = file_path.read_text(encoding='utf-8')
            lines = content.split('\n')[:25]  # 显示前25行
            for i, line in enumerate(lines, 1):
                print(f"{i:2d}: {line}")

            if len(content.split('\n')) > 25:
                print("... (更多内容)")

            # 显示文件统计信息
            total_lines = len(content.split('\n'))
            total_chars = len(content)
            print(f"\n文件统计: {total_lines} 行, {total_chars} 字符")

        except Exception as e:
            print(f"读取文件出错: {e}")


async def example_performance_test():
    """性能测试示例"""
    print("\n=== 性能测试示例 ===")

    import time

    converter = AdvancedWebToMarkdownConverter(output_dir="performance_test")

    urls = [
        "https://www.python.org/",
        "https://docs.python.org/3/",
        "https://github.com/",
    ]

    print(f"测试并发转换 {len(urls)} 个页面...")
    start_time = time.time()

    # 并发转换
    tasks = []
    for i, url in enumerate(urls):
        filename = f"page_{i+1}.md"
        task = asyncio.create_task(converter.convert_url_to_markdown(url, filename))
        tasks.append((url, task))

    successful = 0
    for url, task in tasks:
        try:
            result = await task
            if result:
                successful += 1
                print(f"✓ {url}")
            else:
                print(f"✗ {url}")
        except Exception as e:
            print(f"✗ {url} - 错误: {e}")

    end_time = time.time()
    elapsed = end_time - start_time

    print(f"\n性能测试结果:")
    print(f"  总耗时: {elapsed:.2f} 秒")
    print(f"  成功转换: {successful}/{len(urls)} 个页面")
    print(f"  平均耗时: {elapsed/len(urls):.2f} 秒/页面")


async def main():
    """主函数"""
    print("URL到Markdown转换器高级示例程序")
    print("=" * 60)

    # 基本使用示例
    await example_basic_usage()

    # 自定义文件名示例
    await example_custom_filename()

    # 不下载媒体文件示例
    await example_without_media()

    # 不同转换库示例
    await example_different_converters()

    # 批量转换示例
    await example_batch_conversion()

    # 媒体丰富页面转换示例
    await example_media_rich_page()

    # 性能测试示例
    await example_performance_test()

    # 查看转换结果
    print("\n=== 查看转换结果示例 ===")
    output_dirs = ["example_output", "batch_output", "media_test"]

    for output_dir_name in output_dirs:
        output_dir = Path(output_dir_name)
        if output_dir.exists():
            md_files = list(output_dir.glob("*.md"))
            if md_files:
                print(f"\n{output_dir_name} 目录中的文件:")
                for md_file in md_files:
                    file_size = md_file.stat().st_size
                    print(f"  - {md_file.name} ({file_size} bytes)")

                # 查看第一个文件的内容
                if md_files:
                    view_converted_file(md_files[0])
                    break

    print(f"\n✓ 高级示例程序运行完成！")
    print(f"转换的文件保存在以下目录:")
    for output_dir_name in output_dirs:
        print(f"  - {output_dir_name}/")

    print(f"\n媒体文件保存在各目录的 media/ 子目录中")


if __name__ == "__main__":
    asyncio.run(main())