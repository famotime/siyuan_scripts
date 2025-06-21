"""
通过思源笔记API，获取指定笔记本下所有笔记文档的custom-docGuid和custom-title属性值，并保存到json文件（若有子笔记则视为目录，体现层次关系）
根据API文档 @思源API.md ，先打开笔记本，再从根目录"/"获取子文档ID，然后再获取文档的属性，再逐层往下探索目录结构。

json文件示例：
{
  "吉光片羽": {
    "997e7347-6e78-4de4-9796-d8f3e7f15e9b": "AI 技术 & 产品服务",
    "d4fee691-9438-4983-a1a9-dfd5e041a6de": "Github项目",
    "思维模型": {
      "f2846dd8-fc22-4207-97f8-475c10e99b67": "100个思维模型（图片）",
      "99cd969a-4fba-40af-a95f-a76ff124f51b": "15种顶级分析思维模型。"
    }
  }
}

"""
import requests
import json
import logging
from pathlib import Path

# ====== 配置区 ======
API_URL = 'http://127.0.0.1:6806'
TOKEN = '6bc792eg8bg5x1p3'  # <<< 请在此处填写你的token
NOTEBOOK_ID = '20250614224007-27h8mrb'  # <<< 请在此处填写你的笔记本id
# OUTPUT_JSON 将在获取到笔记本名称后动态生成
# ====================

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    'Authorization': f'Token {TOKEN}',
    'Content-Type': 'application/json'
}

def make_api_request(endpoint, data=None):
    """统一的API请求处理函数"""
    url = f'{API_URL}{endpoint}'
    try:
        if data is None:
            data = {}
        resp = requests.post(url, headers=HEADERS, json=data)
        resp.raise_for_status()
        result = resp.json()
        if result['code'] != 0:
            raise Exception(f'API请求失败 [{endpoint}]: {result}')
        return result['data']
    except requests.exceptions.RequestException as e:
        logger.error(f'网络请求错误 [{endpoint}]: {e}')
        raise
    except Exception as e:
        logger.error(f'API调用错误 [{endpoint}]: {e}')
        raise

def open_notebook(notebook_id):
    """打开指定的笔记本"""
    logger.info(f'正在打开笔记本: {notebook_id}')
    make_api_request('/api/notebook/openNotebook', {'notebook': notebook_id})
    logger.info('笔记本已打开')

def get_child_blocks(block_id):
    """获取指定块的子块"""
    logger.debug(f'获取子块: {block_id}')
    return make_api_request('/api/block/getChildBlocks', {'id': block_id})

def get_block_attrs(block_id):
    """获取指定块的属性"""
    logger.debug(f'获取块属性: {block_id}')
    return make_api_request('/api/attr/getBlockAttrs', {'id': block_id})

def build_tree(block_id, level=0):
    """递归构建文档树结构"""
    indent = "  " * level
    logger.info(f'{indent}正在处理块: {block_id}')

    try:
        # 获取当前块的属性
        attrs = get_block_attrs(block_id)
        block_type = attrs.get('type', '')

        logger.debug(f'{indent}块属性: type={block_type}, attrs={attrs}')

        # 如果当前块不是文档块，直接返回空
        if block_type not in ['d', 'doc']:
            logger.info(f'{indent}当前块不是文档块 (type: {block_type})')
            return {}

        # 获取文档标题和GUID
        title = attrs.get('custom-title') or attrs.get('title', '无标题')
        docguid = attrs.get('custom-docGuid')

        logger.info(f'{indent}文档: {title} (GUID: {docguid}, Type: {block_type})')

        # 获取子块并查找子文档
        children = get_child_blocks(block_id)
        child_docs = [child for child in children if child.get('type') in ['d', 'doc']]

        logger.info(f'{indent}找到 {len(children)} 个子块，其中 {len(child_docs)} 个子文档')

        # 如果没有子文档，这是一个叶子文档
        if not child_docs:
            if docguid:
                logger.info(f'{indent}  叶子文档: {docguid} -> {title}')
                return {docguid: title}
            else:
                logger.info(f'{indent}  无GUID叶子文档: no-guid-{block_id} -> {title}')
                return {f'no-guid-{block_id}': title}

        # 如果有子文档，这是一个目录
        logger.info(f'{indent}目录文档: {title}，包含 {len(child_docs)} 个子文档')

        # 构建子文档树
        subtree = {}
        for child in child_docs:
            child_id = child['id']
            child_result = build_tree(child_id, level + 1)
            if child_result:
                subtree.update(child_result)

        # 构建当前目录的结构
        if subtree:
            # 如果当前文档也有GUID，需要特殊处理
            if docguid:
                # 目录本身也是一个文档，使用特殊结构
                result = {
                    title: {
                        "__self__": {docguid: title},  # 目录本身的GUID
                        **subtree  # 子文档
                    }
                }
                logger.info(f'{indent}  目录结构(有GUID): {title} -> 包含自身和{len(subtree)}个子项')
            else:
                # 目录没有GUID，只作为容器
                result = {title: subtree}
                logger.info(f'{indent}  目录结构(无GUID): {title} -> 包含{len(subtree)}个子项')

            return result
        else:
            # 虽然有子块，但没有子文档，仍作为叶子文档处理
            if docguid:
                return {docguid: title}
            else:
                return {f'no-guid-{block_id}': title}

    except Exception as e:
        logger.error(f'{indent}处理块 {block_id} 时出错: {e}')
        return {}

def list_notebooks():
    """查询所有笔记本id和名称"""
    logger.info('正在获取笔记本列表...')
    notebooks = make_api_request('/api/notebook/lsNotebooks')['notebooks']
    return [(nb['id'], nb['name']) for nb in notebooks]

def get_notebook_name(notebook_id):
    """根据笔记本ID获取笔记本名称"""
    notebooks = list_notebooks()
    for nb_id, nb_name in notebooks:
        if nb_id == notebook_id:
            return nb_name
    return f'未知笔记本-{notebook_id}'

def get_ids_by_hpath(hpath, notebook_id):
    """根据人类可读路径获取文档IDs"""
    logger.info(f'正在获取路径 "{hpath}" 下的文档IDs (笔记本: {notebook_id})')
    data = make_api_request('/api/filetree/getIDsByHPath', {
        'path': hpath,
        'notebook': notebook_id
    })
    logger.info(f'找到 {len(data)} 个文档ID: {data}')
    return data

def get_notebook_docs_by_sql(notebook_id):
    """通过SQL查询获取指定笔记本下的所有文档块"""
    logger.info(f'正在通过SQL查询获取笔记本 {notebook_id} 下的文档...')

    # SQL查询：获取指定笔记本下的所有文档块
    # type='d' 表示文档块 (根据调试信息确认是'd'类型)
    # box是笔记本ID字段
    sql = f"SELECT id, content FROM blocks WHERE box = '{notebook_id}' AND type = 'd' ORDER BY created"

    logger.info(f'执行SQL: {sql}')
    data = make_api_request('/api/query/sql', {'stmt': sql})
    logger.info(f'通过SQL查询找到 {len(data)} 个文档')

    # 提取文档ID列表
    doc_ids = [doc['id'] for doc in data]
    logger.info(f'文档ID列表: {doc_ids[:10]}...' if len(doc_ids) > 10 else f'文档ID列表: {doc_ids}')

    return doc_ids

def get_doc_tree(notebook_id, path="/"):
    """通过API获取指定笔记本的文档树结构"""
    logger.info(f'正在获取笔记本 {notebook_id} 的文档树结构...')

    data = make_api_request('/api/filetree/listDocTree', {
        'notebook': notebook_id,
        'path': path
    })

    tree_data = data.get('tree', [])
    logger.info(f'获取到文档树，包含 {len(tree_data)} 个根节点')

    return tree_data

def process_doc_tree_node(node, level=0):
    """递归处理文档树节点"""
    indent = "  " * level
    node_id = node['id']
    children = node.get('children', [])

    logger.info(f'{indent}正在处理节点: {node_id} (有 {len(children)} 个子节点)')

    try:
        # 获取当前文档的属性
        attrs = get_block_attrs(node_id)
        title = attrs.get('custom-title') or attrs.get('title', '无标题')
        docguid = attrs.get('custom-docGuid')

        logger.info(f'{indent}文档: {title} (GUID: {docguid})')

        # 如果没有子节点，这是叶子文档
        if not children:
            if docguid:
                logger.info(f'{indent}  叶子文档: {docguid} -> {title}')
                return {docguid: title}
            else:
                logger.info(f'{indent}  无GUID叶子文档: no-guid-{node_id} -> {title}')
                return {f'no-guid-{node_id}': title}

        # 如果有子节点，这是目录
        logger.info(f'{indent}目录文档: {title}，包含 {len(children)} 个子文档')

        # 递归处理所有子节点
        subtree = {}
        for child in children:
            child_result = process_doc_tree_node(child, level + 1)
            if child_result:
                subtree.update(child_result)

        # 构建当前目录的结构
        if subtree:
            if docguid:
                # 目录本身也有GUID，使用特殊结构
                result = {
                    title: {
                        "__self__": {docguid: title},  # 目录本身的GUID
                        **subtree  # 子文档
                    }
                }
                logger.info(f'{indent}  目录结构(有GUID): {title} -> 包含自身和{len(subtree)}个子项')
            else:
                # 目录没有GUID，只作为容器
                result = {title: subtree}
                logger.info(f'{indent}  目录结构(无GUID): {title} -> 包含{len(subtree)}个子项')

            return result
        else:
            # 虽然API显示有子节点，但实际没有获取到子文档，仍作为叶子文档处理
            if docguid:
                return {docguid: title}
            else:
                return {f'no-guid-{node_id}': title}

    except Exception as e:
        logger.error(f'{indent}处理节点 {node_id} 时出错: {e}')
        return {}

def main(folder_name):
    """主函数"""
    logger.info('开始执行思源笔记文档GUID提取程序')

    try:
        # 查询并打印所有笔记本id和名称，便于查找NOTEBOOK_ID
        logger.info('所有可用笔记本:')
        notebooks = list_notebooks()
        for nb_id, nb_name in notebooks:
            logger.info(f'  {nb_id}  {nb_name}')

        logger.info(f'\n当前NOTEBOOK_ID设置为: {NOTEBOOK_ID}')

        # 验证笔记本ID是否存在
        notebook_ids = [nb[0] for nb in notebooks]
        if NOTEBOOK_ID not in notebook_ids:
            logger.error(f'错误: 笔记本ID {NOTEBOOK_ID} 不存在！')
            return

        # 打开笔记本
        open_notebook(NOTEBOOK_ID)

        # 获取笔记本名称
        notebook_name = get_notebook_name(NOTEBOOK_ID)
        logger.info(f'开始处理笔记本: {notebook_name}')

        # 通过API获取文档树结构
        try:
            tree_data = get_doc_tree(NOTEBOOK_ID, folder_name)

            if not tree_data:
                logger.warning('文档树为空，尝试使用SQL查询作为备用方案')
                raise Exception("文档树为空")

            # 处理文档树
            tree = {}
            for node in tree_data:
                logger.info(f'处理根节点: {node["id"]}')
                node_result = process_doc_tree_node(node)
                if node_result:
                    tree.update(node_result)

        except Exception as e:
            logger.warning(f'API获取失败，尝试使用SQL查询: {e}')
            # 备用方案：尝试使用SQL查询
            root_doc_ids = get_notebook_docs_by_sql(NOTEBOOK_ID)

            if not root_doc_ids:
                logger.warning('没有找到任何文档，尝试直接使用笔记本ID作为根块')
                # 最后的备用方案：直接使用笔记本ID
                root_doc_ids = [NOTEBOOK_ID]

            # 构建文档树（备用方案）
            tree = {}
            for doc_id in root_doc_ids:
                logger.info(f'处理文档: {doc_id}')
                doc_tree = build_tree(doc_id)
                tree.update(doc_tree)

        # 保存到JSON文件（笔记本名称作为文件名）
        OUTPUT_JSON = Path(__file__).parent / 'output' / f'siyuannotes_output_docguids_{notebook_name}.json'
        logger.info(f'正在保存结果到: {OUTPUT_JSON}')
        with OUTPUT_JSON.open('w', encoding='utf-8') as f:
            json.dump(tree, f, ensure_ascii=False, indent=2)

        logger.info(f'成功完成！共处理了 {count_documents(tree)} 个文档')
        logger.info(f'结果已保存到: {OUTPUT_JSON}')

    except Exception as e:
        logger.error(f'程序执行失败: {e}')
        raise

def count_documents(tree):
    """递归计算文档数量"""
    count = 0
    for key, value in tree.items():
        if isinstance(value, str):
            # 这是一个docGuid-title对
            count += 1
        elif isinstance(value, dict):
            if '__self__' in value:
                # 这是一个有自身GUID的目录，先计算自身
                count += count_documents(value['__self__'])
                # 再递归计算子目录中的文档数量
                remaining_items = {k: v for k, v in value.items() if k != '__self__'}
                count += count_documents(remaining_items)
            else:
                # 递归计算子目录中的文档数量
                count += count_documents(value)
    return count

if __name__ == '__main__':
    folder_name = "/"
    main(folder_name)