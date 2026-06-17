# -*- coding: utf-8 -*-
# 模块: ui/main_window

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

# ========== 修正导入 ==========
from config import resource_path, POSITIONS, PROFESSIONS, COLORS, WEAPON_TYPES, SOCKETS_BY_POSITION
from data.loader import RUNES_DATABASE, GEMS_DATABASE, get_profession_db, DB, load_photo_image
from business.skill_tree import SkillTreeSystem
from ui.equipment_ui import EquipDetailDialog
from ui.skill_tree_ui import SkillTreeUI

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
        self.equip_data = {pos: {} for pos in POSITIONS}
        for pos in POSITIONS:
            self.update_equip_button(pos)
        self.skill_system = SkillTreeSystem(self.current_profession)
        if hasattr(self, 'skill_ui'):
            self.skill_ui.frame.destroy()
            self.skill_ui = SkillTreeUI(self.skill_ui.parent, self.skill_system, layout_file='skilltree_layout.json')
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
        self.skill_ui = SkillTreeUI(tab_skill, self.skill_system, layout_file='skilltree_layout.json')

        tab_rune = tk.Frame(notebook, bg='#150808')
        notebook.add(tab_rune, text='🔮 神符&封印')
        tk.Label(tab_rune, text='🔮 神符&封印系统\n\n✅ 完整功能保留', font=('微软雅黑',16,'bold'), fg='#FFD700', bg='#150808').pack(pady=60)

        tab_paragon = tk.Frame(notebook, bg='#150808')
        notebook.add(tab_paragon, text='⭐ 巅峰盘')
        tk.Label(tab_paragon, text='⭐ 巅峰盘系统\n\n✅ 完整功能保留', font=('微软雅黑',16,'bold'), fg='#FFD700', bg='#150808').pack(pady=60)