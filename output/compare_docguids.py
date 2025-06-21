"""
比较两个json文件，递归找出所有相同路径（目录）下不同的docguids，并输出到另一个json文件中
仅比较存在相同路径（目录）的docguids，不比较仅出现在一个文件中的路径（目录）
只输出不同的项，不输出相同的项

json文件结构示例：
{
  "Web收集箱": {
    "no-guid-20250615083750-vl9nn96": "想省大钱？思源笔记第三方同步 S3 手把手教程（使用七牛云对象存储 Kodo）（2024.4.25）",
    "no-guid-20250615093833-odybz7u": "SQL 小助手"
  },
  "我的草稿": {
    "6bb9646a-1951-4a2b-8a13-276fc57b9afe": "百度网盘视频素材转存进度",
    "0bd09603-832d-4e44-be38-3f42c9345197": "YouTube视频解析",
    "293e6f2a-979d-4df7-931c-af8e8e4eb26b": "碎笔记20250608"
  }
}

"""

import json
from pathlib import Path
from typing import Dict, Any, List


def load_json_file(file_path: str) -> Dict[str, Any]:
    """加载JSON文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"错误：找不到文件 {file_path}")
        return {}
    except json.JSONDecodeError as e:
        print(f"错误：解析JSON文件 {file_path} 时出错: {e}")
        return {}


def is_leaf_node(node: Any) -> bool:
    """判断是否为叶子节点（即docguid字典）"""
    return isinstance(node, dict) and all(
        not isinstance(v, dict) for v in node.values()
    )


def recursive_compare(d1: Dict[str, Any], d2: Dict[str, Any], path: List[str], result: Dict[str, Any]):
    """
    递归比较两个字典结构下所有相同路径的docguids，只输出不同项
    :param d1: 第一个json对象的当前子树
    :param d2: 第二个json对象的当前子树
    :param path: 当前递归路径
    :param result: 结果字典
    """
    # 只比较两个文件都存在的key
    common_keys = set(d1.keys()) & set(d2.keys())
    for key in common_keys:
        v1 = d1[key]
        v2 = d2[key]
        current_path = path + [key]
        if isinstance(v1, dict) and isinstance(v2, dict):
            if is_leaf_node(v1) and is_leaf_node(v2):
                # 比较docguid字典
                guids1 = set(v1.keys())
                guids2 = set(v2.keys())
                only1 = guids1 - guids2
                only2 = guids2 - guids1
                if only1 or only2:
                    # 只记录有差异的路径
                    path_str = '/'.join(current_path)
                    result[path_str] = {}
                    if only1:
                        result[path_str]['file1_only'] = {guid: v1[guid] for guid in only1}
                    if only2:
                        result[path_str]['file2_only'] = {guid: v2[guid] for guid in only2}
            else:
                # 递归子目录
                recursive_compare(v1, v2, current_path, result)


def compare_docguids_recursive(file1_path: str, file2_path: str, output_path: str) -> None:
    """
    递归比较两个JSON文件中所有相同路径下的docguids差异，只输出不同项
    """
    data1 = load_json_file(file1_path)
    data2 = load_json_file(file2_path)
    if not data1 or not data2:
        print("无法加载JSON文件，程序终止")
        return
    result = {}
    recursive_compare(data1, data2, [], result)
    if not result:
        print("没有发现不同项，两个文件在所有相同路径下的docguids完全一致。")
    else:
        print(f"共发现 {len(result)} 处不同的目录/路径。")
    try:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"比较结果已保存到: {output_path}")
    except Exception as e:
        print(f"错误：保存结果文件时出错: {e}")


def main():
    file1_path = "./output/siyuannotes_output_docguids_QuincyZou.json"
    file2_path = "./output/wiznotes_output_docguids_My Notes.json"
    output_path = "./output/docguids_comparison_result.json"
    print("开始递归比较JSON文件中的docguids...")
    print(f"文件1: {file1_path}")
    print(f"文件2: {file2_path}")
    print(f"输出文件: {output_path}")
    print("-" * 50)
    compare_docguids_recursive(file1_path, file2_path, output_path)


if __name__ == "__main__":
    main()