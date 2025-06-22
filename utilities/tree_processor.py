"""
树结构处理器
"""
from typing import Dict, Any


class TreeProcessor:
    """树结构处理类"""

    @staticmethod
    def is_leaf_node(node: Any) -> bool:
        """
        判断是否为叶子节点（即docguid字典）

        :param node: 节点数据
        :return: 是否为叶子节点
        """
        return isinstance(node, dict) and all(
            not isinstance(v, dict) for v in node.values()
        )

    @staticmethod
    def count_documents(tree: Dict[str, Any]) -> int:
        """
        递归计算文档数量

        :param tree: 文档树
        :return: 文档数量
        """
        count = 0
        for key, value in tree.items():
            if isinstance(value, str):
                # 这是一个docGuid-title对
                count += 1
            elif isinstance(value, dict):
                if '__self__' in value:
                    # 这是一个有自身GUID的目录，先计算自身
                    count += TreeProcessor.count_documents(value['__self__'])
                    # 再递归计算子目录中的文档数量
                    remaining_items = {k: v for k, v in value.items() if k != '__self__'}
                    count += TreeProcessor.count_documents(remaining_items)
                else:
                    # 递归计算子目录中的文档数量
                    count += TreeProcessor.count_documents(value)
        return count