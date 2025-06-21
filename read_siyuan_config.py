"""
读取思源笔记的配置文件，导出快捷键设置为markdown文件：
- 内容形式为表格，包含主要类别、次要类别、功能、自定义快捷键、默认快捷键；
- 快捷键显示为Windows系统下的快捷键，比如：
  - ⌘ 对应 Windows 下的 Ctrl
  - ⌥ 对应 Windows 下的 Alt
  - ⇧ 对应 Windows 下的 Shift
  - ⌫ 对应 Windows 下的 Delete
  - ↩ 对应 Windows 下的 Enter
  - ↑ 对应 Windows 上的 Up
"""

import json
from pathlib import Path


def convert_mac_to_windows_shortcut(shortcut):
    """将macOS快捷键符号转换为Windows快捷键显示"""
    if not shortcut:
        return shortcut

    # 快捷键符号映射表
    mac_to_windows = {
        '⌘': 'Ctrl',
        '⌥': 'Alt',
        '⇧': 'Shift',
        '⌃': 'Ctrl',  # Control键
        '⌫': 'Delete',
        '⌦': 'Delete',  # Forward Delete
        '↩': 'Enter',
        '↑': 'Up',
        '↓': 'Down',
        '←': 'Left',
        '→': 'Right',
        '⇥': 'Tab',
        '⎋': 'Esc',
        '⏎': 'Enter',
        '⌤': 'Enter',
        '⌧': 'Clear',
        '⌴': 'Space',
        '⌵': 'Space',
        '⏏': 'Eject'
    }

    # 替换快捷键符号
    result = shortcut
    for mac_symbol, windows_key in mac_to_windows.items():
        result = result.replace(mac_symbol, windows_key + '+')

    # 清理多余的加号
    result = result.replace('++', '+')
    result = result.rstrip('+')

    # 处理单个字符的情况（如字母、数字、符号）
    if result and not any(modifier in result for modifier in ['Ctrl', 'Alt', 'Shift']):
        # 如果是功能键，保持原样
        if result.startswith('F') and result[1:].isdigit():
            return result
        # 如果是单个字符，保持原样
        if len(result) == 1:
            return result

    return result


def read_siyuan_config(config_path):
    """读取思源笔记配置文件"""
    try:
        print(f"正在读取配置文件: {config_path}")
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print("配置文件读取成功")
        return config
    except FileNotFoundError:
        print(f"错误：配置文件不存在 - {config_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"错误：JSON解析失败 - {e}")
        return None
    except Exception as e:
        print(f"错误：读取配置文件时发生异常 - {e}")
        return None


def export_keymap_to_markdown(config, output_path):
    """导出快捷键设置为markdown表格"""
    if not config:
        print("错误：配置文件为空")
        return

    keymap = config.get('keymap', {})
    if not keymap:
        print("错误：配置文件中没有找到keymap数据")
        return

    # 确保输出目录存在
    output_dir = Path(output_path)
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / '思源笔记快捷键设置.md'  # 默认文件名

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('# 思源笔记快捷键设置\n\n')

            # 遍历keymap的主要类别
            for main_category, sub_categories in keymap.items():
                # print(f"处理主类别: {main_category}")
                f.write(f'## {get_category_name(main_category)}\n\n')
                f.write('| 次要类别 | 功能 | 自定义快捷键 | 默认快捷键 |\n')
                f.write('|---------|------|------------|----------|\n')

                if main_category == 'editor':
                    # 处理editor结构: editor -> sub_category -> function -> {custom, default}
                    for sub_category, functions in sub_categories.items():
                        sub_category_name = get_category_name(sub_category)

                        if isinstance(functions, dict):
                            for function_name, shortcuts in functions.items():
                                if isinstance(shortcuts, dict):
                                    function_display = get_function_name(function_name)
                                    custom_key = convert_mac_to_windows_shortcut(shortcuts.get('custom', ''))
                                    default_key = convert_mac_to_windows_shortcut(shortcuts.get('default', ''))

                                    f.write(f'| {sub_category_name} | {function_display} | {custom_key} | {default_key} |\n')

                elif main_category == 'general':
                    # 处理general结构: general -> function -> {custom, default}
                    for function_name, shortcuts in sub_categories.items():
                        if isinstance(shortcuts, dict):
                            function_display = get_function_name(function_name)
                            custom_key = convert_mac_to_windows_shortcut(shortcuts.get('custom', ''))
                            default_key = convert_mac_to_windows_shortcut(shortcuts.get('default', ''))

                            f.write(f'| - | {function_display} | {custom_key} | {default_key} |\n')

                elif main_category == 'plugin':
                    # 处理plugin结构: plugin -> plugin_name -> function -> {custom, default}
                    for plugin_name, plugin_functions in sub_categories.items():
                        plugin_display_name = get_category_name(plugin_name)

                        if isinstance(plugin_functions, dict):
                            for function_name, shortcuts in plugin_functions.items():
                                if isinstance(shortcuts, dict):
                                    function_display = get_function_name(function_name)
                                    custom_key = convert_mac_to_windows_shortcut(shortcuts.get('custom', ''))
                                    default_key = convert_mac_to_windows_shortcut(shortcuts.get('default', ''))

                                    f.write(f'| {plugin_display_name} | {function_display} | {custom_key} | {default_key} |\n')
                                else:
                                    # 某些插件功能可能有不同的结构
                                    function_display = get_function_name(function_name)
                                    converted_shortcut = convert_mac_to_windows_shortcut(str(shortcuts))
                                    f.write(f'| {plugin_display_name} | {function_display} | {converted_shortcut} |  |\n')

                f.write('\n')

        print(f"快捷键设置已成功导出到: {output_file}")
        # print("快捷键已转换为Windows系统格式")

    except Exception as e:
        print(f"错误：写入文件时发生异常 - {e}")


def get_category_name(category_key):
    """获取类别的中文名称"""
    category_names = {
        'editor': '编辑器',
        'general': '通用',
        'plugin': '插件',
        'heading': '标题',
        'insert': '插入',
        'list': '列表',
        'table': '表格',
        'siyuan-drawio-plugin': 'drawio插件',
        'sy-f-misc': 'f-misc插件',
        'sy-tomato-plugin': 'tomato插件'
    }
    return category_names.get(category_key, category_key)


def get_function_name(function_key):
    """获取功能的中文名称"""
    function_names = {
        # 通用功能
        'ai': 'AI',
        'aiWriting': 'AI编写',
        'alignCenter': '居中对齐',
        'alignLeft': '左对齐',
        'alignRight': '右对齐',
        'attr': '属性',
        'backlinks': '反向链接',
        'collapse': '折叠',
        'copyBlockEmbed': '复制为嵌入块',
        'copyBlockRef': '复制为引用块',
        'copyHPath': '复制层级路径',
        'copyID': '复制ID',
        'copyPlainText': '复制纯文本',
        'copyProtocol': '复制块超链接',
        'copyProtocolInMd': '复制块Markdown链接',
        'copyText': '复制文本',
        'duplicate': '复制为副本',
        'duplicateCompletely': '复制为完整副本',
        'exitFocus': '退出焦点',
        'expand': '展开',
        'expandDown': '向下扩选',
        'expandUp': '向上扩选',
        'fullscreen': '全屏',
        'graphView': '关系图',
        'hLayout': '水平布局',
        'insertAfter': '在后插入',
        'insertBefore': '在前插入',
        'insertBottom': '在下方插入',
        'insertRight': '在右侧插入',
        'jumpToParent': '跳转到父级块',
        'jumpToParentNext': '跳转到父级下一个块',
        'jumpToParentPrev': '跳转到父级上一个块',
        'ltr': '从左到右',
        'moveToDown': '向下移动',
        'moveToUp': '向上移动',
        'netAssets2LocalAssets': '网络资源转本地资源',
        'netImg2LocalAsset': '网络图片转本地资源',
        'newContentFile': '新建文档内容为',
        'newNameFile': '新建子文档名为',
        'newNameSettingFile': '新建命名设置文件',
        'openBy': '打开',
        'openInNewTab': '在新标签页打开',
        'optimizeTypography': '优化排版',
        'outline': '大纲',
        'preview': '导出预览',
        'quickMakeCard': '快速制卡',
        'redo': '重做',
        'refPopover': '在浮窗中打开',
        'refTab': '在后台标签页中打开',
        'refresh': '刷新',
        'rename': '重命名',
        'rtl': '从右到左',
        'showInFolder': '打开文件位置',
        'spaceRepetition': '间隔重复',
        'switchAdjust': '切换自适应宽度',
        'switchReadonly': '切换只读模式',
        'undo': '撤销',
        'vLayout': '垂直布局',
        'wysiwyg': '所见即所得',

        # 标题功能
        'heading1': '一级标题',
        'heading2': '二级标题',
        'heading3': '三级标题',
        'heading4': '四级标题',
        'heading5': '五级标题',
        'heading6': '六级标题',
        'paragraph': '段落',

        # 插入功能
        'appearance': '外观',
        'bold': '粗体',
        'check': '复选框',
        'clearInline': '清除内联样式',
        'code': '代码块',
        'inline-code': '内联代码',
        'inline-math': '内联数学公式',
        'italic': '斜体',
        'kbd': '键盘按键',
        'lastUsed': '最后使用',
        'link': '链接',
        'list': '无序列表',
        'mark': '标记',
        'memo': '备注',
        'ordered-list': '有序列表',
        'quote': '引述',
        'ref': '引用',
        'strike': '删除线',
        'sub': '下标',
        'sup': '上标',
        'table': '表格',
        'tag': '标签',
        'underline': '下划线',

        # 列表功能
        'checkToggle': '切换复选框勾选状态',
        'indent': '列表缩进',
        'outdent': '列表反向缩进',

        # 表格功能
        'delete-column': '删除列',
        'delete-row': '删除行',
        'insertColumnLeft': '在左侧插入列',
        'insertColumnRight': '在右侧插入列',
        'insertRowAbove': '在上方插入行',
        'insertRowBelow': '在下方插入行',
        'moveToLeft': '向左移',
        'moveToRight': '向右移',

        # 通用快捷键
        'addToDatabase': '添加到数据库',
        'bookmark': '书签',
        'closeAll': '关闭所有',
        'closeLeft': '关闭左侧',
        'closeOthers': '关闭其他',
        'closeRight': '关闭右侧',
        'closeTab': '关闭标签页',
        'closeUnmodified': '关闭未修改的标签页',
        'commandPanel': '命令面板',
        'config': '设置',
        'dailyNote': '日记',
        'dataHistory': '数据历史',
        'editReadonly': '只读模式',
        'enter': '聚焦',
        'enterBack': '聚焦到上层',
        'fileTree': '文档树',
        'globalGraph': '全局关系图',
        'globalSearch': '全局搜索',
        'goBack': '后退',
        'goForward': '前进',
        'goToEditTabNext': '跳转到下一个编辑标签页',
        'goToEditTabPrev': '跳转到上一个编辑标签页',
        'goToTab1': '跳转到标签页1',
        'goToTab2': '跳转到标签页2',
        'goToTab3': '跳转到标签页3',
        'goToTab4': '跳转到标签页4',
        'goToTab5': '跳转到标签页5',
        'goToTab6': '跳转到标签页6',
        'goToTab7': '跳转到标签页7',
        'goToTab8': '跳转到标签页8',
        'goToTab9': '跳转到标签页9',
        'goToTabNext': '跳转到下一个标签页',
        'goToTabPrev': '跳转到上一个标签页',
        'inbox': '收集箱',
        'lockScreen': '锁屏',
        'mainMenu': '主菜单',
        'move': '移动',
        'newFile': '新建文件',
        'recentDocs': '最近文档',
        'replace': '替换',
        'riffCard': '闪卡',
        'search': '搜索',
        'selectOpen1': '定位打开的文档',
        'splitLR': '向右分屏',
        'splitMoveB': '向下分屏并移动',
        'splitMoveR': '向右分屏并移动',
        'splitTB': '向下分屏',
        'stickSearch': '固定搜索',
        'syncNow': '立即同步',
        'tabToWindow': '移动到新窗口',
        'tag': '标签',
        'toggleDock': '显示/隐藏停靠栏',
        'toggleWin': '显示/隐藏窗口',
        'unsplit': '取消分屏',
        'unsplitAll': '取消所有分屏',

        # 插件相关
        'openDrawio': '打开Drawio',
        'siyuan-drawio-plugindrawio_dock': 'Drawio停靠栏'
    }
    return function_names.get(function_key, function_key)


if __name__ == "__main__":
    print("开始执行思源笔记快捷键导出脚本...")
    config = read_siyuan_config(Path('D:/SiYuan_data/conf/conf.json'))
    if config:
        export_keymap_to_markdown(config, './output')
    else:
        print("脚本执行失败：无法读取配置文件")