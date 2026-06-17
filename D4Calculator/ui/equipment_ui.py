# -*- coding: utf-8 -*-
# 模块: ui/equipment_ui

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

from business.equipment import get_affixes_for_position, calculate_affix_value, get_reforge_affixes_for_position
from config import SOCKETS_BY_POSITION, COLORS, WEAPON_TYPES
from data.loader import RUNES_DATABASE, GEMS_DATABASE, AFFIX_VALUES
from ui.widgets import filter_combobox

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

