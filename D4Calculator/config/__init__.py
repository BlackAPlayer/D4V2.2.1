# -*- coding: utf-8 -*-
# config 包

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def resource_path(relative_path):
    """获取资源文件的绝对路径（兼容开发环境和打包环境）"""
    return os.path.join(BASE_DIR, relative_path)

PROFESSIONS = ["巫师", "野蛮人", "游侠", "德鲁伊", "死灵法师"]
POSITIONS = ["头盔", "胸甲", "手套", "裤子", "鞋子", "主手", "副手", "项链", "戒指1", "戒指2"]
WEAPON_TYPES = ["单手武器", "双手武器", "副手武器"]

COLORS = {
    'normal': '#C0A060', 'ancient': '#FFD700', 'reforge': '#FF6600',
    'reforge_blue': '#4169E1', 'transmute': '#FF69B4', 'transmute_gray': '#808080',
    'mythic_bg': '#4B0082', 'mythic_fg': '#EE82EE', 'duplicate_warning': '#FF0000',
    'rune_legendary': '#FFAA00', 'rune_rare': '#0066FF', 'rune_magic': '#6666FF',
}

SOCKETS_BY_POSITION = {
    "头盔": 2,
    "胸甲": 2,
    "手套": 0,
    "裤子": 2,
    "鞋子": 0,
    "主手": 1,
    "副手": 1,
    "项链": 1,
    "戒指1": 1,
    "戒指2": 1
}