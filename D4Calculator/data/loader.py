# -*- coding: utf-8 -*-
# 模块: data/loader

import json
import os
import sys
import gc
import logging
from PIL import Image, ImageTk

# ---------- 路径工具（从 config 导入） ----------
try:
    from config import resource_path, BASE_DIR
except ImportError:
    # 如果 config 不存在，定义临时路径
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    def resource_path(relative_path):
        return os.path.join(BASE_DIR, relative_path)

# ---------- 加载 full_database_new.json ----------
# 优先从项目根目录加载
DB_FILE = os.path.join(BASE_DIR, 'full_database_new.json')
if not os.path.exists(DB_FILE):
    # 回退到 resource_path（可能指向 utils/）
    DB_FILE = resource_path('full_database_new.json')

try:
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        FULL_DB = json.load(f)
    logging.info("数据库加载成功: %s", DB_FILE)
except Exception as e:
    logging.warning("加载数据库失败: %s -> %s", DB_FILE, e)
    FULL_DB = {}

# ---------- 确保 FULL_DB 有必需的键 ----------
if not isinstance(FULL_DB, dict):
    FULL_DB = {}
FULL_DB.setdefault('gems', {})
FULL_DB.setdefault('runes', {})
FULL_DB.setdefault('affix_values', {})
FULL_DB.setdefault('affix_by_position', {})
FULL_DB.setdefault('powers', {'all': {}})
FULL_DB.setdefault('main_stat', {})
FULL_DB.setdefault('transmute_by_position', {})
FULL_DB.setdefault('unique_items', {'all': {}})
# 确保 affix_by_position 至少有 '主手' 键，避免 KeyError
if '主手' not in FULL_DB['affix_by_position']:
    FULL_DB['affix_by_position']['主手'] = []

# ---------- 导出常用数据 ----------
GEMS_DATABASE = FULL_DB.get('gems', {})
RUNES_DATABASE = FULL_DB.get('runes', {})
AFFIX_VALUES = FULL_DB.get('affix_values', {})
AFFIX_BY_POSITION = FULL_DB.get('affix_by_position', {})
IMAGE_CACHE = {}

# ---------- 图片加载函数 ----------
def load_photo_image(path, size=None):
    """加载图片并缓存，支持尺寸缩放"""
    key = (os.path.abspath(path), None if size is None else tuple(size))
    if key in IMAGE_CACHE:
        return IMAGE_CACHE[key]
    try:
        img = Image.open(path)
        if size:
            img = img.resize(size, Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        IMAGE_CACHE[key] = photo
        return photo
    except Exception as e:
        logging.debug("加载图片失败 %s -> %s", path, e)
        return None

# ---------- 职业数据库缓存 ----------
_PROFESSION_CACHE = {}

def get_profession_db(profession):
    """根据职业加载对应的威能、词缀、暗金等数据"""
    if profession in _PROFESSION_CACHE:
        return _PROFESSION_CACHE[profession]

    db = {
        'powers': {'all': {}},
        'affixes_list': [],
        'transmute_list': [],
        'unique_items': {}
    }

    # 1. 威能
    for name, data in FULL_DB['powers']['all'].items():
        power_class = data.get('class', '全职业')
        if power_class in ('全职业', profession, 'nan'):
            db['powers']['all'][name] = data

    # 2. 词缀
    for affix_name in FULL_DB['affix_by_position'].get('主手', []):
        if affix_name in AFFIX_VALUES:
            data = AFFIX_VALUES[affix_name]
            db['affixes_list'].append(f"+[{data['min']}-{data['max']}] {affix_name}")

    # 3. 嬗变词缀
    transmute_list = []
    for affix_name in FULL_DB.get('transmute_by_position', {}).get('主手', []):
        if affix_name in AFFIX_VALUES:
            v = AFFIX_VALUES[affix_name]
            transmute_list.append(f"+[{v['min']}-{v['max']}] {affix_name}")
        else:
            transmute_list.append(affix_name)
    db['transmute_list'] = transmute_list

    # 4. 暗金装备（含神话暗金）
    MYTHIC_ITEMS = {
        '祖父', '末日使者', '艾尔度因，正义之剑', '无星夜空之戒',
        '阿瓦里昂，莱姗德之矛', '堕狱传承', '破碎的誓言', '安达莉尔的仪容',
        '谐角之冠', '泰瑞尔之力', '涅塞科姆，绝望先驱', '塞利格的溶解之心',
        '虚假死亡之衣'
    }
    for name, data in FULL_DB['unique_items']['all'].items():
        if data.get('class', '全职业') in (profession, '全职业'):
            db['unique_items'][name] = data

    # 处理 v43 格式的暗金（若存在）
    if 'unique_items_v43' in FULL_DB:
        for slot, classes in FULL_DB['unique_items_v43'].items():
            for cls, items in classes.items():
                if cls in (profession, '全职业'):
                    target_slots = ['戒指1', '戒指2'] if slot == '戒指' else [slot]
                    for target_slot in target_slots:
                        for item_name, item_data in items.items():
                            rarity = '神话暗金装备' if item_name in MYTHIC_ITEMS else '暗金装备'
                            db['unique_items'][item_name] = {
                                'name': item_name,
                                'slot': target_slot,
                                'class': cls,
                                'rarity': rarity,
                                'ilvl': item_data.get('ilvl', 925),
                                'sockets': item_data.get('sockets', 0),
                                'effect': item_data.get('effect', ''),
                                'power': item_data.get('power', ''),
                                'fixed_affixes': item_data.get('fixed_affixes', []),
                                'random_affixes': item_data.get('random_affixes', [])
                            }

    gc.collect()
    _PROFESSION_CACHE[profession] = db
    return db

# 默认数据库实例（巫师）
DB = get_profession_db("巫师")