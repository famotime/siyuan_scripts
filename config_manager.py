"""
配置管理工具
提供命令行和交互式界面来管理项目配置
"""

import json
import argparse
from pathlib import Path
from config import get_config, Config

def save_config_to_file(config: Config, file_path: str = "project_config.json"):
    """将配置保存到JSON文件"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)
        print(f"✅ 配置已保存到: {file_path}")
        return True
    except Exception as e:
        print(f"❌ 保存配置失败: {e}")
        return False

def load_config_from_file(config: Config, file_path: str = "project_config.json"):
    """从JSON文件加载配置"""
    try:
        if Path(file_path).exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
            config.from_dict(config_dict)
            print(f"✅ 配置已从文件加载: {file_path}")
            return True
        else:
            print(f"⚠️ 配置文件不存在: {file_path}")
            return False
    except Exception as e:
        print(f"❌ 加载配置失败: {e}")
        return False

def show_current_config(config: Config):
    """显示当前配置"""
    print("\n" + "=" * 60)
    print("📋 当前项目配置")
    print("=" * 60)
    
    print(f"\n📁 基础导出目录: {config.base_export_dir}")
    
    print("\n📂 导出子目录:")
    for key, value in config.export_subdirs.items():
        full_path = config.get_export_path(key)
        print(f"  {key:12}: {value} -> {full_path}")
    
    print("\n📚 思源笔记配置:")
    for key, value in config.siyuan.items():
        print(f"  {key:20}: {value}")
    
    print("\n📧 为知笔记配置:")
    for key, value in config.wiznotes.items():
        print(f"  {key:20}: {value}")
    
    print("\n📎 媒体文件配置:")
    for key, value in config.media.items():
        print(f"  {key:20}: {value}")
    
    print("=" * 60)

def interactive_config_editor(config: Config):
    """交互式配置编辑器"""
    print("\n🔧 交互式配置编辑器")
    print("输入 'help' 查看可用命令，输入 'quit' 退出")
    
    while True:
        try:
            command = input("\n请输入命令: ").strip().lower()
            
            if command == 'quit' or command == 'exit':
                break
            elif command == 'help':
                print_help()
            elif command == 'show':
                show_current_config(config)
            elif command == 'save':
                file_path = input("请输入保存路径 (默认: project_config.json): ").strip()
                if not file_path:
                    file_path = "project_config.json"
                save_config_to_file(config, file_path)
            elif command == 'load':
                file_path = input("请输入配置文件路径: ").strip()
                load_config_from_file(config, file_path)
            elif command == 'base':
                new_base = input(f"请输入新的基础导出目录 (当前: {config.base_export_dir}): ").strip()
                if new_base:
                    config.update_base_dir(new_base)
                    print(f"✅ 基础导出目录已更新为: {new_base}")
            elif command == 'subdir':
                print("可用的子目录键:")
                for key in config.export_subdirs.keys():
                    print(f"  {key}")
                subdir_key = input("请输入要修改的子目录键: ").strip()
                if subdir_key in config.export_subdirs:
                    new_subdir = input(f"请输入新的子目录名 (当前: {config.export_subdirs[subdir_key]}): ").strip()
                    if new_subdir:
                        config.update_subdir(subdir_key, new_subdir)
                        print(f"✅ 子目录 {subdir_key} 已更新为: {new_subdir}")
                else:
                    print(f"❌ 未知的子目录键: {subdir_key}")
            elif command == 'test':
                test_paths(config)
            else:
                print("❌ 未知命令，输入 'help' 查看可用命令")
                
        except KeyboardInterrupt:
            print("\n\n👋 配置编辑器已退出")
            break
        except Exception as e:
            print(f"❌ 执行命令时出错: {e}")

def print_help():
    """打印帮助信息"""
    print("\n📖 可用命令:")
    print("  show     - 显示当前配置")
    print("  save     - 保存配置到文件")
    print("  load     - 从文件加载配置")
    print("  base     - 修改基础导出目录")
    print("  subdir   - 修改导出子目录")
    print("  test     - 测试路径配置")
    print("  help     - 显示此帮助信息")
    print("  quit     - 退出配置编辑器")

def test_paths(config: Config):
    """测试路径配置"""
    print("\n🧪 测试路径配置")
    
    base_path = config.base_path
    print(f"基础目录: {base_path}")
    print(f"  存在: {'✅' if base_path.exists() else '❌'}")
    
    for key in config.export_subdirs.keys():
        try:
            path = config.get_export_path(key)
            print(f"{key:12}: {path}")
            print(f"{'':12}  存在: {'✅' if path.exists() else '❌'}")
        except Exception as e:
            print(f"{key:12}: ❌ 错误: {e}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="思源笔记脚本项目配置管理工具")
    parser.add_argument("--show", action="store_true", help="显示当前配置")
    parser.add_argument("--save", metavar="FILE", help="保存配置到指定文件")
    parser.add_argument("--load", metavar="FILE", help="从指定文件加载配置")
    parser.add_argument("--base", metavar="DIR", help="设置基础导出目录")
    parser.add_argument("--subdir", nargs=2, metavar=("KEY", "VALUE"), help="设置子目录 (键 值)")
    parser.add_argument("--test", action="store_true", help="测试路径配置")
    parser.add_argument("--interactive", "-i", action="store_true", help="启动交互式配置编辑器")
    
    args = parser.parse_args()
    
    # 获取配置实例
    config = get_config()
    
    # 先处理加载配置的命令
    if args.load:
        load_config_from_file(config, args.load)
    else:
        # 尝试从默认配置文件加载
        load_config_from_file(config)
    
    # 先处理修改配置的命令
    if args.base:
        config.update_base_dir(args.base)
        print(f"✅ 基础导出目录已设置为: {args.base}")
    
    if args.subdir:
        key, value = args.subdir
        try:
            config.update_subdir(key, value)
            print(f"✅ 子目录 {key} 已设置为: {value}")
        except ValueError as e:
            print(f"❌ {e}")
    
    # 然后处理其他命令
    if args.show:
        show_current_config(config)
    elif args.save:
        save_config_to_file(config, args.save)
    elif args.test:
        test_paths(config)
    elif args.interactive:
        show_current_config(config)
        interactive_config_editor(config)
    else:
        # 默认显示配置
        show_current_config(config)
        print("\n💡 使用 --help 查看命令行选项，或使用 --interactive 启动交互式编辑器")
    
    # 如果指定了保存，则在最后保存配置
    if args.save and (args.base or args.subdir):
        save_config_to_file(config, args.save)

if __name__ == "__main__":
    main()
