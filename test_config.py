#!/usr/bin/env python3
"""
配置系统测试脚本
"""

def test_config_system():
    """测试配置系统"""
    print("🧪 开始测试配置系统...")
    
    try:
        # 测试导入配置模块
        print("1. 测试导入配置模块...")
        from config import get_config, get_wiznotes_path, get_urls_path
        print("   ✅ 配置模块导入成功")
        
        # 测试获取配置实例
        print("2. 测试获取配置实例...")
        config = get_config()
        print("   ✅ 配置实例获取成功")
        
        # 测试配置属性
        print("3. 测试配置属性...")
        print(f"   基础导出目录: {config.base_export_dir}")
        print(f"   为知笔记子目录: {config.export_subdirs['wiznotes']}")
        print(f"   URL子目录: {config.export_subdirs['urls']}")
        print("   ✅ 配置属性访问成功")
        
        # 测试路径生成
        print("4. 测试路径生成...")
        wiznotes_path = get_wiznotes_path()
        urls_path = get_urls_path()
        print(f"   为知笔记路径: {wiznotes_path}")
        print(f"   URL路径: {urls_path}")
        print("   ✅ 路径生成成功")
        
        # 测试配置修改
        print("5. 测试配置修改...")
        original_base = config.base_export_dir
        config.update_base_dir("D:/测试目录")
        print(f"   修改后的基础目录: {config.base_export_dir}")
        config.update_base_dir(original_base)
        print(f"   恢复后的基础目录: {config.base_export_dir}")
        print("   ✅ 配置修改成功")
        
        # 测试配置序列化
        print("6. 测试配置序列化...")
        config_dict = config.to_dict()
        print(f"   配置字典键: {list(config_dict.keys())}")
        print("   ✅ 配置序列化成功")
        
        print("\n🎉 所有测试通过！配置系统工作正常。")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_config_system()
