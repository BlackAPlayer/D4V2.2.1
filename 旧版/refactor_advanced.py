#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级重构脚本：将 D4v2.2.1.py 拆分为模块化结构，自动处理依赖导入
用法： python refactor_advanced.py
输出： D4Calculator/ 目录，包含完整可运行项目
"""
import ast
import os
import sys
from collections import defaultdict

# ==================== 1. 模块映射定义 ====================
# 定义每个模块应包含的顶层名称（类、函数、常量）
MODULE_MAP = {
    'config': {
        'constants': [
            'PROFESSIONS', 'POSITIONS', 'WEAPON_TYPES', 'COLORS',
            'SOCKETS_BY_POSITION'
        ],
        'functions': ['resource_path']
    },
    'data/loader': {
        'constants': ['FULL_DB', 'GEMS_DATABASE', 'RUNES_DATABASE',
                      'AFFIX_VALUES', 'AFFIX_BY_POSITION', 'IMAGE_CACHE'],
        'functions': ['load_photo_image', 'get_profession_db']
    },
    'business/skill_tree': {
        'classes': ['SkillTreeSystem']
    },
    'business/equipment': {
        'functions': ['calculate_affix_value', 'get_affixes_for_position',
                      'get_reforge_affixes_for_position']
    },
    'ui/skill_tree_ui': {
        'classes': ['SkillTreeUI']
    },
    'ui/equipment_ui': {
        'classes': ['EquipDetailDialog', 'GemSelectDialog', 'RuneTwoStepDialog']
    },
    'ui/main_window': {
        'classes': ['DiabloCalculator']
    },
    'ui/widgets': {
        'functions': ['filter_combobox']
    },
    'utils/image_cache': {
        'functions': ['load_photo_image'],
        'constants': ['IMAGE_CACHE']
    },
    'utils/path_helper': {
        'functions': ['resource_path'],
        'constants': ['BASE_DIR']
    },
    'utils/logging_config': {
        'imports': ['import logging'],
        'statements': ["logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')"]
    }
}

# 补充：BASE_DIR 在 config 中定义，resource_path 需要它
MODULE_MAP['config']['constants'].append('BASE_DIR')

# ==================== 2. AST 解析与名称收集 ====================
def parse_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        code = f.read()
    return ast.parse(code), code.splitlines()

def extract_top_level_defs(tree):
    """提取所有顶层定义：类、函数、赋值（常量）和导入"""
    top = {'classes': [], 'functions': [], 'constants': [], 'imports': []}
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            top['classes'].append(node)
        elif isinstance(node, ast.FunctionDef):
            top['functions'].append(node)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    top['constants'].append((target.id, node))
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            top['imports'].append(node)
    return top

def get_source_segment(node, lines):
    """获取节点的源码字符串"""
    try:
        return ast.get_source_segment(''.join(lines), node)
    except Exception:
        # 降级方案：按行号提取
        return '\n'.join(lines[node.lineno-1:node.end_lineno])

def collect_names_from_node(node):
    """收集AST节点中所有引用的名称（Name节点）"""
    names = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Load):
            names.add(child.id)
    return names

# ==================== 3. 依赖分析与导入生成 ====================
def build_name_to_module_map(top_defs, module_map):
    """构建名称 -> 所属模块的映射"""
    name_to_module = {}
    # 先填充所有模块中的定义
    for module_path, content in module_map.items():
        for cat in ['constants', 'functions', 'classes']:
            if cat in content:
                for name in content[cat]:
                    name_to_module[name] = module_path
    return name_to_module

def generate_imports(module_name, used_names, name_to_module, module_map, all_defs):
    """
    为给定模块生成导入语句
    返回 import 代码字符串列表
    """
    imports = []
    # 排除当前模块自身的定义
    current_defs = set()
    if module_name in module_map:
        for cat in ['constants', 'functions', 'classes']:
            if cat in module_map[module_name]:
                current_defs.update(module_map[module_name][cat])

    # 收集需要从其他模块导入的名称
    external_names = {}
    for name in used_names:
        if name in name_to_module and name_to_module[name] != module_name:
            # 避免导入自身模块
            if name not in current_defs:
                target_mod = name_to_module[name]
                # 将模块路径转换为Python导入路径（如 'data/loader' -> 'data.loader'）
                import_path = target_mod.replace('/', '.')
                external_names.setdefault(import_path, []).append(name)

    # 生成导入语句
    for import_path, names in external_names.items():
        # 优先使用 from ... import ... 形式
        imports.append(f"from {import_path} import {', '.join(names)}")

    # 添加标准库和第三方库导入（由模块自身决定，但为了完整，我们单独处理）
    # 我们将在写入文件时，在模块开头添加通用导入，所以这里只处理自定义模块的导入
    return imports

# ==================== 4. 主重构流程 ====================
def refactor(source_file, output_dir='D4Calculator'):
    # 读取源文件
    tree, lines = parse_file(source_file)
    top = extract_top_level_defs(tree)

    # 建立名称到节点映射
    name_to_node = {}
    for cls in top['classes']:
        name_to_node[cls.name] = cls
    for func in top['functions']:
        name_to_node[func.name] = func
    for const_name, node in top['constants']:
        name_to_node[const_name] = node

    # 构建名称到模块映射
    name_to_module = build_name_to_module_map(top, MODULE_MAP)

    # 创建输出目录
    os.makedirs(output_dir, exist_ok=True)
    for sub in ['config', 'data', 'business', 'ui', 'utils']:
        os.makedirs(os.path.join(output_dir, sub), exist_ok=True)

    # 为每个模块生成文件
    for module_path, content in MODULE_MAP.items():
        module_dir = os.path.dirname(module_path)
        if module_dir:
            os.makedirs(os.path.join(output_dir, module_dir), exist_ok=True)

        target_file = os.path.join(output_dir, f"{module_path}.py")
        with open(target_file, 'w', encoding='utf-8') as f:
            # 写入文件头
            f.write(f"# -*- coding: utf-8 -*-\n# 模块: {module_path}\n\n")

            # 收集该模块需包含的所有定义源码
            definitions = []
            used_names = set()
            # 收集常量
            if 'constants' in content:
                for const_name in content['constants']:
                    if const_name in name_to_node:
                        node = name_to_node[const_name]
                        src = get_source_segment(node, lines)
                        definitions.append(src)
                        # 收集该节点中引用的外部名称
                        used_names.update(collect_names_from_node(node))
            # 收集函数
            if 'functions' in content:
                for func_name in content['functions']:
                    if func_name in name_to_node:
                        node = name_to_node[func_name]
                        src = get_source_segment(node, lines)
                        definitions.append(src)
                        used_names.update(collect_names_from_node(node))
            # 收集类
            if 'classes' in content:
                for cls_name in content['classes']:
                    if cls_name in name_to_node:
                        node = name_to_node[cls_name]
                        src = get_source_segment(node, lines)
                        definitions.append(src)
                        used_names.update(collect_names_from_node(node))

            # 生成导入语句（自定义模块导入）
            custom_imports = generate_imports(module_path, used_names, name_to_module, MODULE_MAP, top)
            # 通用导入（标准库和第三方）
            common_imports = [
                "import tkinter as tk",
                "from tkinter import ttk, messagebox",
                "import json",
                "import os",
                "import gc",
                "import sys",
                "import re",
                "import math",
                "import copy",
                "from PIL import Image, ImageTk",
                "import logging"
            ]
            # 写入通用导入
            for imp in common_imports:
                f.write(imp + "\n")
            f.write("\n")
            # 写入自定义导入
            for imp in custom_imports:
                f.write(imp + "\n")
            f.write("\n")

            # 写入模块特定的定义
            for code in definitions:
                f.write(code + "\n\n")

            # 如果模块是 utils/logging_config，额外写入配置语句
            if module_path == 'utils/logging_config':
                if 'statements' in content:
                    for stmt in content['statements']:
                        f.write(stmt + "\n")

    # 创建 main.py 入口
    main_content = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""D4计算器 V2.2.1 - 模块化入口"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from ui.main_window import DiabloCalculator
import tkinter as tk

if __name__ == '__main__':
    root = tk.Tk()
    root.title('D4计算器 V2.2.1')
    root.geometry('750x800')
    root.configure(bg='#1a0505')
    app = DiabloCalculator(root)
    root.mainloop()
'''
    with open(os.path.join(output_dir, 'main.py'), 'w', encoding='utf-8') as f:
        f.write(main_content)

    # 生成各个包的 __init__.py（可选）
    for sub in ['config', 'data', 'business', 'ui', 'utils']:
        init_path = os.path.join(output_dir, sub, '__init__.py')
        with open(init_path, 'w', encoding='utf-8') as f:
            f.write("# 包初始化\n")

    print(f"✅ 重构完成！生成目录: {output_dir}")
    print("请运行 python main.py 启动程序。")
    print("若有缺失导入，请根据报错提示手动补充（极少数情况）。")

if __name__ == '__main__':
    refactor('D4v2.2.1.py')