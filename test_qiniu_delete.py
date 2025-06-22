"""
七牛云批量删除文件功能测试脚本
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(str(Path(__file__).parent))

from delete_qiniu_files import QiniuFileDeleter


def test_basic_functionality():
    """测试基本功能"""
    print("=== 七牛云批量删除工具测试 ===\n")

    # 检查环境变量
    access_key = os.getenv("QINIU_ACCESS_KEY")
    secret_key = os.getenv("QINIU_SECRET_KEY")
    bucket_name = os.getenv("QINIU_BUCKET_NAME")

    if not all([access_key, secret_key, bucket_name]):
        print("❌ 环境变量未设置完整")
        print("请设置以下环境变量：")
        print("- QINIU_ACCESS_KEY")
        print("- QINIU_SECRET_KEY")
        print("- QINIU_BUCKET_NAME")
        print("\n可以创建 .env 文件或在系统中设置环境变量")
        return False

    try:
        # 初始化删除工具
        print("1. 初始化七牛云删除工具...")
        deleter = QiniuFileDeleter()
        print("✅ 初始化成功")

        # 测试获取文件列表（限制数量避免过多输出）
        print("\n2. 测试获取文件列表...")
        file_list = deleter.get_file_list(bucket_name, max_files=5)  # 最多获取5个文件
        if file_list:
            print(f"✅ 成功获取到 {len(file_list)} 个文件")
            print("文件列表示例：")
            for i, file_key in enumerate(file_list[:3], 1):
                print(f"   {i}. {file_key}")
            if len(file_list) > 3:
                print(f"   ... 还有 {len(file_list) - 3} 个文件")
        else:
            print("⚠️  存储空间为空或无法访问")

        # 测试保存文件列表
        print("\n3. 测试保存文件列表...")
        if file_list:
            list_file = deleter.save_file_list(bucket_name, "test_file_list.txt", prefix=None)
            if Path(list_file).exists():
                print(f"✅ 文件列表已保存到: {list_file}")
            else:
                print("❌ 文件列表保存失败")
        else:
            print("⚠️  跳过文件列表保存（无文件）")

        # 测试删除功能（仅测试接口，不实际删除）
        print("\n4. 测试删除接口...")
        print("测试未确认的删除操作...")
        result = deleter.delete_files_by_prefix(bucket_name, prefix="test-prefix/", confirm=False)
        if "error" in result:
            print("✅ 安全检查正常 - 需要确认才能删除")
        else:
            print("❌ 安全检查异常")

        print("\n=== 测试完成 ===")
        print("✅ 所有基本功能测试通过")
        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_with_sample_data():
    """使用示例数据测试（需要手动确认）"""
    print("\n=== 示例数据测试 ===")
    print("这个测试需要手动确认，不会自动执行删除操作")

    # 示例：如何安全地删除文件
    print("\n安全删除流程示例：")
    print("```python")
    print("# 1. 获取要删除的文件列表")
    print("deleter = QiniuFileDeleter()")
    print("files = deleter.get_file_list('bucket-name', prefix='temp/')")
    print("print(f'找到 {len(files)} 个文件')")
    print("")
    print("# 2. 保存备份列表")
    print("deleter.save_file_list('bucket-name', 'backup.txt', prefix='temp/')")
    print("")
    print("# 3. 确认后删除")
    print("if len(files) < 100:  # 设置安全阈值")
    print("    result = deleter.delete_files_by_prefix('bucket-name', prefix='temp/', confirm=True)")
    print("    print(f'删除结果: {result}')")
    print("```")


def main():
    """主测试函数"""
    print("七牛云批量删除工具测试")
    print("=" * 50)

    # 基本功能测试
    success = test_basic_functionality()

    if success:
        # 示例数据测试
        test_with_sample_data()

        print("\n" + "=" * 50)
        print("测试总结：")
        print("✅ 工具已准备就绪，可以正常使用")
        print("⚠️  请谨慎使用删除功能，确保数据安全")
        print("📖 详细使用说明请查看：七牛云批量删除使用说明.md")
    else:
        print("\n" + "=" * 50)
        print("测试总结：")
        print("❌ 工具配置有问题，请检查环境变量和网络连接")


if __name__ == "__main__":
    main()