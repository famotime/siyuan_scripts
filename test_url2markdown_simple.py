"""
简单的url2markdown功能测试
测试基本的转换功能和媒体下载功能
"""

import asyncio
import sys
from pathlib import Path
from url2markdown import AdvancedWebToMarkdownConverter


async def test_basic_conversion():
    """测试基本转换功能"""
    print("=== 测试基本转换功能 ===")

    converter = AdvancedWebToMarkdownConverter(output_dir="test_output")

    # 使用一个简单的测试页面
    test_url = "https://httpbin.org/html"  # 简单的HTML测试页面

    print(f"转换测试页面: {test_url}")

    try:
        result_path = await converter.convert_url_to_markdown(
            test_url,
            "test_basic.md",
            download_media=False  # 这个页面没有媒体文件
        )

        if result_path and result_path.exists():
            print(f"✓ 基本转换测试成功: {result_path}")

            # 读取并显示内容概要
            content = result_path.read_text(encoding='utf-8')
            lines = content.split('\n')
            print(f"  文件行数: {len(lines)}")
            print(f"  文件大小: {len(content)} 字符")

            # 显示前几行
            print("  文件开头内容:")
            for i, line in enumerate(lines[:5], 1):
                print(f"    {i}: {line}")

            return True
        else:
            print("✗ 基本转换测试失败")
            return False

    except Exception as e:
        print(f"✗ 基本转换测试出错: {e}")
        return False


async def test_media_download():
    """测试媒体下载功能"""
    print("\n=== 测试媒体下载功能 ===")

    converter = AdvancedWebToMarkdownConverter(output_dir="test_output")

    # 使用一个包含图片的简单页面
    test_url = "https://httpbin.org/html"

    print(f"转换包含媒体的页面: {test_url}")

    try:
        result_path = await converter.convert_url_to_markdown(
            test_url,
            "test_media.md",
            download_media=True
        )

        if result_path and result_path.exists():
            print(f"✓ 媒体下载测试完成: {result_path}")

            # 检查媒体目录
            media_dir = converter.output_dir / "media"
            if media_dir.exists():
                media_files = list(media_dir.glob("*"))
                print(f"  下载的媒体文件数量: {len(media_files)}")

                if media_files:
                    print("  媒体文件:")
                    for media_file in media_files[:5]:  # 只显示前5个
                        file_size = media_file.stat().st_size
                        print(f"    - {media_file.name} ({file_size} bytes)")
            else:
                print("  没有媒体文件需要下载")

            return True
        else:
            print("✗ 媒体下载测试失败")
            return False

    except Exception as e:
        print(f"✗ 媒体下载测试出错: {e}")
        return False


async def test_different_converters():
    """测试不同的转换器"""
    print("\n=== 测试不同转换器 ===")

    test_url = "https://httpbin.org/html"

    converters_to_test = ["auto", "markdownify", "html2text"]
    results = {}

    for converter_lib in converters_to_test:
        print(f"\n测试 {converter_lib} 转换器...")

        try:
            converter = AdvancedWebToMarkdownConverter(
                output_dir="test_output",
                converter_lib=converter_lib
            )

            filename = f"test_{converter_lib}.md"
            result_path = await converter.convert_url_to_markdown(
                test_url,
                filename,
                download_media=False
            )

            if result_path and result_path.exists():
                file_size = result_path.stat().st_size
                print(f"✓ {converter_lib} 转换成功，文件大小: {file_size} 字节")
                results[converter_lib] = True
            else:
                print(f"✗ {converter_lib} 转换失败")
                results[converter_lib] = False

        except Exception as e:
            print(f"✗ {converter_lib} 转换出错: {e}")
            results[converter_lib] = False

    # 总结结果
    successful = sum(results.values())
    total = len(results)
    print(f"\n转换器测试结果: {successful}/{total} 个成功")

    return successful > 0


async def test_error_handling():
    """测试错误处理"""
    print("\n=== 测试错误处理 ===")

    converter = AdvancedWebToMarkdownConverter(output_dir="test_output")

    # 测试无效URL
    invalid_url = "https://this-domain-does-not-exist-12345.com"

    print(f"测试无效URL: {invalid_url}")

    try:
        result_path = await converter.convert_url_to_markdown(
            invalid_url,
            "test_error.md",
            download_media=False
        )

        if result_path is None:
            print("✓ 错误处理测试成功 - 正确返回None")
            return True
        else:
            print("✗ 错误处理测试失败 - 应该返回None")
            return False

    except Exception as e:
        print(f"✓ 错误处理测试成功 - 捕获异常: {type(e).__name__}")
        return True


async def cleanup_test_files():
    """清理测试文件"""
    print("\n=== 清理测试文件 ===")

    test_dir = Path("test_output")
    if test_dir.exists():
        import shutil
        try:
            shutil.rmtree(test_dir)
            print("✓ 测试文件已清理")
        except Exception as e:
            print(f"清理测试文件时出错: {e}")


def print_system_info():
    """打印系统信息"""
    print("=== 系统信息 ===")
    print(f"Python版本: {sys.version}")

    # 检查依赖库
    try:
        import requests
        print(f"✓ requests 已安装")
    except ImportError:
        print("✗ requests 未安装")

    try:
        import aiohttp
        print(f"✓ aiohttp 已安装")
    except ImportError:
        print("✗ aiohttp 未安装")

    try:
        import aiofiles
        print(f"✓ aiofiles 已安装")
    except ImportError:
        print("✗ aiofiles 未安装")

    try:
        from bs4 import BeautifulSoup
        print(f"✓ BeautifulSoup 已安装")
    except ImportError:
        print("✗ BeautifulSoup 未安装")

    try:
        import markdownify
        print(f"✓ markdownify 已安装")
    except ImportError:
        print("✗ markdownify 未安装")

    try:
        import html2text
        print(f"✓ html2text 已安装")
    except ImportError:
        print("✗ html2text 未安装")


async def run_all_tests():
    """运行所有测试"""
    print("URL到Markdown转换器测试程序")
    print("=" * 50)

    # 打印系统信息
    print_system_info()

    # 运行测试
    tests = [
        ("基本转换功能", test_basic_conversion),
        ("媒体下载功能", test_media_download),
        ("不同转换器", test_different_converters),
        ("错误处理", test_error_handling),
    ]

    results = {}

    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"✗ 测试 {test_name} 出现未处理异常: {e}")
            results[test_name] = False

    # 总结测试结果
    print(f"\n{'='*50}")
    print("测试结果总结:")

    successful_tests = 0
    total_tests = len(tests)

    for test_name, result in results.items():
        status = "✓ 通过" if result else "✗ 失败"
        print(f"  {test_name}: {status}")
        if result:
            successful_tests += 1

    print(f"\n总体结果: {successful_tests}/{total_tests} 个测试通过")

    if successful_tests == total_tests:
        print("🎉 所有测试都通过了！")
    elif successful_tests > 0:
        print("⚠️  部分测试通过，请检查失败的测试")
    else:
        print("❌ 所有测试都失败了，请检查环境配置")

    # 询问是否清理测试文件
    try:
        response = input("\n是否清理测试文件？(y/n): ").lower().strip()
        if response in ['y', 'yes', '是']:
            await cleanup_test_files()
    except (EOFError, KeyboardInterrupt):
        print("\n跳过清理步骤")


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试程序出错: {e}")
        sys.exit(1)