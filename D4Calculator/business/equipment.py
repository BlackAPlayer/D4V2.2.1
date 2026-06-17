# -*- coding: utf-8 -*-
# 模块: business/equipment

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import gc
import sys
import re
import math
import copy
from PIL import Image, ImageTk
import logging

from data.loader import FULL_DB, AFFIX_BY_POSITION, AFFIX_VALUES

def calculate_affix_value(affix_name, quality, is_ancient, is_reforge=False):
    if affix_name not in AFFIX_VALUES:
        return 0
    data = AFFIX_VALUES[affix_name]
    ratio = quality / 25.0
    base_value = data['min'] + (data['max'] - data['min']) * ratio
    if is_ancient:
        base_value *= 1.25
    if is_reforge:
        base_value *= 1.25
    return int(base_value)

def get_affixes_for_position(position, profession=None):
    position_key = position if position in AFFIX_BY_POSITION else '主手'
    if profession:
        main_stat = FULL_DB["main_stat"].get(profession, '智力')
        other_stats = {'力量', '敏捷', '意志'} - {main_stat}
    else:
        other_stats = set()
    affixes = []
    for affix_name in AFFIX_BY_POSITION[position_key]:
        if affix_name in other_stats:
            continue
        if affix_name in AFFIX_VALUES:
            data = AFFIX_VALUES[affix_name]
            affixes.append(f"+[{data['min']}-{data['max']}] {affix_name}")
    return affixes

def get_reforge_affixes_for_position(position, profession=None):
    position_key = position if position in FULL_DB.get('reforge_by_position', {}) else '主手'
    affixes = []
    for affix_name in FULL_DB.get('reforge_by_position', {}).get(position_key, []):
        if affix_name in AFFIX_VALUES:
            data = AFFIX_VALUES[affix_name]
            affixes.append(f"+[{data['min']}-{data['max']}] {affix_name}")
    return affixes

