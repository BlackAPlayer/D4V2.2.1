# -*- coding: utf-8 -*-
# 模块: data/loader

import json
import os
import sys
import gc
import logging
from PIL import Image, ImageTk

try:
    from config import resource_path, BASE_DIR
except ImportError:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    def resource_path(relative_path):
        return os.path.join(BASE_DIR, relative_path)

DB_FILE = os.path.join(BASE_DIR, 'full_database_new.json')
if not os.path.exists(DB_FILE):
    DB_FILE = resource_path('full_database_new.json')

try:
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        FULL_DB = json.load(f)
    logging.info("数据库加载成功: %s", DB_FILE)
except Exception as e:
    logging.warning("加载数据库失败: %s -> %s", DB_FILE, e)
    FULL_DB = {}

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
FULL_DB.setdefault('unique_items_v43', {})
FULL_DB.setdefault('seals', {})            # 新增
FULL_DB.setdefault('talisman_runes', {})   # 新增

if '主手' not in FULL_DB.get('affix_by_position', {}):
    FULL_DB['affix_by_position']['主手'] = []

GEMS_DATABASE = FULL_DB.get('gems', {})
RUNES_DATABASE = FULL_DB.get('runes', {})
AFFIX_VALUES = FULL_DB.get('affix_values', {})
AFFIX_BY_POSITION = FULL_DB.get('affix_by_position', {})
IMAGE_CACHE = {}

# 新增护身符数据导出
SEALS_DATABASE = FULL_DB.get('seals', {})
TALISMAN_RUNES_DATABASE = FULL_DB.get('talisman_runes', {})

def load_photo_image(path, size=None):
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

_PROFESSION_CACHE = {}

def get_profession_db(profession):
    if profession in _PROFESSION_CACHE:
        return _PROFESSION_CACHE[profession]

    db = {
        'powers': {'all': {}},
        'affixes_list': [],
        'transmute_list': [],
        'unique_items': {},
        'seals': {},           # 新增
        'talisman_runes': {},  # 新增
    }

    for name, data in FULL_DB['powers']['all'].items():
        power_class = data.get('class', '全职业')
        if power_class in ('全职业', profession, 'nan'):
            db['powers']['all'][name] = data

    for affix_name in FULL_DB['affix_by_position'].get('主手', []):
        if affix_name in AFFIX_VALUES:
            data = AFFIX_VALUES[affix_name]
            db['affixes_list'].append(f"+[{data['min']}-{data['max']}] {affix_name}")

    transmute_list = []
    for affix_name in FULL_DB.get('transmute_by_position', {}).get('主手', []):
        if affix_name in AFFIX_VALUES:
            v = AFFIX_VALUES[affix_name]
            transmute_list.append(f"+[{v['min']}-{v['max']}] {affix_name}")
        else:
            transmute_list.append(affix_name)
    db['transmute_list'] = transmute_list

    MYTHIC_ITEMS = {
        '祖父', '末日使者', '艾尔度因，正义之剑', '无星夜空之戒',
        '阿瓦里昂，莱姗德之矛', '堕狱传承', '破碎的誓言', '安达莉尔的仪容',
        '谐角之冠', '泰瑞尔之力', '涅塞科姆，绝望先驱', '塞利格的溶解之心',
        '虚假死亡之衣'
    }
    for name, data in FULL_DB['unique_items']['all'].items():
        if data.get('class', '全职业') in (profession, '全职业'):
            db['unique_items'][name] = data

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

    # 新增：护身符数据按职业过滤
    for seal_id, seal_data in FULL_DB.get('seals', {}).items():
        restriction = seal_data.get('class_restriction')
        if restriction is None or profession in restriction:
            db['seals'][seal_id] = seal_data

    for rune_id, rune_data in FULL_DB.get('talisman_runes', {}).items():
        restriction = rune_data.get('class_restriction')
        if restriction is None or profession in restriction:
            db['talisman_runes'][rune_id] = rune_data

    gc.collect()
    _PROFESSION_CACHE[profession] = db
    return db

# 新增护身符加载函数
def load_seals(profession=None):
    if profession:
        db = get_profession_db(profession)
        return db.get('seals', {})
    return SEALS_DATABASE

def load_talisman_runes(profession=None):
    if profession:
        db = get_profession_db(profession)
        return db.get('talisman_runes', {})
    return TALISMAN_RUNES_DATABASE

def load_runes(profession=None):
    return load_talisman_runes(profession)

DB = get_profession_db("巫师")