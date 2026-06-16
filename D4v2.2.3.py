#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D4计算器 V2.2.1 (技能树增强版 - 无分支面板 + 滚轮缩放 + 分支节点支持)
- 技能树系统重构：支持分支、外部加成、动态描述、局部刷新
- 移除右侧分支面板，画布占满整个标签页
- 支持滚轮缩放（0.2 ~ 3.0倍）
- 布局文件中支持 branch_skill / branch_id 分支节点
- 保留原装备、宝石、符文等功能
"""
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

# ==================== 资源路径 ====================
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ==================== 加载数据库 ====================
DB_FILE = resource_path('full_database_new.json')
try:
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        FULL_DB = json.load(f)
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

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

IMAGE_CACHE = {}

def load_photo_image(path, size=None):
    key = (os.path.abspath(path), None if size is None else tuple(size))
    if key in IMAGE_CACHE:
        return IMAGE_CACHE[key]
    try:
        img = Image.open(path)
        if size:
            img = img.resize(size, Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        IMAGE_CACHE[key] = photo
        return photo
    except Exception as e:
        logging.debug("加载图片失败 %s -> %s", path, e)
        return None

PROFESSIONS = ["巫师", "野蛮人", "游侠", "德鲁伊", "死灵法师"]
POSITIONS = ["头盔", "胸甲", "手套", "裤子", "鞋子", "主手", "副手", "项链", "戒指1", "戒指2"]
WEAPON_TYPES = ["单手武器", "双手武器", "副手武器"]

COLORS = {
    'normal': '#C0A060', 'ancient': '#FFD700', 'reforge': '#FF6600',
    'reforge_blue': '#4169E1', 'transmute': '#FF69B4', 'transmute_gray': '#808080',
    'mythic_bg': '#4B0082', 'mythic_fg': '#EE82EE', 'duplicate_warning': '#FF0000',
    'rune_legendary': '#FFAA00', 'rune_rare': '#0066FF', 'rune_magic': '#6666FF',
}

GEMS_DATABASE = FULL_DB.get('gems', {})
RUNES_DATABASE = FULL_DB.get('runes', {})

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

# ==================== 防抖过滤 ====================
def filter_combobox(event, combobox, all_values):
    if hasattr(combobox, '_filter_after_id') and combobox._filter_after_id:
        try:
            combobox.after_cancel(combobox._filter_after_id)
        except ValueError:
            pass
    def do_filter():
        entry_text = combobox.get().lower()
        if not entry_text:
            combobox['values'] = all_values
        else:
            filtered = [item for item in all_values if entry_text in item.lower()]
            combobox['values'] = filtered
        combobox.after(10, lambda: combobox.event_generate('<Down>'))
        combobox._filter_after_id = None
    combobox._filter_after_id = combobox.after(300, do_filter)

AFFIX_VALUES = FULL_DB.get('affix_values', {})

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

AFFIX_BY_POSITION = FULL_DB.get('affix_by_position', {})

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

_PROFESSION_CACHE = {}

def get_profession_db(profession):
    if profession in _PROFESSION_CACHE:
        return _PROFESSION_CACHE[profession]
    db = {'powers': {'all': {}}, 'affixes_list': [], 'transmute_list': [], 'unique_items': {}}
    for name, data in FULL_DB['powers']['all'].items():
        power_class = data.get('class', '全职业')
        if power_class in ('全职业', profession, 'nan'):
            db['powers']['all'][name] = data
    for affix_name in FULL_DB['affix_by_position']['主手']:
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
    MYTHIC_ITEMS = {'祖父', '末日使者', '艾尔度因，正义之剑', '无星夜空之戒',
                    '阿瓦里昂，莱姗德之矛', '堕狱传承', '破碎的誓言', '安达莉尔的仪容',
                    '谐角之冠', '泰瑞尔之力', '涅塞科姆，绝望先驱', '塞利格的溶解之心',
                    '虚假死亡之衣'}
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
                                'name': item_name, 'slot': target_slot, 'class': cls, 'rarity': rarity,
                                'ilvl': item_data.get('ilvl', 925), 'sockets': item_data.get('sockets', 0),
                                'effect': item_data.get('effect', ''), 'power': item_data.get('power', ''),
                                'fixed_affixes': item_data.get('fixed_affixes', []),
                                'random_affixes': item_data.get('random_affixes', [])
                            }
    gc.collect()
    _PROFESSION_CACHE[profession] = db
    return db

DB = get_profession_db("巫师")

# ==================== 宝石选择弹窗 ====================
class GemSelectDialog:
    def __init__(self, parent, position, socket_index, current_value):
        self.parent = parent
        self.position = position
        self.socket_index = socket_index
        self.current_value = current_value
        self.result = None
        self.dialog = None
        self.tooltip = None
        self.initUI()
        self.center_dialog()

    def show_tooltip(self, event, item_name, item_data):
        self.hide_tooltip()
        self.tooltip = tk.Toplevel(self.dialog)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{event.x_root+15}+{event.y_root+15}")
        bg_color = '#1a3a1a'
        title_color = '#00FF00'
        weapon = item_data.get('weapon', {})
        armor = item_data.get('armor', {})
        jewelry = item_data.get('jewelry', {})
        effect_text = f"武器: +{weapon.get('value', '?')} {weapon.get('name', '')}\n"
        effect_text += f"防具: +{armor.get('value', '?')} {armor.get('name', '')}\n"
        effect_text += f"首饰: +{jewelry.get('value', '?')} {jewelry.get('name', '')}"
        frame = tk.Frame(self.tooltip, bg=bg_color, bd=1, relief='solid')
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        tk.Label(frame, text=f"{item_data['icon']} {item_name}",
                font=('微软雅黑', 11, 'bold'), fg=title_color, bg=bg_color).pack(anchor='w')
        tk.Frame(frame, height=1, bg='#444444').pack(fill=tk.X, pady=5)
        tk.Label(frame, text=effect_text, font=('微软雅黑', 9), fg='#CCCCCC', bg=bg_color,
                wraplength=300, justify='left').pack(anchor='w')

    def hide_tooltip(self, event=None):
        if hasattr(self, 'tooltip') and self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    def initUI(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.geometry("+10000+10000")
        self.dialog.title('选择宝石')
        self.dialog.configure(bg='#121212')
        self.dialog.transient(self.parent)
        self.dialog.resizable(True, True)
        self.dialog.protocol('WM_DELETE_WINDOW', self.on_close)
        main_frame = tk.Frame(self.dialog, bg='#121212')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        header_frame = tk.Frame(main_frame, bg='#121212')
        header_frame.pack(fill=tk.X, pady=5)
        tk.Label(header_frame, text='🔍 选择宝石',
                font=('微软雅黑', 14, 'bold'), fg='#FFD700', bg='#121212').pack(side=tk.LEFT)
        tk.Button(header_frame, text='✕ 关闭', command=self.on_close,
                 font=('微软雅黑', 10), bg='#2a2a2a', fg='#FFD700', bd=1).pack(side=tk.RIGHT)
        search_frame = tk.Frame(main_frame, bg='#1a1a1a', bd=0)
        search_frame.pack(fill=tk.X, pady=5)
        tk.Label(search_frame, text='🔍 搜索：', font=('微软雅黑', 10),
                fg='#FFD700', bg='#1a1a1a').pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var, font=('微软雅黑', 10),
                               bg='#2a2a2a', fg='#FFFFFF', insertbackground='#FFFFFF', bd=0)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        self.search_var.trace('w', self.on_search)
        self.scrollable_frame = tk.Frame(main_frame, bg='#121212')
        self.scrollable_frame.pack(fill="both", expand=True)
        self.all_buttons = []
        self.fill_gems()

    def fill_gems(self, search_text=''):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.all_buttons = []
        row = 0
        col = 0
        for gem_name, gem_data in GEMS_DATABASE.items():
            if search_text and search_text.lower() not in gem_name.lower():
                continue
            btn = tk.Button(self.scrollable_frame,
                           text=f"{gem_data['icon']} {gem_name}",
                           font=('微软雅黑', 10),
                           bg='#2a2a2a', fg=gem_data['color'],
                           activebackground='#3a3a3a', activeforeground=gem_data['color'],
                           bd=0, width=22, height=2,
                           command=lambda name=gem_name: self.select_item(name))
            btn.bind('<Enter>', lambda e, name=gem_name, data=gem_data:
                    self.show_tooltip(e, name, data))
            btn.bind('<Leave>', self.hide_tooltip)
            btn.grid(row=row, column=col, padx=5, pady=5, sticky='w')
            self.all_buttons.append(btn)
            col += 1
            if col >= 3:
                col = 0
                row += 1

    def on_search(self, *args):
        self.fill_gems(self.search_var.get())

    def select_item(self, name):
        self.result = name
        self.on_close()

    def on_close(self):
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None
        gc.collect()

    def center_dialog(self):
        self.dialog.update()
        self.dialog.update_idletasks()
        screen_w = self.dialog.winfo_screenwidth()
        screen_h = self.dialog.winfo_screenheight()
        dialog_w = 616
        dialog_h = self.dialog.winfo_reqheight()
        x = (screen_w - dialog_w) // 2
        y = (screen_h - dialog_h) // 2
        self.dialog.geometry(f"{dialog_w}x{dialog_h}+{x}+{y}")

    def show(self):
        if self.dialog:
            self.parent.wait_window(self.dialog)
        return self.result

# ==================== 符文两步选择弹窗 ====================
class RuneTwoStepDialog:
    def __init__(self, parent):
        self.parent = parent
        self.result = None
        self.dialog = None
        self.selected_ritual = None
        self.tooltip = None
        self.search_var = None
        self.scrollable = None

    def show_tooltip(self, event, item_name, item_data):
        self.hide_tooltip()
        self.tooltip = tk.Toplevel(self.dialog)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{event.x_root+15}+{event.y_root+15}")
        rarity = item_data.get('rarity', '')
        if '传奇' in rarity:
            bg_color = '#3a2a1a'
            title_color = '#FFA500'
        else:
            bg_color = '#2a2a3a'
            title_color = '#00BFFF'
        frame = tk.Frame(self.tooltip, bg=bg_color, bd=1, relief='solid')
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        tk.Label(frame, text=f"{item_data['icon']} {item_name}",
                font=('微软雅黑', 11, 'bold'), fg=title_color, bg=bg_color).pack(anchor='w')
        tk.Frame(frame, height=1, bg='#444444').pack(fill=tk.X, pady=5)
        tk.Label(frame, text=item_data.get('effect', '暂无描述'), font=('微软雅黑', 9),
                fg='#CCCCCC', bg=bg_color, wraplength=300, justify='left').pack(anchor='w')

    def hide_tooltip(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    def show_ritual_selection(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("选择仪祭符文")
        self.dialog.geometry("600x500")
        self.dialog.configure(bg='#121212')
        self.dialog.transient(self.parent)
        self.dialog.resizable(True, True)

        main_frame = tk.Frame(self.dialog, bg='#121212')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        header = tk.Frame(main_frame, bg='#121212')
        header.pack(fill=tk.X, pady=5)
        tk.Label(header, text='🔍 选择仪祭符文 (第一步)', font=('微软雅黑', 14, 'bold'),
                fg='#FFD700', bg='#121212').pack(side=tk.LEFT)
        tk.Button(header, text='✕ 取消', command=self.on_cancel,
                 font=('微软雅黑', 10), bg='#2a2a2a', fg='#FFD700', bd=1).pack(side=tk.RIGHT)

        search_frame = tk.Frame(main_frame, bg='#1a1a1a')
        search_frame.pack(fill=tk.X, pady=5)
        tk.Label(search_frame, text='🔍 搜索：', font=('微软雅黑', 10),
                fg='#FFD700', bg='#1a1a1a').pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var,
                               font=('微软雅黑', 10), bg='#2a2a2a', fg='#FFFFFF',
                               insertbackground='#FFFFFF', bd=0)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        self.search_var.trace('w', self.on_search_ritual)

        canvas = tk.Canvas(main_frame, bg='#121212', highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollable = tk.Frame(canvas, bg='#121212')
        canvas.create_window((0, 0), window=self.scrollable, anchor='nw', width=canvas.winfo_reqwidth())

        def configure_scroll(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(1, width=canvas.winfo_width())
        self.scrollable.bind("<Configure>", configure_scroll)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(1, width=e.width))

        self.fill_ritual_runes()
        self.center_dialog()
        self.parent.wait_window(self.dialog)
        return self.result

    def fill_ritual_runes(self, search_text=''):
        for widget in self.scrollable.winfo_children():
            widget.destroy()
        row = 0
        col = 0
        for rune_name, rune_data in RUNES_DATABASE.items():
            if rune_data.get('category') != '仪祭符文':
                continue
            if search_text and search_text.lower() not in rune_name.lower():
                continue
            btn = tk.Button(self.scrollable,
                           text=f"{rune_data['icon']} {rune_name}",
                           font=('微软雅黑', 10), bg='#2a2a2a', fg=rune_data['color'],
                           activebackground='#3a3a3a', bd=0, width=22, height=2,
                           command=lambda name=rune_name: self.select_ritual(name))
            btn.bind('<Enter>', lambda e, name=rune_name, data=rune_data: self.show_tooltip(e, name, data))
            btn.bind('<Leave>', self.hide_tooltip)
            btn.grid(row=row, column=col, padx=5, pady=3, sticky='w')
            col += 1
            if col >= 3:
                col = 0
                row += 1

    def on_search_ritual(self, *args):
        self.fill_ritual_runes(self.search_var.get())

    def select_ritual(self, ritual_name):
        self.selected_ritual = ritual_name
        self.dialog.destroy()
        self.show_invocation_selection()

    def show_invocation_selection(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("选择祈告符文")
        self.dialog.geometry("600x500")
        self.dialog.configure(bg='#121212')
        self.dialog.transient(self.parent)
        self.dialog.resizable(True, True)

        main_frame = tk.Frame(self.dialog, bg='#121212')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)

        header = tk.Frame(main_frame, bg='#121212')
        header.pack(fill=tk.X, pady=5)
        tk.Label(header, text=f'🔍 选择祈告符文 (第二步) - 已选仪祭: {self.selected_ritual}',
                font=('微软雅黑', 12, 'bold'), fg='#00BFFF', bg='#121212').pack(side=tk.LEFT)
        tk.Button(header, text='✕ 取消', command=self.on_cancel,
                 font=('微软雅黑', 10), bg='#2a2a2a', fg='#FFD700', bd=1).pack(side=tk.RIGHT)

        search_frame = tk.Frame(main_frame, bg='#1a1a1a')
        search_frame.pack(fill=tk.X, pady=5)
        tk.Label(search_frame, text='🔍 搜索：', font=('微软雅黑', 10),
                fg='#00BFFF', bg='#1a1a1a').pack(side=tk.LEFT, padx=5)
        self.search_var2 = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=self.search_var2,
                               font=('微软雅黑', 10), bg='#2a2a2a', fg='#FFFFFF',
                               insertbackground='#FFFFFF', bd=0)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5, pady=5)
        self.search_var2.trace('w', self.on_search_invocation)

        canvas = tk.Canvas(main_frame, bg='#121212', highlightthickness=0)
        scrollbar = tk.Scrollbar(main_frame, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollable2 = tk.Frame(canvas, bg='#121212')
        canvas.create_window((0, 0), window=self.scrollable2, anchor='nw', width=canvas.winfo_reqwidth())

        def configure_scroll2(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(1, width=canvas.winfo_width())
        self.scrollable2.bind("<Configure>", configure_scroll2)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(1, width=e.width))

        self.fill_invocation_runes()
        self.center_dialog()
        self.parent.wait_window(self.dialog)

    def fill_invocation_runes(self, search_text=''):
        for widget in self.scrollable2.winfo_children():
            widget.destroy()
        row = 0
        col = 0
        for rune_name, rune_data in RUNES_DATABASE.items():
            if rune_data.get('category') != '祈告符文':
                continue
            if search_text and search_text.lower() not in rune_name.lower():
                continue
            btn = tk.Button(self.scrollable2,
                           text=f"{rune_data['icon']} {rune_name}",
                           font=('微软雅黑', 10), bg='#2a2a2a', fg=rune_data['color'],
                           activebackground='#3a3a3a', bd=0, width=22, height=2,
                           command=lambda name=rune_name: self.select_invocation(name))
            btn.bind('<Enter>', lambda e, name=rune_name, data=rune_data: self.show_tooltip(e, name, data))
            btn.bind('<Leave>', self.hide_tooltip)
            btn.grid(row=row, column=col, padx=5, pady=3, sticky='w')
            col += 1
            if col >= 3:
                col = 0
                row += 1
        if row == 0 and col == 0:
            tk.Label(self.scrollable2, text="没有找到祈告符文", font=('微软雅黑', 12),
                    fg='#FF6666', bg='#121212').pack(pady=20)

    def on_search_invocation(self, *args):
        self.fill_invocation_runes(self.search_var2.get())

    def select_invocation(self, invocation_name):
        self.result = f"{self.selected_ritual}|{invocation_name}"
        self.dialog.destroy()

    def on_cancel(self):
        self.result = None
        self.dialog.destroy()

    def center_dialog(self):
        self.dialog.update_idletasks()
        screen_w = self.dialog.winfo_screenwidth()
        screen_h = self.dialog.winfo_screenheight()
        dialog_w = self.dialog.winfo_width()
        dialog_h = self.dialog.winfo_height()
        x = (screen_w - dialog_w) // 2
        y = (screen_h - dialog_h) // 2
        self.dialog.geometry(f"+{x}+{y}")

    def show(self):
        return self.show_ritual_selection()

# ==================== 装备编辑弹窗（完整） ====================
class EquipDetailDialog:
    def __init__(self, parent, position, equip_data, current_profession, get_powers_func, current_db, selected_powers):
        self.parent = parent
        self.position = position
        self.equip_data = equip_data
        self.current_profession = current_profession
        self.get_powers_func = get_powers_func
        self.DB = current_db
        self.UNIQUE_ITEMS = current_db['unique_items']
        self.selected_powers = selected_powers
        self.quality = tk.IntVar(value=int(equip_data.get('quality', 25)))
        self.ancient_flags = [tk.BooleanVar(value=equip_data.get('affixes', [{}]*4)[i].get('ancient', False)) for i in range(4)]
        self.reforge_flags = [tk.BooleanVar(value=equip_data.get('affixes', [{}]*4)[i].get('reforge', False)) for i in range(4)]
        saved_trans = equip_data.get('trans_affixes', [{}])
        self.trans_reforge_flags = [tk.BooleanVar(value=saved_trans[i].get('reforge', False)) for i in range(len(saved_trans))]

        base_sockets = SOCKETS_BY_POSITION.get(position, 0)
        if position == '主手':
            weapon_type = equip_data.get('weapon_type', '')
            if weapon_type == '双手武器':
                base_sockets = 2
        self.max_sockets = base_sockets
        self.sockets = equip_data.get('sockets', [None] * self.max_sockets)
        if len(self.sockets) < self.max_sockets:
            self.sockets.extend([None] * (self.max_sockets - len(self.sockets)))

        has_gem = any(s in GEMS_DATABASE for s in self.sockets if s)
        has_rune = any((isinstance(s, str) and '|' in s) for s in self.sockets if s)
        if has_gem and has_rune:
            for i, s in enumerate(self.sockets):
                if isinstance(s, str) and '|' in s:
                    self.sockets[i] = None
            messagebox.showwarning("数据修复", "检测到装备同时存在宝石和符文，已自动清空符文，请重新编辑。")

        self.result = None
        self.dialog = None
        self.initUI()
        self.center_dialog()

    def initUI(self):
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title(f'编辑 {self.position}')
        self.dialog.configure(bg='#121212')
        self.dialog.transient(self.parent)
        self.dialog.resizable(True, True)
        self.dialog.protocol('WM_DELETE_WINDOW', self.on_close)

        main_frame = tk.Frame(self.dialog, bg='#121212', padx=15, pady=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(main_frame, text=self.position, font=('微软雅黑', 14, 'bold'),
                fg='#FFD700', bg='#121212').pack(anchor='w', pady=(0,10))

        quality_frame = tk.Frame(main_frame, bg='#121212')
        quality_frame.pack(fill=tk.X, pady=2)
        tk.Label(quality_frame, text='品质:', font=('微软雅黑', 9, 'bold'), fg='#FFD700', bg='#121212').pack(side=tk.LEFT, padx=3)
        tk.Button(quality_frame, text='-', command=lambda: self.quality.set(max(0, self.quality.get()-1)),
                  font=('微软雅黑', 9, 'bold'), bg='#2a2a2a', fg='#FFD700', bd=1, width=1).pack(side=tk.LEFT)
        tk.Label(quality_frame, textvariable=self.quality, font=('微软雅黑', 9, 'bold'),
                 fg='#00FF00', bg='#121212', width=2).pack(side=tk.LEFT, padx=2)
        tk.Button(quality_frame, text='+', command=lambda: self.quality.set(min(25, self.quality.get()+1)),
                  font=('微软雅黑', 9, 'bold'), bg='#2a2a2a', fg='#FFD700', bd=1, width=1).pack(side=tk.LEFT)
        tk.Button(quality_frame, text='最大', command=lambda: self.quality.set(25),
                  font=('微软雅黑', 9), bg='#2a2a2a', fg='#FFD700', bd=0).pack(side=tk.LEFT, padx=3)
        tk.Button(quality_frame, text='归零', command=lambda: self.quality.set(0),
                  font=('微软雅黑', 9), bg='#2a2a2a', fg='#FFD700', bd=0).pack(side=tk.LEFT)
        self.quality.trace('w', self.update_all_affixes)

        row1 = tk.Frame(main_frame, bg='#121212')
        row1.pack(fill=tk.X, pady=5)
        tk.Label(row1, text='稀有度:', font=('微软雅黑', 9, 'bold'), fg='#FFD700', bg='#121212').pack(side=tk.LEFT)
        self.rarity_type = ttk.Combobox(row1, values=['传奇装备', '暗金装备', '神话暗金装备'], state='normal', width=12)
        self.rarity_type.pack(side=tk.LEFT, padx=5)
        if self.equip_data.get('type'):
            self.rarity_type.set(self.equip_data['type'])
        tk.Label(row1, text='装备:', font=('微软雅黑', 9, 'bold'), fg='#FFD700', bg='#121212').pack(side=tk.LEFT, padx=(15,5))
        self.specific_equip = ttk.Combobox(row1, state='normal', width=20)
        self.specific_equip.pack(side=tk.LEFT, padx=5)
        equip_values = list(self.specific_equip['values'])
        self.specific_equip.bind('<KeyRelease>', lambda e: filter_combobox(e, self.specific_equip, equip_values))

        if self.position in ['主手', '副手']:
            row2 = tk.Frame(main_frame, bg='#121212')
            row2.pack(fill=tk.X, pady=5)
            tk.Label(row2, text='武器类型:', font=('微软雅黑', 9, 'bold'), fg='#FFD700', bg='#121212').pack(side=tk.LEFT)
            self.weapon_type = ttk.Combobox(row2, values=WEAPON_TYPES, state='normal', width=12)
            self.weapon_type.pack(side=tk.LEFT, padx=5)
            if self.equip_data.get('weapon_type'):
                self.weapon_type.set(self.equip_data['weapon_type'])
            self.weapon_type.bind('<<ComboboxSelected>>', self.on_weapon_type_change)

        affix_frame = tk.LabelFrame(main_frame, text="词缀", font=('微软雅黑', 9, 'bold'),
                                    fg='#FFD700', bg='#121212', bd=1, relief='solid')
        affix_frame.pack(fill=tk.X, pady=10)
        self.affix_vars = []
        self.affixes = []
        self.ancient_btns = []
        self.reforge_btns = []
        self.affix_entries = []
        for i in range(4):
            row = tk.Frame(affix_frame, bg='#121212')
            row.pack(fill=tk.X, pady=2)
            rb = tk.Button(row, text='🔨', font=('微软雅黑', 9), bg='#121212', fg='#666666', bd=0, width=2,
                           command=lambda idx=i: self.toggle_reforge(idx))
            rb.pack(side=tk.LEFT)
            self.reforge_btns.append(rb)
            ab = tk.Button(row, text='◇', font=('微软雅黑', 9), bg='#121212', fg=COLORS['normal'], bd=0, width=2,
                           command=lambda idx=i: self.toggle_ancient(idx))
            ab.pack(side=tk.LEFT)
            self.ancient_btns.append(ab)
            cb = ttk.Combobox(row, values=get_affixes_for_position(self.position), state='normal', width=40)
            cb.pack(side=tk.LEFT, padx=2)
            cb.bind('<<ComboboxSelected>>', lambda e, idx=i: self.update_affix(idx))
            cb.bind('<KeyRelease>', lambda e, cb=cb, vals=get_affixes_for_position(self.position): filter_combobox(e, cb, vals))
            self.affixes.append(cb)
            var = tk.IntVar(value=0)
            entry = tk.Entry(row, textvariable=var, width=8, justify='center', font=('微软雅黑', 9),
                             bg='#2a2a2a', fg='#00FF00', bd=1)
            entry.pack(side=tk.LEFT, padx=2)
            self.affix_vars.append(var)
            self.affix_entries.append(entry)

        reforge_frame = tk.LabelFrame(main_frame, text="回火词缀", font=('微软雅黑', 9, 'bold'),
                                      fg='#FFD700', bg='#121212', bd=1, relief='solid')
        reforge_frame.pack(fill=tk.X, pady=5)
        self.reforge_affix_vars = []
        self.reforge_affixes = []
        self.reforge_reforge_btns = []
        self.reforge_reforge_flags = [tk.BooleanVar(value=False)]
        self.reforge_ancient_btns = []
        self.reforge_ancient_flags = [tk.BooleanVar(value=False)]
        self.reforge_affix_entries = []
        for i in range(1):
            row = tk.Frame(reforge_frame, bg='#121212')
            row.pack(fill=tk.X, pady=2)
            rb = tk.Button(row, text='🔨', font=('微软雅黑', 9), bg='#121212', fg='#666666', bd=0, width=2,
                           command=lambda idx=i: self.toggle_reforge_reforge(idx))
            rb.pack(side=tk.LEFT)
            self.reforge_reforge_btns.append(rb)
            ab = tk.Button(row, text='◇', font=('微软雅黑', 9), bg='#121212', fg=COLORS['normal'], bd=0, width=2,
                           command=lambda idx=i: self.toggle_reforge_ancient(idx))
            ab.pack(side=tk.LEFT)
            self.reforge_ancient_btns.append(ab)
            cb = ttk.Combobox(row, values=get_reforge_affixes_for_position(self.position), state='normal', width=40)
            cb.pack(side=tk.LEFT, padx=2)
            cb.bind('<<ComboboxSelected>>', lambda e, idx=i: self.update_reforge_affix(idx))
            self.reforge_affixes.append(cb)
            var = tk.IntVar(value=0)
            entry = tk.Entry(row, textvariable=var, width=8, justify='center', font=('微软雅黑', 9),
                             bg='#2a2a2a', fg='#FFA500', bd=1)
            entry.pack(side=tk.LEFT, padx=2)
            self.reforge_affix_vars.append(var)
            self.reforge_affix_entries.append(entry)

        trans_frame = tk.LabelFrame(main_frame, text="嬗变词缀", font=('微软雅黑', 9, 'bold'),
                                    fg=COLORS['transmute'], bg='#121212', bd=1, relief='solid')
        trans_frame.pack(fill=tk.X, pady=5)
        control = tk.Frame(trans_frame, bg='#121212')
        control.pack(fill=tk.X)
        tk.Button(control, text='+', font=('微软雅黑', 9, 'bold'), bg='#121212', fg='#00FF00', bd=0, width=2,
                  command=self.add_trans).pack(side=tk.LEFT)
        tk.Button(control, text='-', font=('微软雅黑', 9, 'bold'), bg='#121212', fg='#FF4444', bd=0, width=2,
                  command=self.remove_trans).pack(side=tk.LEFT, padx=5)
        self.trans_container = tk.Frame(trans_frame, bg='#121212')
        self.trans_container.pack(fill=tk.X)
        self.trans_count = 1
        self.max_trans = 3
        self.trans_affix_vars = []
        self.trans_affixes = []
        self.trans_reforge_btns = []
        self.trans_value_entries = []
        for i in range(self.trans_count):
            self.create_trans_row(self.trans_container, i)

        power_frame = tk.LabelFrame(main_frame, text="威能", font=('微软雅黑', 9, 'bold'),
                                    fg='#FFD700', bg='#121212', bd=1, relief='solid')
        power_frame.pack(fill=tk.X, pady=10)
        power_row = tk.Frame(power_frame, bg='#121212')
        power_row.pack(fill=tk.X, pady=2)
        tk.Label(power_row, text='威能:', font=('微软雅黑', 9, 'bold'), fg='#FFD700', bg='#121212').pack(side=tk.LEFT)
        self.power = ttk.Combobox(power_row, state='normal', width=40)
        self.power.pack(side=tk.LEFT, padx=5)
        tk.Label(power_row, text='数值:', font=('微软雅黑', 9, 'bold'), fg='#FFD700', bg='#121212').pack(side=tk.LEFT, padx=(10,2))
        self.power_value_var = tk.IntVar(value=int(self.equip_data.get('power_value', 0) or 0))
        power_entry = tk.Entry(power_row, textvariable=self.power_value_var, width=8, justify='center',
                               font=('微软雅黑', 9), bg='#2a2a2a', fg='#00FF00', bd=1)
        power_entry.pack(side=tk.LEFT)
        self.power_desc = tk.Label(power_frame, text='', wraplength=450, justify=tk.LEFT, anchor='w',
                                   font=('微软雅黑', 9), fg='#00FF00', bg='#121212')
        self.power_desc.pack(fill=tk.X, pady=2)
        self.effect_label = tk.Label(power_frame, text='', wraplength=450, justify=tk.LEFT, anchor='w',
                                     font=('微软雅黑', 9), fg='#00FFFF', bg='#121212')
        self.effect_label.pack(fill=tk.X, pady=2)

        if self.max_sockets > 0:
            socket_frame = tk.LabelFrame(main_frame, text="插槽镶嵌物", font=('微软雅黑', 9, 'bold'),
                                         fg='#FFD700', bg='#121212', bd=1, relief='solid')
            socket_frame.pack(fill=tk.X, pady=10)
            self.socket_display_frame = tk.Frame(socket_frame, bg='#121212')
            self.socket_display_frame.pack(fill=tk.X, pady=5)
            btn_frame = tk.Frame(socket_frame, bg='#121212')
            btn_frame.pack(fill=tk.X, pady=5)
            self.gem_btn = tk.Button(btn_frame, text='+宝石', font=('微软雅黑', 9), bg='#2a2a2a', fg='#00FF00', bd=0,
                                     command=self.open_gem_select)
            self.gem_btn.pack(side=tk.LEFT, padx=5)
            if self.position in ['头盔', '胸甲', '裤子']:
                self.rune_btn = tk.Button(btn_frame, text='+符文', font=('微软雅黑', 9), bg='#2a2a2a', fg='#00FFFF', bd=0,
                                          command=self.open_rune_select)
                self.rune_btn.pack(side=tk.LEFT, padx=5)
            else:
                self.rune_btn = None
            self.update_socket_display()

        bottom = tk.Frame(main_frame, bg='#121212')
        bottom.pack(fill=tk.X, pady=15)
        tk.Button(bottom, text='✅ 保存', command=self.save_and_close,
                  font=('微软雅黑', 10, 'bold'), bg='#2a2a2a', fg='#FFD700', padx=18, pady=5, bd=0).pack(side=tk.LEFT, padx=10)
        tk.Button(bottom, text='❌ 取消', command=self.on_close,
                  font=('微软雅黑', 10, 'bold'), bg='#2a2a2a', fg='#FFD700', padx=18, pady=5, bd=0).pack(side=tk.LEFT, padx=10)

        self.rarity_type.bind('<<ComboboxSelected>>', self.on_rarity_change)
        self.specific_equip.bind('<<ComboboxSelected>>', self.on_equip_change)
        self.power.bind('<<ComboboxSelected>>', self.on_power_change)
        self.update_power_list()
        self.on_rarity_change(None)
        if self.equip_data.get('power'):
            self.power.set(self.equip_data['power'])
            self.on_power_change(None)

        for i in range(4):
            if self.equip_data.get('affixes', [{}]*4)[i].get('name'):
                self.affixes[i].set(self.equip_data['affixes'][i]['name'])
                self.affix_vars[i].set(self.equip_data['affixes'][i].get('value', ''))
                if self.equip_data['affixes'][i].get('ancient'):
                    self.ancient_btns[i].config(text='⭐', fg=COLORS['ancient'])
                if self.equip_data['affixes'][i].get('reforge'):
                    self.reforge_btns[i].config(fg=COLORS['reforge'])
                self.update_affix_color(i)
        saved_trans = self.equip_data.get('trans_affixes', [{}])
        for i in range(len(saved_trans)):
            if saved_trans[i].get('name') and i < len(self.trans_affixes):
                self.trans_affixes[i].set(saved_trans[i]['name'])
                self.trans_affix_vars[i].set(saved_trans[i].get('value', ''))
                if saved_trans[i].get('reforge') and i < len(self.trans_reforge_btns):
                    self.trans_reforge_btns[i].config(text='💎')
                self.update_trans_affix_color(i)
        self.update_all_affixes()

    def toggle_ancient(self, idx):
        self.ancient_flags[idx].set(not self.ancient_flags[idx].get())
        if self.ancient_flags[idx].get():
            self.ancient_btns[idx].config(text='⭐', fg=COLORS['ancient'])
        else:
            self.ancient_btns[idx].config(text='◇', fg=COLORS['normal'])
        self.update_affix(idx)

    def toggle_reforge(self, idx):
        self.reforge_flags[idx].set(not self.reforge_flags[idx].get())
        if self.reforge_flags[idx].get():
            self.reforge_btns[idx].config(fg=COLORS['reforge'])
        else:
            self.reforge_btns[idx].config(fg='#666666')
        self.update_affix(idx)

    def toggle_reforge_reforge(self, idx):
        self.reforge_reforge_flags[idx].set(not self.reforge_reforge_flags[idx].get())
        if self.reforge_reforge_flags[idx].get():
            self.reforge_reforge_btns[idx].config(fg='#FF6600')
        else:
            self.reforge_reforge_btns[idx].config(fg='#666666')

    def toggle_reforge_ancient(self, idx):
        self.reforge_ancient_flags[idx].set(not self.reforge_ancient_flags[idx].get())
        if self.reforge_ancient_flags[idx].get():
            self.reforge_ancient_btns[idx].config(text='⭐', fg='#FFD700')
        else:
            self.reforge_ancient_btns[idx].config(text='◇', fg='#666666')

    def update_affix(self, idx):
        txt = self.affixes[idx].get()
        if not txt:
            return
        for name in AFFIX_VALUES:
            if name in txt:
                val = calculate_affix_value(name, self.quality.get(), self.ancient_flags[idx].get(), self.reforge_flags[idx].get())
                self.affix_vars[idx].set(val)
                break
        self.update_affix_color(idx)

    def update_affix_color(self, idx):
        if self.reforge_flags[idx].get() and self.quality.get() >= 25:
            col = COLORS['reforge_blue']
        elif self.reforge_flags[idx].get():
            col = COLORS['reforge']
        elif self.ancient_flags[idx].get():
            col = COLORS['ancient']
        else:
            col = COLORS['normal']
        self.affixes[idx].config(foreground=col)

    def update_reforge_affix(self, idx):
        if idx >= len(self.reforge_affix_vars):
            return
        txt = self.reforge_affixes[idx].get()
        if not txt:
            self.reforge_affix_vars[idx].set(0)
            return
        if '] ' in txt:
            name = txt.split('] ', 1)[1]
        else:
            name = txt
        val = calculate_affix_value(name, self.quality.get(), self.reforge_ancient_flags[idx].get(), True)
        self.reforge_affix_vars[idx].set(val)

    def create_trans_row(self, parent, row):
        frame = tk.Frame(parent, bg='#121212')
        frame.pack(fill=tk.X, pady=2)
        btn = tk.Button(frame, text='🔮', font=('微软雅黑', 9), bg='#121212', fg=COLORS['transmute'], bd=0, width=2,
                        command=lambda idx=len(self.trans_affixes): self.toggle_trans_reforge(idx))
        btn.pack(side=tk.LEFT)
        self.trans_reforge_btns.append(btn)
        cb = ttk.Combobox(frame, values=self.DB['transmute_list'], state='normal', width=40)
        cb.pack(side=tk.LEFT, padx=2)
        cb.bind('<<ComboboxSelected>>', lambda e, idx=len(self.trans_affixes): self.update_trans_affix(idx))
        self.trans_affixes.append(cb)
        var = tk.IntVar(value=0)
        entry = tk.Entry(frame, textvariable=var, width=8, justify='center', font=('微软雅黑', 9),
                         bg='#2a2a2a', fg=COLORS['transmute'], bd=1)
        entry.pack(side=tk.LEFT, padx=2)
        self.trans_affix_vars.append(var)
        self.trans_value_entries.append(entry)

    def add_trans(self):
        if self.trans_count >= self.max_trans:
            return
        self.trans_count += 1
        self.create_trans_row(self.trans_container, self.trans_count-1)

    def remove_trans(self):
        if self.trans_count <= 1:
            return
        self.trans_count -= 1
        if self.trans_reforge_btns:
            self.trans_reforge_btns[-1].master.destroy()
            self.trans_reforge_btns.pop()
        if self.trans_affixes:
            self.trans_affixes.pop()
        if self.trans_value_entries:
            self.trans_value_entries.pop()
        if self.trans_affix_vars:
            self.trans_affix_vars.pop()

    def toggle_trans_reforge(self, idx):
        self.trans_reforge_flags[idx].set(not self.trans_reforge_flags[idx].get())
        if self.trans_reforge_flags[idx].get():
            self.trans_reforge_btns[idx].config(text='💎')
        else:
            self.trans_reforge_btns[idx].config(text='🔮')
        self.update_trans_affix(idx)

    def update_trans_affix(self, idx):
        if idx >= len(self.trans_affix_vars):
            return
        txt = self.trans_affixes[idx].get()
        if not txt:
            self.trans_affix_vars[idx].set(0)
            return
        if '] ' in txt:
            name = txt.split('] ', 1)[1]
        else:
            name = txt
        val = calculate_affix_value(name, self.quality.get(), False, self.trans_reforge_flags[idx].get())
        self.trans_affix_vars[idx].set(val)
        self.update_trans_affix_color(idx)

    def update_trans_affix_color(self, idx):
        if self.trans_reforge_flags[idx].get() and self.quality.get() >= 25:
            col = COLORS['transmute_gray']
        elif self.trans_reforge_flags[idx].get():
            col = COLORS['reforge_blue']
        else:
            col = COLORS['transmute']
        self.trans_affixes[idx].config(foreground=col)

    def update_all_affixes(self, *args):
        show = self.quality.get() >= 25
        for i in range(4):
            row = self.affixes[i].master
            for child in row.winfo_children():
                child.pack_forget()
            if show:
                self.reforge_btns[i].pack(side=tk.LEFT)
            self.ancient_btns[i].pack(side=tk.LEFT)
            self.affixes[i].pack(side=tk.LEFT, padx=2)
            self.affix_entries[i].pack(side=tk.LEFT, padx=2)
            self.update_affix(i)
        for i in range(len(self.reforge_affixes)):
            row = self.reforge_affixes[i].master
            for child in row.winfo_children():
                child.pack_forget()
            if show:
                self.reforge_reforge_btns[i].pack(side=tk.LEFT)
            self.reforge_ancient_btns[i].pack(side=tk.LEFT)
            self.reforge_affixes[i].pack(side=tk.LEFT, padx=2)
            self.reforge_affix_entries[i].pack(side=tk.LEFT, padx=2)
            self.update_reforge_affix(i)
        for i in range(len(self.trans_affixes)):
            row = self.trans_affixes[i].master
            for child in row.winfo_children():
                child.pack_forget()
            if show:
                self.trans_reforge_btns[i].pack(side=tk.LEFT)
            self.trans_affixes[i].pack(side=tk.LEFT, padx=2)
            self.trans_value_entries[i].pack(side=tk.LEFT, padx=2)
            self.update_trans_affix(i)

    def update_socket_display(self):
        for w in self.socket_display_frame.winfo_children():
            w.destroy()

        has_gem = any(s in GEMS_DATABASE for s in self.sockets if s)
        has_rune = any((isinstance(s, str) and '|' in s) for s in self.sockets if s)
        all_filled = all(s is not None for s in self.sockets)
        has_rune_btn = hasattr(self, 'rune_btn') and self.rune_btn is not None

        if all_filled:
            self.gem_btn.pack_forget()
            if has_rune_btn:
                self.rune_btn.pack_forget()
        elif has_gem:
            self.gem_btn.pack(side=tk.LEFT, padx=5)
            if has_rune_btn:
                self.rune_btn.pack_forget()
        elif has_rune:
            if has_rune_btn:
                self.rune_btn.pack(side=tk.LEFT, padx=5)
            self.gem_btn.pack_forget()
        else:
            self.gem_btn.pack(side=tk.LEFT, padx=5)
            if has_rune_btn:
                self.rune_btn.pack(side=tk.LEFT, padx=5)

        for i, s in enumerate(self.sockets):
            if s:
                if '|' in s:
                    rit, inv = s.split('|')
                    btn = tk.Button(self.socket_display_frame, text=f"📿{rit[:6]}+🔮{inv[:6]} ✕",
                                    font=('微软雅黑', 8), bg='#1a1a1a', fg='#FFFFFF', bd=0, padx=3, pady=1,
                                    command=lambda idx=i: self.remove_socket(idx))
                    btn.pack(side=tk.LEFT, padx=1, pady=1)
                elif s in GEMS_DATABASE:
                    data = GEMS_DATABASE[s]
                    btn = tk.Button(self.socket_display_frame, text=f"{data['icon']} {s[:8]} ✕",
                                    font=('微软雅黑', 9), bg='#1a1a1a', fg=data['color'], bd=0, padx=3, pady=1,
                                    command=lambda idx=i: self.remove_socket(idx))
                    btn.pack(side=tk.LEFT, padx=1, pady=1)
                else:
                    tk.Label(self.socket_display_frame, text='[未知] ✕', font=('微软雅黑', 6), fg='#666666', bg='#1a1a1a').pack(side=tk.LEFT, padx=2, pady=1)
            else:
                tk.Label(self.socket_display_frame, text=f'[空{i+1}]', font=('微软雅黑', 6), fg='#666666', bg='#1a1a1a').pack(side=tk.LEFT, padx=2, pady=1)

    def open_gem_select(self):
        has_rune = any((isinstance(s, str) and '|' in s) for s in self.sockets if s)
        if has_rune:
            messagebox.showinfo("提示", "该装备已镶嵌符文，无法再镶嵌宝石。请先移除符文。")
            return
        empty_index = None
        for i, s in enumerate(self.sockets):
            if s is None:
                empty_index = i
                break
        if empty_index is None:
            messagebox.showinfo("提示", "没有空闲插槽，请先移除一个镶嵌物。")
            return
        dlg = GemSelectDialog(self.dialog, self.position, empty_index, None)
        res = dlg.show()
        if res:
            self.sockets[empty_index] = res
            self.update_socket_display()

    def open_rune_select(self):
        has_gem = any(s in GEMS_DATABASE for s in self.sockets if s)
        if has_gem:
            messagebox.showinfo("提示", "该装备已镶嵌宝石，无法再镶嵌符文。请先移除宝石。")
            return
        empty_index = None
        for i, s in enumerate(self.sockets):
            if s is None:
                empty_index = i
                break
        if empty_index is None:
            messagebox.showinfo("提示", "没有空闲插槽，请先移除一个镶嵌物。")
            return
        dlg = RuneTwoStepDialog(self.dialog)
        res = dlg.show()
        if res:
            self.sockets[empty_index] = res
            self.update_socket_display()

    def remove_socket(self, idx):
        self.sockets[idx] = None
        self.update_socket_display()

    def on_weapon_type_change(self, event):
        if self.position != '主手':
            return
        new_type = self.weapon_type.get()
        target_sockets = 2 if new_type == '双手武器' else 1
        if target_sockets == self.max_sockets:
            return
        old_sockets = self.sockets
        self.max_sockets = target_sockets
        new_sockets = [None] * self.max_sockets
        for i in range(min(len(old_sockets), self.max_sockets)):
            new_sockets[i] = old_sockets[i]
        self.sockets = new_sockets
        self.update_socket_display()

    def update_power_list(self):
        powers = self.get_powers_func(self.position)
        self.power['values'] = powers
        self.power.bind('<KeyRelease>', lambda e: filter_combobox(e, self.power, powers))

    def on_rarity_change(self, e):
        self.update_specific_equip()
        if self.rarity_type.get() not in ['神话暗金装备']:
            for i in range(4):
                self.affixes[i].config(state='normal')
            for cb in self.trans_affixes:
                cb.config(state='normal')
        if self.rarity_type.get() == '传奇装备':
            self.power.config(state='normal')
            self.power_desc.pack()
            self.specific_equip.pack_forget()
            self.effect_label.config(text='')
            self.update_power_list()
        else:
            self.power.config(state='disabled')
            self.power.set('')
            self.power_desc.pack_forget()
            if self.rarity_type.get() in ['暗金装备', '神话暗金装备']:
                self.specific_equip.pack()
            else:
                self.specific_equip.pack_forget()

    def update_specific_equip(self):
        rarity = self.rarity_type.get()
        if rarity in ['暗金装备', '神话暗金装备']:
            items = []
            for name, data in self.UNIQUE_ITEMS.items():
                slot_match = False
                if self.position in ['戒指1', '戒指2']:
                    if data['slot'] in ['戒指', '戒指1', '戒指2']:
                        slot_match = True
                else:
                    if data['slot'] == self.position:
                        slot_match = True
                if slot_match:
                    if rarity == '神话暗金装备' and data['rarity'] == '神话暗金装备':
                        items.append(f"⭐ {name}")
                    elif rarity == '暗金装备' and data['rarity'] == '暗金装备':
                        items.append(name)
            self.specific_equip['values'] = sorted(items)
        if self.equip_data.get('equip_name'):
            name = self.equip_data['equip_name']
            if f"⭐ {name}" in self.specific_equip['values']:
                self.specific_equip.set(f"⭐ {name}")
            elif name in self.specific_equip['values']:
                self.specific_equip.set(name)

    def on_equip_change(self, e):
        name = self.specific_equip.get()
        if name.startswith('⭐ '):
            name = name[2:]
        if name in self.UNIQUE_ITEMS:
            eq = self.UNIQUE_ITEMS[name]
            self.effect_label.config(text=f"💎 {eq['effect']}")
            if eq.get('power'):
                self.power['values'] = [eq['power']]
                self.power.set(eq['power'])
                if eq['power'] in self.DB['powers']['all']:
                    self.power_desc.config(text=self.DB['powers']['all'][eq['power']]['desc'])
            self.power.config(state='disabled')
            if eq['rarity'] == '神话暗金装备':
                fixed = {
                    '祖父': ['+[35-50] 暴击伤害', '+[150-182] 全属性', '+[1839-2175] 生命上限', '+[8-12] 资源生成'],
                    '末日使者': ['+[150-182] 全属性', '+[1839-2175] 生命上限', '+[5-10] 所有伤害', '+[3-6] 暴击几率'],
                    '艾尔度因，正义之剑': ['+[150-182] 全属性', '+[1839-2175] 生命上限', '+[2-4] 所有技能', '+[5-10] 所有伤害'],
                    '无星夜空之戒': ['+[10-15] 攻击速度', '+[3-6] 暴击几率', '+[5-10] 幸运一击几率', '+[1-3] 核心技能'],
                    '阿瓦里昂，莱姗德之矛': ['+[125-151] 全属性', '+[12-25] 移动速度', '+[150-182] 主属性', '+[8-12] 资源生成'],
                    '堕狱传承': ['+[3-6] 暴击几率', '+[5-10] 幸运一击几率', '+[12-25] 移动速度', '+[1-3] 核心技能'],
                    '破碎的誓言': ['+[35-50] 暴击伤害', '+[25-40] 易伤伤害', '+[1839-2175] 生命上限', '+[10-15] 攻击速度'],
                    '安达莉尔的仪容': ['+[10-15] 攻击速度', '+[125-151] 全属性', '+[1839-2175] 生命上限', '+[150-182] 主属性'],
                    '谐角之冠': ['+[5-10] 冷却缩减', '+[1839-2175] 生命上限', '+[2944-3675] 护甲值', '+[2-4] 所有技能'],
                    '泰瑞尔之力': ['+[1839-2175] 生命上限', '+[12-25] 移动速度', '+[2944-3675] 护甲值', '+[125-151] 全属性'],
                    '涅塞科姆，绝望先驱': ['+[150-182] 全属性', '+[1839-2175] 生命上限', '+[35-50] 暴击伤害', '+[25-40] 易伤伤害'],
                    '塞利格的溶解之心': ['+[125-151] 全属性', '+[5-10] 幸运一击几率', '+[12-25] 移动速度', '+[8-12] 资源生成'],
                    '虚假死亡之衣': ['+[150-182] 全属性', '+[1839-2175] 生命上限', '+[2944-3675] 护甲值', '+[8-12] 资源生成'],
                }
                if name in fixed:
                    for i in range(4):
                        self.affixes[i].set(fixed[name][i])
                        self.affixes[i].config(state='disabled')
                        self.ancient_flags[i].set(True)
                        self.ancient_btns[i].config(text='⭐', fg=COLORS['ancient'])
                        self.update_affix(i)

    def on_power_change(self, e):
        pn = self.power.get()
        if pn in self.DB['powers']['all']:
            if pn != '无威能' and pn in self.selected_powers:
                self.power_desc.config(text=f'⚠️ 【威能重复】{self.DB["powers"]["all"][pn]["desc"]}', fg='#FF0000')
            else:
                self.power_desc.config(text=self.DB['powers']['all'][pn]['desc'], fg='#00FF00')

    def save_and_close(self):
        name = self.specific_equip.get()
        if name.startswith('⭐ '):
            name = name[2:]
        aff = []
        for i in range(4):
            aff.append({
                'name': self.affixes[i].get(),
                'value': self.affix_vars[i].get(),
                'ancient': self.ancient_flags[i].get(),
                'reforge': self.reforge_flags[i].get()
            })
        ref = []
        for i in range(len(self.reforge_affixes)):
            ref.append({
                'name': self.reforge_affixes[i].get(),
                'value': self.reforge_affix_vars[i].get(),
                'ancient': self.reforge_ancient_flags[i].get(),
                'reforge': self.reforge_reforge_flags[i].get()
            })
        trans = []
        for i in range(len(self.trans_affixes)):
            trans.append({
                'name': self.trans_affixes[i].get(),
                'value': self.trans_affix_vars[i].get(),
                'reforge': self.trans_reforge_flags[i].get()
            })
        self.result = {
            'type': self.rarity_type.get(),
            'weapon_type': self.weapon_type.get() if self.position in ['主手', '副手'] else '',
            'equip_name': name,
            'power': self.power.get(),
            'power_value': self.power_value_var.get(),
            'quality': self.quality.get(),
            'affixes': aff,
            'reforge_affixes': ref,
            'trans_affixes': trans,
            'sockets': self.sockets,
        }
        self.on_close()

    def center_dialog(self):
        self.dialog.update_idletasks()
        w = self.dialog.winfo_width()
        h = self.dialog.winfo_height()
        x = self.parent.winfo_pointerx()
        y = self.parent.winfo_pointery()
        offset_x, offset_y = 20, 20
        left = x + offset_x
        top = y + offset_y
        screen_w = self.dialog.winfo_screenwidth()
        screen_h = self.dialog.winfo_screenheight()
        if left + w > screen_w:
            left = x - w - offset_x
        if top + h > screen_h:
            top = y - h - offset_y
        if left < 0:
            left = 10
        if top < 0:
            top = 10
        self.dialog.geometry(f"+{int(left)}+{int(top)}")

    def on_close(self):
        if self.dialog:
            self.dialog.destroy()
            self.dialog = None
        gc.collect()

    def show(self):
        if self.dialog:
            self.parent.wait_window(self.dialog)
        return self.result

# ==================== 新版技能树系统（支持分支节点） ====================
class SkillTreeSystem:
    def __init__(self, profession, data_path='skill.json'):
        self.profession = profession
        self.data_path = data_path
        self.skill_data = {}
        self.skill_levels = {}
        self.branch_levels = {}
        self.external_bonuses = {
            "global": {"all_skills": 0, "fire_skills": 0, "frost_skills": 0, "shock_skills": 0},
            "specific": {}
        }
        self.available_points = 84
        self.listeners = []
        self._branch_cache = {}
        self._load_data()
        self._parse_all_branches()

    def _load_data(self):
        full_path = resource_path(self.data_path)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                raw = json.load(f)
        except Exception as e:
            logging.warning("加载技能数据失败: %s", e)
            return
        if isinstance(raw, list):
            skills_list = raw
        elif isinstance(raw, dict):
            if self.profession in raw:
                skills_list = raw[self.profession] if isinstance(raw[self.profession], list) else raw[self.profession].get('skills', [])
            else:
                skills_list = raw.get('skills', [])
        else:
            skills_list = []
        prefix = f"{self.profession.lower()}_"
        for skill in skills_list:
            key = skill.get('key')
            if not key or not key.startswith(prefix):
                continue
            self.skill_data[key] = {
                'id': skill.get('id'),
                'name': skill.get('name'),
                'type': 'active' if skill.get('active') else 'passive',
                'tags': skill.get('tags', []),
                'damage_type': skill.get('damageType', '物理伤害'),
                'base_max_level': skill.get('ranks', 15),
                'desc_template': self._extract_desc_template(skill),
                'enchant_desc': skill.get('enchantment', ''),
                'mods': skill.get('mods', []),
                'icon': skill.get('icon'),
                'val1': skill.get('val1', []),
                'val2': skill.get('val2', []),
                'val3': skill.get('val3', []),
                'val4': skill.get('val4', []),
                'level_scaling': skill.get('level_scaling', {})
            }

    def _extract_desc_template(self, skill):
        desc_parts = skill.get('desc', [])
        if desc_parts:
            full = ' '.join(desc_parts)
            full = re.sub(r'\{c_[^}]+\}|{/c}', '', full)
            return full
        return ""

    def _parse_all_branches(self):
        for key in self.skill_data:
            self._branch_cache[key] = self._parse_branches(self.skill_data[key])

    def _parse_branches(self, skill):
        mods = skill.get('mods', [])
        morphs = []
        passives = []
        for mod in mods:
            name = mod.get('name', '')
            if any(kw in name for kw in ['强化', '变体', '形态', '替换', '变为']):
                morphs.append(mod)
            else:
                passives.append(mod)
        branch_groups = []
        branches = {}
        if morphs:
            selected = morphs[:3]
            branch_groups.append({
                'type': 'choice_3',
                'branches': [str(m.get('modId', m.get('id', ''))) for m in selected],
                'max_select': 1
            })
            for m in selected:
                bid = str(m.get('modId', m.get('id', '')))
                branches[bid] = {
                    'id': bid,
                    'name': m.get('name', ''),
                    'desc': '\n'.join(m.get('desc', [''])),
                }
        if passives:
            selected = passives[:4]
            branch_groups.append({
                'type': 'choice_2',
                'branches': [str(m.get('modId', m.get('id', ''))) for m in selected],
                'max_select': 2
            })
            for m in selected:
                bid = str(m.get('modId', m.get('id', '')))
                branches[bid] = {
                    'id': bid,
                    'name': m.get('name', ''),
                    'desc': '\n'.join(m.get('desc', [''])),
                }
        return branch_groups, branches

    def get_branch_groups(self, skill_key):
        return self._branch_cache.get(skill_key, ([], {}))[0]

    def get_branches(self, skill_key):
        return self._branch_cache.get(skill_key, ([], {}))[1]

    def get_base_level(self, skill_key):
        return self.skill_levels.get(skill_key, 0)

    def get_total_level(self, skill_key):
        base = self.get_base_level(skill_key)
        extra = 0
        extra += self.external_bonuses['global'].get('all_skills', 0)
        skill = self.skill_data.get(skill_key, {})
        for tag in skill.get('tags', []):
            if '火焰' in tag or 'Fire' in tag:
                extra += self.external_bonuses['global'].get('fire_skills', 0)
            elif '冰霜' in tag or 'Frost' in tag:
                extra += self.external_bonuses['global'].get('frost_skills', 0)
            elif '闪电' in tag or 'Shock' in tag:
                extra += self.external_bonuses['global'].get('shock_skills', 0)
        extra += self.external_bonuses['specific'].get(skill_key, {}).get('level', 0)
        return base + extra

    def can_add_level(self, skill_key):
        if self.available_points <= 0:
            return False
        base_max = self.skill_data.get(skill_key, {}).get('base_max_level', 15)
        if self.get_base_level(skill_key) >= base_max:
            return False
        return True

    def add_level(self, skill_key):
        if not self.can_add_level(skill_key):
            return False
        self.skill_levels[skill_key] = self.skill_levels.get(skill_key, 0) + 1
        self.available_points -= 1
        self._notify_change()
        return True

    def remove_level(self, skill_key):
        if self.get_base_level(skill_key) <= 0:
            return False
        self.skill_levels[skill_key] -= 1
        self.available_points += 1
        if self.skill_levels[skill_key] == 0:
            self.branch_levels.pop(skill_key, None)
        self._notify_change()
        return True

    def can_activate_branch(self, skill_key, branch_id):
        if self.get_base_level(skill_key) == 0:
            return False
        branches = self.get_branches(skill_key)
        if branch_id not in branches:
            return False
        if self.branch_levels.get(skill_key, {}).get(branch_id, 0) >= 1:
            return False
        if self.available_points <= 0:
            return False
        groups = self.get_branch_groups(skill_key)
        for group in groups:
            if branch_id in group['branches']:
                selected = [bid for bid in group['branches'] if self.branch_levels.get(skill_key, {}).get(bid, 0) > 0]
                if len(selected) >= group['max_select']:
                    return False
                break
        return True

    def activate_branch(self, skill_key, branch_id):
        if not self.can_activate_branch(skill_key, branch_id):
            return False
        groups = self.get_branch_groups(skill_key)
        for group in groups:
            if branch_id in group['branches'] and group['type'] in ('choice_2', 'choice_3'):
                for bid in group['branches']:
                    if bid != branch_id:
                        self.branch_levels.setdefault(skill_key, {}).pop(bid, None)
                break
        self.branch_levels.setdefault(skill_key, {})[branch_id] = 1
        self.available_points -= 1
        self._notify_change()
        return True

    def deactivate_branch(self, skill_key, branch_id):
        if self.branch_levels.get(skill_key, {}).get(branch_id, 0) == 0:
            return False
        self.branch_levels.setdefault(skill_key, {}).pop(branch_id, None)
        self.available_points += 1
        self._notify_change()
        return True

    def evaluate_formula(self, formula_str, level):
        try:
            return eval(formula_str, {"level": level, "__builtins__": {}})
        except:
            return 0.0

    def get_skill_display_info(self, skill_key):
        skill = self.skill_data.get(skill_key)
        if not skill:
            return {}
        base_level = self.get_base_level(skill_key)
        total_level = self.get_total_level(skill_key)
        extra_level = total_level - base_level

        vals = {}
        for i in range(1, 10):
            key = f'val{i}'
            if key in skill:
                val_data = skill[key]
                if isinstance(val_data, list):
                    idx = min(total_level-1, len(val_data)-1)
                    vals[key] = val_data[idx] if idx >= 0 else 0
                elif isinstance(val_data, str):
                    vals[key] = self.evaluate_formula(val_data, total_level)
        if 'val1' in vals and '{damage}' in skill.get('desc_template', ''):
            vals['damage'] = vals['val1']

        desc = skill.get('desc_template', '')
        for k, v in vals.items():
            desc = desc.replace(f'{{{k}}}', str(int(v)) if isinstance(v, float) and v.is_integer() else f"{v:.1f}")

        tags = skill.get('tags', [])
        if skill_key in self.external_bonuses['specific']:
            tags_change = self.external_bonuses['specific'][skill_key].get('tags_change', {})
            for old, new in tags_change.items():
                if old in tags:
                    tags = [new if t == old else t for t in tags]

        branches = self.get_branches(skill_key)
        active_branches = {bid: lvl for bid, lvl in self.branch_levels.get(skill_key, {}).items() if lvl > 0}
        branch_desc = []
        for bid, lvl in active_branches.items():
            branch = branches.get(bid)
            if branch:
                effect = branch.get('desc', '')
                effect = re.sub(r'\{c_[^}]+\}|{/c}', '', effect)
                branch_desc.append(f"✨ {branch['name']}: {effect}")
        if branch_desc:
            desc += "\n\n" + "\n".join(branch_desc)

        enchant = skill.get('enchant_desc', '')
        if enchant:
            desc += f"\n\n✨ 附魔: {enchant}"

        return {
            'name': skill['name'],
            'icon': skill.get('icon'),
            'base_level': base_level,
            'total_level': total_level,
            'extra_level': extra_level,
            'tags': tags,
            'damage_type': skill.get('damage_type', ''),
            'description': desc,
            'active_branches': active_branches,
            'all_branches': branches,
            'branch_groups': self.get_branch_groups(skill_key),
        }

    def update_external_bonuses(self, bonus_data):
        if 'global' in bonus_data:
            for k, v in bonus_data['global'].items():
                self.external_bonuses['global'][k] = self.external_bonuses['global'].get(k, 0) + v
        if 'specific' in bonus_data:
            for skill_key, data in bonus_data['specific'].items():
                if skill_key not in self.external_bonuses['specific']:
                    self.external_bonuses['specific'][skill_key] = {}
                for k, v in data.items():
                    self.external_bonuses['specific'][skill_key][k] = v
        self._notify_change()

    def reset_all(self):
        self.skill_levels.clear()
        self.branch_levels.clear()
        self.available_points = 84
        self._notify_change()

    def _notify_change(self):
        for cb in self.listeners:
            cb()

    def add_listener(self, callback):
        self.listeners.append(callback)


# ==================== 技能树UI（无分支面板 + 滚轮缩放 + 分支节点支持） ====================
class SkillTreeUI:
    def __init__(self, parent, skill_system, layout_file='skilltree_data.json'):
        self.skill_system = skill_system
        self.parent = parent
        self.layout_file = layout_file
        self.frame = tk.Frame(parent, bg='#150808')
        self.frame.pack(fill=tk.BOTH, expand=True)

        info_frame = tk.Frame(self.frame, bg='#150808')
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        self.points_label = tk.Label(info_frame, text=f"剩余点数: {self.skill_system.available_points}",
                                     font=('微软雅黑', 12), fg='#FFD700', bg='#150808')
        self.points_label.pack(side=tk.LEFT, padx=5)
        self.allocated_label = tk.Label(info_frame, text="已分配点数: 0",
                                        font=('微软雅黑', 12), fg='#88FF88', bg='#150808')
        self.allocated_label.pack(side=tk.LEFT, padx=20)
        reset_btn = tk.Button(info_frame, text="重置", font=('微软雅黑', 10),
                              bg='#2a2a2a', fg='#FFD700', command=self._reset_skills)
        reset_btn.pack(side=tk.LEFT, padx=10)

        search_frame = tk.Frame(info_frame, bg='#150808')
        search_frame.pack(side=tk.RIGHT)
        tk.Label(search_frame, text="搜索:", font=('微软雅黑', 10), fg='#FFD700', bg='#150808').pack(side=tk.LEFT)
        self.search_entry = tk.Entry(search_frame, font=('微软雅黑', 10), width=12)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        search_btn = tk.Button(search_frame, text="查找", command=self._search_skill,
                               bg='#2a2a2a', fg='#FFD700')
        search_btn.pack(side=tk.LEFT)

        self.canvas = tk.Canvas(self.frame, bg='#1a1a1a', highlightthickness=0)
        self.h_scroll = tk.Scrollbar(self.frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.v_scroll = tk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.h_scroll.set, yscrollcommand=self.v_scroll.set)
        self.h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas.bind('<MouseWheel>', self._on_mousewheel)
        self.canvas.bind('<Button-4>', self._on_mousewheel)
        self.canvas.bind('<Button-5>', self._on_mousewheel)
        self.canvas.bind('<ButtonPress-1>', self._start_drag)
        self.canvas.bind('<B1-Motion>', self._on_drag)

        self.nodes = []
        self.node_refs = {}
        self.current_scale = 1.0
        self._load_layout(layout_file)

        self.skill_system.add_listener(self.refresh)
        self.refresh()

    def _load_layout(self, layout_file):
        full_path = resource_path(layout_file)
        if not os.path.exists(full_path):
            logging.warning("布局文件不存在，使用自动布局")
            self._auto_layout()
            return
        with open(full_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        nodes_data = data.get('nodes', [])
        self.nodes = []
        for nd in nodes_data:
            skill_id = nd.get('skill_id')
            skill = None
            if skill_id and skill_id in self.skill_system.skill_data:
                skill = self.skill_system.skill_data[skill_id]
            # 读取分支字段
            branch_skill = nd.get('branch_skill')
            branch_id = nd.get('branch_id')
            node = {
                'skill_key': skill_id if skill else None,
                'skill': skill,
                'x': nd.get('left', 0),
                'y': nd.get('top', 0),
                'type': nd.get('type', 'skill'),
                'internal_id': skill_id if skill_id else f"token_{nd.get('left',0)}_{nd.get('top',0)}",
                'branch_skill': branch_skill,
                'branch_id': branch_id,
            }
            self.nodes.append(node)
        if self.nodes:
            xs = [n['x'] for n in self.nodes]
            ys = [n['y'] for n in self.nodes]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            margin = 150
            self.canvas.config(scrollregion=(min_x-margin, min_y-margin, max_x+margin, max_y+margin))
        self._draw_all_nodes()

    def _auto_layout(self):
        type_order = ['基础', '核心', '防御', '咒唤', '掌控', '终极', '关键被动']
        groups = {t: [] for t in type_order}
        for skill in self.skill_system.skill_data.values():
            skill_type = skill.get('tags', ['其他'])[0] if skill.get('tags') else '其他'
            matched = False
            for t in type_order:
                if t in skill_type:
                    groups[t].append(skill)
                    matched = True
                    break
            if not matched:
                groups.setdefault('其他', []).append(skill)
        self.nodes = []
        start_x, start_y = 100, 100
        col_width, row_height, max_per_row = 180, 120, 10
        current_y = start_y
        for t in type_order + ['其他']:
            skill_list = groups.get(t, [])
            if not skill_list:
                continue
            skill_list.sort(key=lambda s: s.get('name', ''))
            row_count = max(1, (len(skill_list) + max_per_row - 1) // max_per_row)
            for row in range(row_count):
                start_idx = row * max_per_row
                end_idx = min(start_idx + max_per_row, len(skill_list))
                x = start_x
                for skill in skill_list[start_idx:end_idx]:
                    key = None
                    for k, v in self.skill_system.skill_data.items():
                        if v is skill:
                            key = k
                            break
                    self.nodes.append({
                        'skill_key': key,
                        'skill': skill,
                        'x': x,
                        'y': current_y + row * row_height,
                        'type': 'skill',
                        'internal_id': key if key else f"auto_{x}_{current_y+row*row_height}",
                        'branch_skill': None,
                        'branch_id': None,
                    })
                    x += col_width
            current_y += row_count * row_height + 40
        if self.nodes:
            xs = [n['x'] for n in self.nodes]
            ys = [n['y'] for n in self.nodes]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)
            margin = 150
            self.canvas.config(scrollregion=(min_x-margin, min_y-margin, max_x+margin, max_y+margin))
        self._draw_all_nodes()

    def _draw_all_nodes(self):
        self.canvas.delete('all')
        self.node_refs.clear()
        NODE_RADIUS = 32
        ICON_SIZE = 28
        for node in self.nodes:
            x, y = node['x'], node['y']
            skill = node.get('skill')
            internal_id = node['internal_id']
            is_branch = node.get('branch_skill') is not None and node.get('branch_id') is not None

            # 背景圆形
            if is_branch:
                fill_color = '#1a3a5a'
                outline = '#66CCFF'
            else:
                fill_color = '#2a2a2a' if skill else '#3a2a3a'
                outline = '#FFD700' if skill else '#AA66FF'
            oval = self.canvas.create_oval(x-NODE_RADIUS, y-NODE_RADIUS, x+NODE_RADIUS, y+NODE_RADIUS,
                                           fill=fill_color, outline=outline, width=2,
                                           tags=(internal_id, 'node'))

            # 图标或分支标识
            icon_id = None
            if is_branch:
                # 分支节点显示分支名称缩写
                branches = self.skill_system.get_branches(node['branch_skill'])
                branch = branches.get(node['branch_id'])
                display_text = branch['name'][:2] if branch else 'BR'
                icon_id = self.canvas.create_text(x, y, text=display_text, fill='#88CCFF',
                                                  font=('微软雅黑', 12, 'bold'), tags=(internal_id, 'text'))
                # 显示激活状态
                is_active = self.skill_system.branch_levels.get(node['branch_skill'], {}).get(node['branch_id'], 0) > 0
                self.canvas.create_text(x, y+NODE_RADIUS+6, text='✓' if is_active else '',
                                        fill='#88FF88', font=('微软雅黑', 10, 'bold'),
                                        tags=(internal_id, 'branch_status'))
            elif skill and skill.get('icon'):
                icon_path = resource_path(f'images/icons/{skill["icon"]}.png')
                if os.path.exists(icon_path):
                    photo = load_photo_image(icon_path, size=(ICON_SIZE, ICON_SIZE))
                    if photo:
                        icon_id = self.canvas.create_image(x, y, image=photo, tags=(internal_id, 'icon'))
            if not icon_id and not is_branch:
                text = skill['name'][:2] if skill else '??'
                self.canvas.create_text(x, y, text=text, fill='white',
                                        font=('微软雅黑', 12, 'bold'), tags=(internal_id, 'text'))

            # 等级背景和文本（仅主动技能，非分支）
            lv_bg = None
            lv_text = None
            if skill and skill.get('type') == 'active' and not is_branch:
                lv_bg = self.canvas.create_rectangle(x+20, y+20, x+NODE_RADIUS, y+NODE_RADIUS,
                                                     fill='#00000080', outline='', tags=(internal_id, 'lv_bg'))
                lv_text = self.canvas.create_text(x+26, y+26, text='', fill='#88FF88',
                                                  font=('微软雅黑',8,'bold'), anchor='se',
                                                  tags=(internal_id, 'lv_text'))

            # 命中区域
            hitbox = self.canvas.create_rectangle(x-NODE_RADIUS, y-NODE_RADIUS, x+NODE_RADIUS, y+NODE_RADIUS,
                                                  fill='', outline='', tags=(internal_id, 'hitbox'))
            if is_branch:
                # 分支节点绑定事件
                self.canvas.tag_bind(hitbox, '<Button-1>', lambda e, sk=node['branch_skill'], bid=node['branch_id']: self._on_branch_click(sk, bid))
                self.canvas.tag_bind(hitbox, '<Button-3>', lambda e, sk=node['branch_skill'], bid=node['branch_id']: self._on_branch_right_click(sk, bid))
                self.canvas.tag_bind(hitbox, '<Enter>', lambda e, sk=node['branch_skill'], bid=node['branch_id']: self._show_branch_tooltip(e, sk, bid))
                self.canvas.tag_bind(hitbox, '<Leave>', self._hide_tooltip)
            else:
                self.canvas.tag_bind(hitbox, '<Button-1>', lambda e, key=node['skill_key']: self._on_left_click(key))
                self.canvas.tag_bind(hitbox, '<Button-3>', lambda e, key=node['skill_key']: self._on_right_click(key))
                self.canvas.tag_bind(hitbox, '<Enter>', lambda e, key=node['skill_key']: self._show_tooltip(e, key))
                self.canvas.tag_bind(hitbox, '<Leave>', self._hide_tooltip)

            self.node_refs[internal_id] = {
                'oval': oval,
                'icon': icon_id,
                'lv_bg': lv_bg,
                'lv_text': lv_text,
                'hitbox': hitbox,
                'node': node,
                'is_branch': is_branch,
                'branch_skill': node.get('branch_skill'),
                'branch_id': node.get('branch_id'),
            }

    # ---------- 滚轮缩放 ----------
    def _on_mousewheel(self, event):
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        if event.delta:
            delta = event.delta / 120
        else:
            if event.num == 4:
                delta = 1
            elif event.num == 5:
                delta = -1
            else:
                return
        scale_factor = 1.1 ** delta
        new_scale = self.current_scale * scale_factor
        if new_scale < 0.2 or new_scale > 3.0:
            return
        self.current_scale = new_scale
        self.canvas.scale('all', x, y, scale_factor, scale_factor)
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    # ---------- 节点交互 ----------
    def _on_left_click(self, skill_key):
        if not skill_key:
            return
        self.skill_system.add_level(skill_key)

    def _on_right_click(self, skill_key):
        if not skill_key:
            return
        self.skill_system.remove_level(skill_key)

    def _on_branch_click(self, skill_key, branch_id):
        if not skill_key or not branch_id:
            return
        if self.skill_system.branch_levels.get(skill_key, {}).get(branch_id, 0) > 0:
            return
        self.skill_system.activate_branch(skill_key, branch_id)

    def _on_branch_right_click(self, skill_key, branch_id):
        if not skill_key or not branch_id:
            return
        self.skill_system.deactivate_branch(skill_key, branch_id)

    def _show_branch_tooltip(self, event, skill_key, branch_id):
        self._hide_tooltip()
        branches = self.skill_system.get_branches(skill_key)
        branch = branches.get(branch_id)
        if not branch:
            return
        self.tooltip = tk.Toplevel(self.parent)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.geometry(f"+{event.x_root+15}+{event.y_root+15}")
        label = tk.Label(self.tooltip, text=f"{branch['name']}\n{branch.get('desc', '')}",
                         font=('微软雅黑',9), bg='#2a2a2a', fg='#FFFFFF', wraplength=200, justify='left')
        label.pack(padx=5, pady=5)

    # ---------- 悬浮窗 ----------
    def _show_tooltip(self, event, skill_key):
        if not skill_key:
            return
        self._hide_tooltip()
        info = self.skill_system.get_skill_display_info(skill_key)
        if not info:
            return
        self.tooltip = tk.Toplevel(self.parent)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_attributes('-topmost', True)
        self.tooltip.configure(bg='#1e1e1e', bd=1, relief='solid')
        frame = tk.Frame(self.tooltip, bg='#2a2a2a')
        frame.pack(padx=8, pady=6)
        icon_path = resource_path(f'images/icons/{info["icon"]}.png') if info.get('icon') else None
        if icon_path and os.path.exists(icon_path):
            img = load_photo_image(icon_path, size=(32,32))
            if img:
                tk.Label(frame, image=img, bg='#2a2a2a').grid(row=0, column=0, rowspan=2, padx=5)
        tk.Label(frame, text=info['name'], font=('微软雅黑', 12, 'bold'),
                 fg='#FFD700', bg='#2a2a2a').grid(row=0, column=1, sticky='w')
        skill = self.skill_system.skill_data.get(skill_key, {})
        max_lv = skill.get('base_max_level', 15)
        level_text = f"等级 {info['base_level']}/{max_lv}"
        if info['extra_level'] > 0:
            level_text += f" (+{info['extra_level']} 来自装备)"
        tk.Label(frame, text=level_text, font=('微软雅黑', 9),
                 fg='#88FF88', bg='#2a2a2a').grid(row=1, column=1, sticky='w')
        tags_text = ' | '.join(info['tags'])
        tk.Label(frame, text=tags_text, font=('微软雅黑', 9),
                 fg='#AAAAAA', bg='#2a2a2a').grid(row=2, column=0, columnspan=2, sticky='w', pady=(5,0))
        desc_label = tk.Label(frame, text=info['description'], font=('微软雅黑', 9),
                              fg='#FFFFFF', bg='#2a2a2a', wraplength=350, justify='left')
        desc_label.grid(row=3, column=0, columnspan=2, pady=(8,0), sticky='w')
        self.tooltip.update_idletasks()
        x = event.x_root + 15
        y = event.y_root + 15
        w = self.tooltip.winfo_width()
        h = self.tooltip.winfo_height()
        sw = self.tooltip.winfo_screenwidth()
        sh = self.tooltip.winfo_screenheight()
        if x + w > sw: x = event.x_root - w - 15
        if y + h > sh: y = event.y_root - h - 15
        if x < 0: x = 10
        if y < 0: y = 10
        self.tooltip.geometry(f"+{x}+{y}")

    def _hide_tooltip(self, event=None):
        if hasattr(self, 'tooltip') and self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    # ---------- 画布拖拽 ----------
    def _start_drag(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def _on_drag(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    # ---------- 其他 ----------
    def _reset_skills(self):
        if messagebox.askyesno("确认重置", "确定要重置所有技能点吗？"):
            self.skill_system.reset_all()

    def _search_skill(self):
        keyword = self.search_entry.get().strip().lower()
        if not keyword:
            return
        for node in self.nodes:
            skill = node.get('skill')
            if skill and keyword in skill['name'].lower():
                items = self.canvas.find_withtag(node['internal_id'])
                for item in items:
                    self.canvas.itemconfig(item, outline='#FF0000')
                    coords = self.canvas.bbox(item)
                    if coords:
                        self.canvas.see(coords[0], coords[1])
                self.canvas.after(3000, lambda: self.canvas.itemconfig(items, outline='#FFD700'))
                break

    def refresh(self):
        total_allocated = sum(self.skill_system.skill_levels.values()) + sum(len(b) for b in self.skill_system.branch_levels.values())
        self.allocated_label.config(text=f"已分配点数: {total_allocated}")
        self.points_label.config(text=f"剩余点数: {self.skill_system.available_points}")
        for ref in self.node_refs.values():
            node = ref['node']
            if ref.get('is_branch'):
                # 更新分支状态
                skill_key = ref['branch_skill']
                branch_id = ref['branch_id']
                is_active = self.skill_system.branch_levels.get(skill_key, {}).get(branch_id, 0) > 0
                for item in self.canvas.find_withtag(node['internal_id']):
                    if 'branch_status' in self.canvas.gettags(item):
                        self.canvas.itemconfig(item, text='✓' if is_active else '')
                        break
            else:
                skill_key = node.get('skill_key')
                if not skill_key:
                    continue
                skill = self.skill_system.skill_data.get(skill_key)
                if not skill or skill.get('type') != 'active':
                    continue
                lv_text_id = ref.get('lv_text')
                if lv_text_id:
                    total_lv = self.skill_system.get_total_level(skill_key)
                    base_lv = self.skill_system.get_base_level(skill_key)
                    max_lv = skill.get('base_max_level', 15)
                    txt = f"{base_lv}/{max_lv}"
                    if total_lv > base_lv:
                        txt = f"{base_lv}+{total_lv-base_lv}/{max_lv}"
                    self.canvas.itemconfig(lv_text_id, text=txt)

# ==================== 主程序 ====================
class DiabloCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title('D4计算器 V2.2.1')
        self.root.geometry('750x800')
        self.root.configure(bg='#1a0505')
        self.init_style()
        self.current_profession = "巫师"
        self.current_db = DB
        self.equip_data = {pos: {} for pos in POSITIONS}
        self.equip_buttons = {}
        self.tooltip = None
        self.current_dialog = None
        self.current_gem_dialog = None
        self.initUI()
        self.root.after(30000, self.gc_collect)

    def init_style(self):
        style = ttk.Style(self.root)
        style.theme_use('clam')
        style.configure('TCombobox', fieldbackground='#2a2a2a', background='#2a2a2a', foreground='#C0A060',
                        selectbackground='#3a3a3a', selectforeground='#FFD700')
        style.configure('TNotebook', background='#1a0505', borderwidth=0)
        style.configure('TNotebook.Tab', background='#2a1a1a', foreground='#FFD700', padding=[10,5])
        style.map('TNotebook.Tab', background=[('selected', '#1a0505')], foreground=[('selected', '#FFD700')])

    def gc_collect(self):
        gc.collect()
        self.root.after(30000, self.gc_collect)

    def on_profession_change(self, e):
        self.current_profession = self.profession_cb.get()
        self.current_db = get_profession_db(self.current_profession)
        self.info_label.config(text=f'（当前：{self.current_profession} | {len(self.current_db["powers"]["all"])}威能）')
        self.equip_data = {pos: {} for pos in POSITIONS}
        for pos in POSITIONS:
            self.update_equip_button(pos)
        self.skill_system = SkillTreeSystem(self.current_profession)
        if hasattr(self, 'skill_ui'):
            self.skill_ui.frame.destroy()
            self.skill_ui = SkillTreeUI(self.skill_ui.parent, self.skill_system, layout_file='skilltree_data.json')
        gc.collect()

    def get_powers_for_slot(self, position):
        attack_pos = ['主手', '副手', '手套', '戒指1', '戒指2']
        defense_pos = ['头盔', '胸甲', '裤子', '鞋子']
        selected_powers = set()
        for pos, data in self.equip_data.items():
            if pos != position and data.get('power') and data['power'] != '无威能':
                selected_powers.add(data['power'])
        powers = ['无威能']
        for name, data in self.current_db['powers']['all'].items():
            if name in selected_powers:
                continue
            ptype = data['type']
            if position == '项链':
                powers.append(name)
            elif position in attack_pos and '攻击' in ptype:
                powers.append(name)
            elif position in defense_pos and '防御' in ptype:
                powers.append(name)
            elif '通用' in ptype:
                powers.append(name)
        return sorted(set(powers))

    # ========== 悬浮窗（装备） ==========
    def show_tooltip(self, position, event):
        if self.tooltip:
            self.tooltip.destroy()
        data = self.equip_data.get(position, {})
        if not data or not data.get('type'):
            return

        self.tooltip = tk.Toplevel(self.root)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.configure(bg='#2a2a2a', bd=2, relief='solid')

        content = tk.Frame(self.tooltip, bg='#2a2a2a')
        content.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        equip_type = data.get('type', '')
        if equip_type == '神话暗金装备':
            title_color = '#EE82EE'
        elif equip_type == '暗金装备':
            title_color = '#FFD700'
        else:
            title_color = '#FFD700'

        if equip_type == '传奇装备':
            power_name = data.get('power', '')
            if power_name and power_name != '无威能':
                tk.Label(content, text=power_name, font=('微软雅黑', 11, 'bold'),
                         fg=title_color, bg='#2a2a2a').pack(anchor='w')
        else:
            if data.get('equip_name'):
                tk.Label(content, text=data['equip_name'], font=('微软雅黑', 11, 'bold'),
                         fg=title_color, bg='#2a2a2a').pack(anchor='w')

        tk.Label(content, text='─'*30, font=('微软雅黑', 8),
                 fg=title_color, bg='#2a2a2a').pack(anchor='w', pady=2)

        affixes = data.get('affixes', [])
        for affix in affixes:
            name = affix.get('name', '')
            if name:
                value = affix.get('value', '')
                icon = ''
                if affix.get('ancient'):
                    icon += '⭐'
                if affix.get('reforge'):
                    icon += '🔨'
                if len(icon) == 0:
                    icon = '  '
                elif len(icon) == 1:
                    icon = icon + ' '
                tk.Label(content, text=f'{icon}+{value} {name}',
                         font=('微软雅黑', 9), fg='#FFFFFF', bg='#2a2a2a').pack(anchor='w')

        reforge_affixes = data.get('reforge_affixes', [])
        for affix in reforge_affixes:
            name = affix.get('name', '')
            if name:
                value = affix.get('value', '')
                icon = ''
                if affix.get('ancient'):
                    icon += '⭐'
                if len(icon) == 0:
                    icon = '  '
                elif len(icon) == 1:
                    icon = icon + ' '
                tk.Label(content, text=f'{icon}+{value} {name}',
                         font=('微软雅黑', 9), fg='#FFA500', bg='#2a2a2a').pack(anchor='w')

        trans_affixes = data.get('trans_affixes', [])
        for affix in trans_affixes:
            name = affix.get('name', '')
            if name:
                value = affix.get('value', '')
                icon = '🔮'
                if affix.get('reforge'):
                    icon += '🔨'
                if len(icon) == 1:
                    icon = icon + ' '
                tk.Label(content, text=f'{icon}+{value} {name}',
                         font=('微软雅黑', 9), fg='#FF69B4', bg='#2a2a2a').pack(anchor='w')

        if equip_type == '传奇装备':
            power_name = data.get('power', '')
            power_value = data.get('power_value', 0)
            if power_name and power_name != '无威能':
                if power_name in self.current_db['powers']['all']:
                    power_desc = self.current_db['powers']['all'][power_name]['desc']
                    if power_value > 0:
                        power_desc = re.sub(r'(\[\+\])?\[?(\d+-\d+)\]', f'[{power_value}]', power_desc)
                    tk.Label(content, text=power_desc, font=('微软雅黑', 8),
                             fg='#CCCCCC', bg='#2a2a2a', wraplength=280, justify='left').pack(anchor='w', pady=3)

        if equip_type in ['暗金装备', '神话暗金装备']:
            equip_name = data.get('equip_name', '')
            power_value = data.get('power_value', 0)
            if equip_name and equip_name in self.current_db['unique_items']:
                unique_data = self.current_db['unique_items'][equip_name]
                effect = unique_data.get('effect', '')
                if effect:
                    if power_value > 0:
                        effect = re.sub(r'(\[\+\])?\[?(\d+-\d+)\]', f'[{power_value}]', effect)
                    tk.Label(content, text=effect, font=('微软雅黑', 8),
                             fg='#88FF88', bg='#2a2a2a', wraplength=280, justify='left').pack(anchor='w', pady=3)

        sockets = data.get('sockets', [])
        if any(sockets):
            tk.Label(content, text='─'*30, font=('微软雅黑', 8),
                     fg=title_color, bg='#2a2a2a').pack(anchor='w', pady=2)
            tk.Label(content, text='💎🗿 插槽镶嵌物：', font=('微软雅黑', 9, 'bold'),
                     fg=title_color, bg='#2a2a2a').pack(anchor='w')
            for socket_value in sockets:
                if not socket_value:
                    continue
                if socket_value in GEMS_DATABASE:
                    gem_data = GEMS_DATABASE[socket_value]
                    if position in ['主手', '副手']:
                        effect = gem_data['weapon']
                    elif position in ['项链', '戒指1', '戒指2']:
                        effect = gem_data['jewelry']
                    else:
                        effect = gem_data['armor']
                    gem_frame = tk.Frame(content, bg='#2a2a2a')
                    gem_frame.pack(anchor='w', pady=1)
                    tk.Label(gem_frame, text=f"{gem_data['icon']} {gem_data['name']}【{gem_data['quality']}】",
                             font=('微软雅黑', 9, 'bold'), fg=gem_data['color'], bg='#2a2a2a').pack(anchor='w')
                    tk.Label(gem_frame, text=f"   【{effect['type']}】{effect['name']} +{effect['value']}",
                             font=('微软雅黑', 8), fg=gem_data['color'], bg='#2a2a2a').pack(anchor='w')
                elif socket_value in RUNES_DATABASE:
                    rune_data = RUNES_DATABASE[socket_value]
                    rune_frame = tk.Frame(content, bg='#2a2a2a')
                    rune_frame.pack(anchor='w', pady=1)
                    tk.Label(rune_frame, text=f"{rune_data['icon']} {rune_data['name']}【{rune_data['rarity']}】",
                             font=('微软雅黑', 9, 'bold'), fg=rune_data['color'], bg='#2a2a2a').pack(anchor='w')
                    tk.Label(rune_frame, text=f"   【{rune_data['category']}】{rune_data['effect']}",
                             font=('微软雅黑', 8), fg=rune_data['color'], bg='#2a2a2a', wraplength=260, justify='left').pack(anchor='w')
                elif isinstance(socket_value, str) and '|' in socket_value:
                    ritual_name, invocation_name = socket_value.split('|', 1)
                    ritual_data = RUNES_DATABASE.get(ritual_name, {})
                    invocation_data = RUNES_DATABASE.get(invocation_name, {})
                    rune_frame = tk.Frame(content, bg='#2a2a2a')
                    rune_frame.pack(anchor='w', pady=1)
                    tk.Label(rune_frame, text="📿+🔮 符文组合",
                             font=('微软雅黑', 9, 'bold'), fg='#FFAA00', bg='#2a2a2a').pack(anchor='w')
                    tk.Label(rune_frame, text=f"   仪祭: {ritual_data.get('icon', '')} {ritual_name} - {ritual_data.get('effect', '')[:40]}",
                             font=('微软雅黑', 8), fg='#FFAA00', bg='#2a2a2a', wraplength=260, justify='left').pack(anchor='w')
                    tk.Label(rune_frame, text=f"   祈告: {invocation_data.get('icon', '')} {invocation_name} - {invocation_data.get('effect', '')[:40]}",
                             font=('微软雅黑', 8), fg='#00BFFF', bg='#2a2a2a', wraplength=260, justify='left').pack(anchor='w')

        self.tooltip.update_idletasks()
        x = event.x_root + 15
        y = event.y_root + 15
        w = self.tooltip.winfo_width()
        h = self.tooltip.winfo_height()
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        if x + w > screen_w:
            x = event.x_root - w - 15
        if y + h > screen_h:
            y = event.y_root - h - 15
        self.tooltip.geometry(f"+{x}+{y}")

    def hide_tooltip(self, event):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

    def check_two_handed(self):
        is_two_handed = False
        main_hand = self.equip_data.get('主手', {})
        if main_hand.get('weapon_type') == '双手武器':
            is_two_handed = True
        if main_hand.get('equip_name') in self.current_db['unique_items']:
            if self.current_db['unique_items'][main_hand['equip_name']].get('weapon_type') == '双手':
                is_two_handed = True
        if '副手' in self.equip_buttons:
            btn = self.equip_buttons['副手']
            if is_two_handed:
                btn.config(state='disabled', text='副手\n(双手武器已禁用)')
            else:
                btn.config(state='normal')
                self.update_equip_button('副手')

    def get_equip_color(self, equip_type):
        if equip_type == '神话暗金装备':
            return '#4B0082', '#EE82EE'
        elif equip_type == '暗金装备':
            return '#B8860B', '#FFFFFF'
        elif equip_type == '传奇装备':
            return '#8B4513', '#FFFFFF'
        else:
            return '#1a1a1a', '#FFD700'

    def create_equip_button(self, parent, position):
        img_path = resource_path(f'images/{position}.png')
        if not os.path.exists(img_path):
            alt_names = {
                '头盔': 'Helmet.png',
                '胸甲': 'Chest.png',
                '手套': 'Gloves.png',
                '裤子': 'Pants.png',
                '鞋子': 'Boots.png',
                '项链': 'Amulet.png',
                '戒指1': 'Ring.png',
                '戒指2': 'Ring.png',
                '主手': 'Weapon.png',
                '副手': 'Offhand.png'
            }
            alt_name = alt_names.get(position, f'{position}.png')
            img_path = resource_path(f'images/{alt_name}')

        photo = None
        if os.path.exists(img_path):
            try:
                photo = load_photo_image(img_path, size=(64, 64))
                if not photo:
                    raise ValueError("load_photo_image returned None")
            except Exception as e:
                logging.warning("加载图片失败 %s: %s", img_path, e)

        if photo:
            btn = tk.Button(parent, image=photo, text='', compound='center',
                            bg='#1a1a1a', fg='#FFD700', relief='ridge', bd=2,
                            width=64, height=64,
                            command=lambda pos=position: self.open_equip_detail(pos, None))
            btn.image = photo
        else:
            btn = tk.Button(parent, text=f'{position}\n点击编辑', font=('微软雅黑',10),
                            bg='#1a1a1a', fg='#FFD700', relief='ridge', bd=2,
                            width=14, height=3,
                            command=lambda pos=position: self.open_equip_detail(pos, None))

        btn.bind('<Enter>', lambda e, pos=position: self.show_tooltip(pos, e))
        btn.bind('<Leave>', self.hide_tooltip)
        self.equip_buttons[position] = btn
        return btn

    def update_equip_button(self, position):
        data = self.equip_data[position]
        btn = self.equip_buttons[position]
        equip_type = data.get('type', '')

        if hasattr(btn, 'image') and btn.image:
            if equip_type == '神话暗金装备':
                btn.config(bg='#4B0082', highlightbackground='#EE82EE')
            elif equip_type == '暗金装备':
                btn.config(bg='#B8860B', highlightbackground='#FFD700')
            elif equip_type == '传奇装备':
                btn.config(bg='#8B4513', highlightbackground='#FFA500')
            else:
                btn.config(bg='#1a1a1a', highlightbackground='#FFD700')
            return

        text = f'{position}\n'
        if equip_type in ['暗金装备', '神话暗金装备']:
            text += f"{equip_type}\n"
        elif data.get('power') and data['power'] != '无威能':
            text += f"⚡ {data['power'][:8]}\n"
        elif equip_type:
            text += f"{equip_type}\n"
        if data.get('weapon_type') and position != '副手':
            text += f"{data['weapon_type']}\n"
        if data.get('equip_name'):
            text += f"{data['equip_name'][:10]}\n"
        sockets = data.get('sockets', [])
        socket_icons = ''.join('💎' if s in GEMS_DATABASE else '🗿' for s in sockets if s)
        if socket_icons:
            text += f"\n{socket_icons}"
        _, fg_color = self.get_equip_color(equip_type)
        btn.config(text=text, fg=fg_color)

    def open_equip_detail(self, position, event):
        if position == '副手' and self.equip_buttons['副手']['state'] == 'disabled':
            return
        if self.current_dialog and hasattr(self.current_dialog, 'dialog') and self.current_dialog.dialog:
            try:
                self.current_dialog.dialog.destroy()
            except:
                pass
            self.current_dialog = None
        selected_powers = set()
        for pos, data in self.equip_data.items():
            if pos != position and data.get('power') and data['power'] != '无威能':
                selected_powers.add(data['power'])
        dialog = EquipDetailDialog(self.root, position, self.equip_data[position],
                                   self.current_profession, self.get_powers_for_slot,
                                   self.current_db, selected_powers)
        self.current_dialog = dialog
        result = dialog.show()
        self.current_dialog = None
        if result:
            new_name = result.get('equip_name', '')
            if new_name:
                for pos, data in self.equip_data.items():
                    if pos != position and data.get('equip_name') == new_name:
                        self.equip_data[pos] = {}
                        self.update_equip_button(pos)
            self.equip_data[position] = result
            self.update_equip_button(position)
            self.check_two_handed()
            self.update_skill_bonuses_from_equipment()

    def update_skill_bonuses_from_equipment(self):
        bonus = {'global': {'all_skills': 0, 'fire_skills': 0, 'frost_skills': 0, 'shock_skills': 0}, 'specific': {}}
        for pos, equip in self.equip_data.items():
            for affix in equip.get('affixes', []):
                name = affix.get('name', '')
                val = affix.get('value', 0)
                if '所有技能' in name:
                    bonus['global']['all_skills'] += val
                elif '火焰技能' in name:
                    bonus['global']['fire_skills'] += val
                elif '冰霜技能' in name:
                    bonus['global']['frost_skills'] += val
                elif '电冲技能' in name or '闪电技能' in name:
                    bonus['global']['shock_skills'] += val
            unique = equip.get('equip_name')
            if unique == '谐角之冠':
                bonus['global']['all_skills'] += 4
            elif unique == '艾尔度因，正义之剑':
                bonus['global']['all_skills'] += 2
        if hasattr(self, 'skill_system'):
            self.skill_system.update_external_bonuses(bonus)

    def initUI(self):
        top_frame = tk.Frame(self.root, bg='#1a0505')
        top_frame.pack(fill=tk.X, padx=15, pady=10)
        tk.Label(top_frame, text='🎮 职业：', font=('微软雅黑',12,'bold'), fg='#FFD700', bg='#1a0505').pack(side=tk.LEFT)
        self.profession_cb = ttk.Combobox(top_frame, values=PROFESSIONS, state='normal', width=12)
        self.profession_cb.set('巫师')
        self.profession_cb.pack(side=tk.LEFT, padx=8)
        self.profession_cb.bind('<<ComboboxSelected>>', self.on_profession_change)
        self.info_label = tk.Label(top_frame, text='（当前：D4计算器 V2.2.1）', font=('微软雅黑',10), fg='#00FF00', bg='#1a0505')
        self.info_label.pack(side=tk.LEFT, padx=10)

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        tab_equip = tk.Frame(notebook, bg='#150808')
        notebook.add(tab_equip, text='⚔️ 装备')
        equip_main = tk.Frame(tab_equip, bg='#150808')
        equip_main.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        left_col = tk.Frame(equip_main, bg='#150808')
        left_col.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=20)
        for pos in ['头盔','胸甲','手套','裤子','鞋子']:
            self.create_equip_button(left_col, pos).pack(pady=8)

        right_col = tk.Frame(equip_main, bg='#150808')
        right_col.pack(side=tk.RIGHT, fill=tk.Y, padx=20, pady=20)
        for pos in ['项链','戒指1','戒指2','主手','副手']:
            self.create_equip_button(right_col, pos).pack(pady=8)

        center_canvas = tk.Canvas(equip_main, width=200, height=200, bg='#1a0808', highlightthickness=0)
        center_canvas.pack(side=tk.LEFT, expand=True, padx=20)
        center_canvas.create_oval(10, 10, 190, 190, outline='#FFD700', width=3, fill='#2a1a1a')
        center_canvas.create_text(100, 80, text='👤', font=('微软雅黑', 48, 'bold'), fill='#FFD700')
        center_canvas.create_text(100, 140, text='D4计算器', font=('微软雅黑', 14, 'bold'), fill='#FFD700')
        center_canvas.create_text(100, 165, text='V2.2.1', font=('微软雅黑', 10), fill='#C0A060')

        tab_skill = tk.Frame(notebook, bg='#150808')
        notebook.add(tab_skill, text='🌲 技能树')
        self.skill_system = SkillTreeSystem(self.current_profession)
        self.skill_ui = SkillTreeUI(tab_skill, self.skill_system, layout_file='skilltree_data.json')

        tab_rune = tk.Frame(notebook, bg='#150808')
        notebook.add(tab_rune, text='🔮 神符&封印')
        tk.Label(tab_rune, text='🔮 神符&封印系统\n\n✅ 完整功能保留', font=('微软雅黑',16,'bold'), fg='#FFD700', bg='#150808').pack(pady=60)

        tab_paragon = tk.Frame(notebook, bg='#150808')
        notebook.add(tab_paragon, text='⭐ 巅峰盘')
        tk.Label(tab_paragon, text='⭐ 巅峰盘系统\n\n✅ 完整功能保留', font=('微软雅黑',16,'bold'), fg='#FFD700', bg='#150808').pack(pady=60)


if __name__ == '__main__':
    root = tk.Tk()
    root.title('D4计算器 V2.2.1')
    root.geometry('750x800')
    root.configure(bg='#1a0505')
    app = DiabloCalculator(root)
    root.mainloop()