# -*- coding: utf-8 -*-
# 模块: ui/talisman_ui_tk.py
# 护身符系统UI - tkinter实现（暗黑核风格）

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Optional

from business.talisman import TalismanSystem, SocketedRune


class TalismanUI(tk.Frame):
    def __init__(self, parent, skill_system=None, callback=None, **kwargs):
        bg = kwargs.pop('bg', '#150808')
        super().__init__(parent, bg=bg, **kwargs)

        self.skill_system = skill_system
        self.parent_callback = callback

        self.talisman_system = TalismanSystem(
            skill_system=skill_system,
            callback=self._on_data_changed
        )

        self._selected_seal_id = None
        self._socket_buttons = []
        self._tooltip = None

        self._setup_ui()
        self._refresh_all()

    def _setup_ui(self):
        main_frame = tk.Frame(self, bg='#150808')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        header_frame = tk.Frame(main_frame, bg='#150808')
        header_frame.pack(fill=tk.X, pady=(0, 12))
        tk.Label(header_frame, text='🔹 护身符系统', font=('微软雅黑', 18, 'bold'), fg='#d4af37', bg='#150808').pack(side=tk.LEFT)
        self.class_label = tk.Label(header_frame, text='当前配装: 未选择', font=('微软雅黑', 11), fg='#888888', bg='#150808')
        self.class_label.pack(side=tk.RIGHT, padx=(0, 10))
        reset_btn = tk.Button(header_frame, text='🔄 重置', font=('微软雅黑', 10),
                              bg='#2a1a1a', fg='#c62828', relief='flat',
                              command=self._reset_all)
        reset_btn.pack(side=tk.RIGHT)

        middle_frame = tk.Frame(main_frame, bg='#150808')
        middle_frame.pack(fill=tk.X, pady=(0, 12))

        left_panel = tk.Frame(middle_frame, bg='#141414', relief='ridge', bd=1)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))
        self._build_seal_panel(left_panel)

        right_panel = tk.Frame(middle_frame, bg='#141414', relief='ridge', bd=1)
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._build_socket_panel(right_panel)

        detail_frame = tk.Frame(main_frame, bg='#141414', relief='ridge', bd=1)
        detail_frame.pack(fill=tk.BOTH, expand=True)
        self._build_detail_panel(detail_frame)

    def _build_seal_panel(self, parent):
        inner = tk.Frame(parent, bg='#141414')
        inner.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)
        tk.Label(inner, text='封印基底', font=('微软雅黑', 12, 'bold'), fg='#888888', bg='#141414').pack(anchor='w')
        self.seal_combo = ttk.Combobox(inner, state='readonly', width=20)
        self.seal_combo.pack(fill=tk.X, pady=(8, 4))
        self.seal_combo.bind('<<ComboboxSelected>>', self._on_seal_selected)
        self.seal_info = tk.Label(inner, text='请选择封印', font=('微软雅黑', 10), fg='#888888', bg='#141414', wraplength=200, justify='left')
        self.seal_info.pack(anchor='w', pady=4)
        equip_btn = tk.Button(inner, text='⚔ 装备封印', font=('微软雅黑', 10, 'bold'),
                              bg='#2a2a2a', fg='#d4af37', relief='flat', command=self._equip_seal)
        equip_btn.pack(fill=tk.X, pady=(8, 4))
        self.slot_stats = tk.Label(inner, text='插槽: 0/0', font=('微软雅黑', 10), fg='#888888', bg='#141414')
        self.slot_stats.pack(anchor='w', pady=4)
        self.unique_limit_label = tk.Label(inner, text='暗金上限: 1', font=('微软雅黑', 9), fg='#ab47bc', bg='#141414')
        self.unique_limit_label.pack(anchor='w', pady=2)

    def _build_socket_panel(self, parent):
        inner = tk.Frame(parent, bg='#141414')
        inner.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)
        tk.Label(inner, text='神符插槽', font=('微软雅黑', 12, 'bold'), fg='#888888', bg='#141414').pack(anchor='w')
        self.socket_container = tk.Frame(inner, bg='#141414')
        self.socket_container.pack(fill=tk.BOTH, expand=True, pady=8)
        tk.Label(inner, text='点击空插槽选择神符 · 右键点击卸下', font=('微软雅黑', 9), fg='#555555', bg='#141414').pack()
        self.set_status = tk.Label(inner, text='', font=('微软雅黑', 11), fg='#4fc3f7', bg='#141414')
        self.set_status.pack(pady=(4, 0))

    def _build_detail_panel(self, parent):
        self.detail_container = tk.Frame(parent, bg='#141414')
        self.detail_container.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)
        self._update_detail_panel_empty()

    def _update_detail_panel_empty(self):
        for w in self.detail_container.winfo_children():
            w.destroy()
        empty = tk.Label(self.detail_container, text='请装备封印以查看详情', font=('微软雅黑', 14), fg='#555555', bg='#141414')
        empty.pack(expand=True)

    # ---------- 事件处理 ----------
    def _on_seal_selected(self, event):
        idx = self.seal_combo.current()
        if idx < 0 or not hasattr(self, 'seal_combo_data'):
            return
        seal_id = self.seal_combo_data[idx] if idx < len(self.seal_combo_data) else None
        if not seal_id:
            return
        self._selected_seal_id = seal_id
        seal = self.talisman_system._seal_db.get(seal_id)
        if seal:
            rarity_color = '#d4af37' if seal.get('rarity') == 'mythic' else '#c87a2e'
            info = f'{seal.get("name")}  |  {seal.get("slots_base", 0)}槽'
            if seal.get('seal_affix', {}).get('type') == 'system_modifier':
                info += f'\n✨ {seal["seal_affix"].get("display", "")}'
            self.seal_info.config(text=info, fg=rarity_color)

    def _equip_seal(self):
        if not self._selected_seal_id:
            messagebox.showwarning('提示', '请先选择一个封印')
            return
        if self.talisman_system.equip_seal(self._selected_seal_id):
            self._refresh_all()
        else:
            messagebox.showerror('错误', self.talisman_system.get_last_error())

    def _on_socket_click(self, slot_index):
        if slot_index in self.talisman_system.sockets:
            self._show_rune_detail(self.talisman_system.sockets[slot_index])
            return
        self._show_rune_selector(slot_index)

    def _on_socket_right_click(self, slot_index):
        if slot_index in self.talisman_system.sockets:
            if messagebox.askyesno('确认卸下', f'确定要卸下 "{self.talisman_system.sockets[slot_index].name}" 吗？'):
                self.talisman_system.remove_rune(slot_index)
                self._refresh_all()

    def _show_rune_detail(self, rune: SocketedRune):
        affix_text = '\n'.join([f'  • {a.get("display", "")}' for a in rune.affixes])
        msg = f'【{rune.name}】\n稀有度: {rune.rarity}\n'
        if rune.set_id:
            msg += f'套装: {rune.set_id}\n'
        msg += f'\n词缀:\n{affix_text}'
        if rune.power_reference:
            msg += f'\n\n✨ 威能: {rune.power_reference.get("display", "")}'
        messagebox.showinfo('神符详情', msg)

    def _show_rune_selector(self, slot_index):
        available = self.talisman_system.get_available_runes()
        if not available:
            messagebox.showwarning('提示', '当前职业没有可用的神符')
            return
        rune_names = []
        rune_map = {}
        for rune in available:
            name = rune.get('name', '未知')
            rarity = rune.get('rarity', '')
            set_id = rune.get('set_id', '')
            label = name
            if rarity == 'unique':
                label += ' ★'
            elif rarity == 'mythic_unique':
                label += ' ✦'
            if set_id:
                label += f' [{set_id}]'
            rune_names.append(label)
            rune_map[label] = rune.get('id')
        self._show_list_dialog('选择神符', '请选择要镶嵌的神符:', rune_names, rune_map, slot_index)

    def _show_list_dialog(self, title, prompt, items, item_map, slot_index):
        dialog = tk.Toplevel(self)
        dialog.title(title)
        dialog.geometry('320x420')
        dialog.configure(bg='#1a1a1a')
        dialog.transient(self)
        dialog.grab_set()
        tk.Label(dialog, text=prompt, font=('微软雅黑', 11), fg='#c8c0b8', bg='#1a1a1a').pack(pady=10)
        search_var = tk.StringVar()
        tk.Entry(dialog, textvariable=search_var, font=('微软雅黑', 10), bg='#2a2a2a', fg='#c8c0b8', insertbackground='#c8c0b8').pack(fill=tk.X, padx=20, pady=(0, 8))
        listbox_frame = tk.Frame(dialog, bg='#1a1a1a')
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 10))
        scrollbar = tk.Scrollbar(listbox_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        listbox = tk.Listbox(listbox_frame, font=('微软雅黑', 10), bg='#2a2a2a', fg='#c8c0b8', selectbackground='#3a3a3a', selectforeground='#d4af37', yscrollcommand=scrollbar.set)
        listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=listbox.yview)
        for item in items:
            listbox.insert(tk.END, item)

        def filter_list(*args):
            keyword = search_var.get().lower()
            listbox.delete(0, tk.END)
            for item in items:
                if keyword in item.lower():
                    listbox.insert(tk.END, item)
        search_var.trace('w', filter_list)

        def on_confirm():
            sel = listbox.curselection()
            if not sel:
                return
            label = listbox.get(sel[0])
            rune_id = item_map.get(label)
            if rune_id:
                if self.talisman_system.socket_rune(slot_index, rune_id):
                    dialog.destroy()
                    self._refresh_all()
                else:
                    messagebox.showerror('错误', self.talisman_system.get_last_error())
                    dialog.destroy()

        btn_frame = tk.Frame(dialog, bg='#1a1a1a')
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        tk.Button(btn_frame, text='确认', font=('微软雅黑', 10), bg='#2a2a2a', fg='#d4af37', relief='flat', command=on_confirm).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(btn_frame, text='取消', font=('微软雅黑', 10), bg='#2a2a2a', fg='#888888', relief='flat', command=dialog.destroy).pack(side=tk.LEFT)
        listbox.bind('<Double-Button-1>', lambda e: on_confirm())

    # ---------- 刷新UI ----------
    def _refresh_all(self):
        self._refresh_seal_combo()
        self._refresh_sockets()
        self._refresh_detail_panel()
        self._refresh_set_status()
        self._refresh_slot_stats()
        if self.parent_callback:
            self.parent_callback()

    def _refresh_seal_combo(self):
        current_seal_id = self.talisman_system.current_seal.get('id') if self.talisman_system.current_seal else None
        self.seal_combo.set('')
        self.seal_combo['values'] = []
        self.seal_combo_data = []
        available = self.talisman_system.get_available_seals()
        for seal in available:
            seal_id = seal.get('id')
            name = seal.get('name', '未知')
            slots = seal.get('slots_base', 0)
            rarity = seal.get('rarity', '')
            label = f'{name} [{slots}槽]'
            if rarity == 'mythic':
                label += ' ✦'
            self.seal_combo_data.append(seal_id)
            self.seal_combo['values'] = list(self.seal_combo['values']) + [label]
        if current_seal_id:
            for i, sid in enumerate(self.seal_combo_data):
                if sid == current_seal_id:
                    self.seal_combo.current(i)
                    return
        if self.seal_combo_data:
            self.seal_combo.current(0)
        self.seal_info.config(text='请选择封印', fg='#888888')

    def _refresh_sockets(self):
        for w in self.socket_container.winfo_children():
            w.destroy()
        total_slots = self.talisman_system.get_available_slots()
        socketed = self.talisman_system.sockets
        cols = 6
        rows = (total_slots + cols - 1) // cols
        self._socket_buttons = []
        for i in range(total_slots):
            row = i // cols
            col = i % cols
            btn = tk.Button(self.socket_container, font=('微软雅黑', 10, 'bold'), width=8, height=3, relief='ridge', bd=2, cursor='hand2')
            if i in socketed:
                rune = socketed[i]
                self._setup_socket_button(btn, rune)
                btn.bind('<Button-1>', lambda e, idx=i: self._on_socket_click(idx))
                btn.bind('<Button-3>', lambda e, idx=i: self._on_socket_right_click(idx))
            else:
                self._setup_empty_socket(btn)
                btn.bind('<Button-1>', lambda e, idx=i: self._on_socket_click(idx))
            self.socket_container.grid_rowconfigure(row, weight=1)
            self.socket_container.grid_columnconfigure(col, weight=1)
            btn.grid(row=row, column=col, padx=4, pady=4, sticky='nsew')
            self._socket_buttons.append(btn)
        limit = self.talisman_system._unique_limit_override if self.talisman_system._unique_limit_override is not None else 1
        self.unique_limit_label.config(text=f'暗金上限: {limit}')

    def _setup_socket_button(self, btn, rune):
        color_map = {'set': '#4fc3f7', 'unique': '#ab47bc', 'mythic_unique': '#ff6b35'}
        color = color_map.get(rune.rarity, '#4fc3f7')
        btn.config(text=rune.name[:2], fg=color, bg='#1a2a2a', highlightbackground=color, highlightthickness=2)
        self._add_tooltip(btn, self._format_rune_tooltip(rune))

    def _setup_empty_socket(self, btn):
        btn.config(text='+', fg='#444444', bg='#1a1a1a', highlightbackground='#333333', highlightthickness=2, font=('微软雅黑', 16, 'bold'))

    def _format_rune_tooltip(self, rune):
        lines = [f'【{rune.name}】', f'稀有度: {rune.rarity}']
        if rune.set_id:
            lines.append(f'套装: {rune.set_id}')
        lines.append('')
        for affix in rune.affixes:
            lines.append(f'  • {affix.get("display", "")}')
        if rune.power_reference:
            lines.append('')
            lines.append(f'✨ {rune.power_reference.get("display", "")}')
        return '\n'.join(lines)

    def _add_tooltip(self, widget, text):
        def enter(e):
            self._tooltip = tk.Toplevel(widget)
            self._tooltip.wm_overrideredirect(True)
            self._tooltip.configure(bg='#2a2a2a', bd=1, relief='solid')
            tk.Label(self._tooltip, text=text, font=('微软雅黑', 9), fg='#c8c0b8', bg='#2a2a2a', justify='left').pack(padx=8, pady=6)
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() + 20
            self._tooltip.geometry(f'+{x}+{y}')
        def leave(e):
            if hasattr(self, '_tooltip') and self._tooltip:
                self._tooltip.destroy()
                self._tooltip = None
        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def _refresh_detail_panel(self):
        for w in self.detail_container.winfo_children():
            w.destroy()
        seal = self.talisman_system.current_seal
        if not seal:
            empty = tk.Label(self.detail_container, text='请装备封印以查看详情', font=('微软雅黑', 14), fg='#555555', bg='#141414')
            empty.pack(expand=True)
            return

        rarity = seal.get('rarity', '')
        name = seal.get('name', '未知')
        title_color = '#d4af37' if rarity == 'mythic' else '#c87a2e'
        tk.Label(self.detail_container, text=name, font=('微软雅黑', 16, 'bold'), fg=title_color, bg='#141414').pack(anchor='w')
        tk.Label(self.detail_container, text=f'{rarity.upper()} 封印  |  物品强度: 925', font=('微软雅黑', 10), fg='#888888', bg='#141414').pack(anchor='w', pady=(0, 6))
        self._add_separator()

        seal_affix = seal.get('seal_affix')
        if seal_affix:
            tk.Label(self.detail_container, text='封印词缀', font=('微软雅黑', 10, 'bold'), fg='#888888', bg='#141414').pack(anchor='w', pady=(4, 2))
            color = '#4dd0e1' if seal_affix.get('type') == 'system_modifier' else '#ff8a50'
            tk.Label(self.detail_container, text=f'▸ {seal_affix.get("display", "")}', font=('微软雅黑', 10), fg=color, bg='#141414').pack(anchor='w', padx=(12, 0))

        set_affixes = seal.get('set_affixes', [])
        if set_affixes:
            tk.Label(self.detail_container, text='套装词缀', font=('微软雅黑', 10, 'bold'), fg='#888888', bg='#141414').pack(anchor='w', pady=(4, 2))
            for affix in set_affixes:
                tk.Label(self.detail_container, text=f'▸ {affix.get("display", "")}', font=('微软雅黑', 10), fg='#ffd54f', bg='#141414').pack(anchor='w', padx=(12, 0))

        self._add_separator()
        tk.Label(self.detail_container, text='已镶嵌神符', font=('微软雅黑', 10, 'bold'), fg='#888888', bg='#141414').pack(anchor='w', pady=(4, 2))
        socketed = self.talisman_system.sockets
        if socketed:
            color_map = {'set': '#4fc3f7', 'unique': '#ab47bc', 'mythic_unique': '#ff6b35'}
            for idx, rune in socketed.items():
                color = color_map.get(rune.rarity, '#66bb6a')
                affix_texts = [a.get('display', '') for a in rune.affixes]
                tk.Label(self.detail_container, text=f'#{idx+1} {rune.name}  |  {"  ".join(affix_texts)}', font=('微软雅黑', 9), fg=color, bg='#141414').pack(anchor='w', padx=(12, 0))
        else:
            tk.Label(self.detail_container, text='暂无镶嵌神符', font=('微软雅黑', 10), fg='#555555', bg='#141414').pack(anchor='w', padx=(12, 0))

        self._add_separator()
        tk.Label(self.detail_container, text='套装效果', font=('微软雅黑', 10, 'bold'), fg='#888888', bg='#141414').pack(anchor='w', pady=(4, 2))
        set_bonuses = self.talisman_system.get_active_set_bonuses()
        if set_bonuses:
            tier_colors = {'2': '#8bc34a', '3': '#ffb300', '5': '#ff5722'}
            for set_id, descs in set_bonuses.items():
                tk.Label(self.detail_container, text=f'【{set_id}】已激活', font=('微软雅黑', 10, 'bold'), fg='#4fc3f7', bg='#141414').pack(anchor='w', padx=(12, 0))
                for desc in descs:
                    tier = '2' if '(2)' in desc else '3' if '(3)' in desc else '5'
                    tk.Label(self.detail_container, text=f'  {desc}', font=('微软雅黑', 9), fg=tier_colors.get(tier, '#888888'), bg='#141414').pack(anchor='w', padx=(24, 0))
        else:
            tk.Label(self.detail_container, text='未激活任何套装效果', font=('微软雅黑', 10), fg='#555555', bg='#141414').pack(anchor='w', padx=(12, 0))

    def _add_separator(self):
        sep = tk.Frame(self.detail_container, height=1, bg='#2a2a2a')
        sep.pack(fill=tk.X, pady=6)

    def _refresh_set_status(self):
        set_bonuses = self.talisman_system.get_active_set_bonuses()
        if set_bonuses:
            texts = []
            for set_id, descs in set_bonuses.items():
                count = sum(1 for r in self.talisman_system.sockets.values() if r.set_id == set_id)
                req = self.talisman_system.get_required_count_for_tier(5)
                texts.append(f'✅ {set_id} {count}/{req} 已激活' if count >= req else f'⏳ {set_id} {count}/{req} 还需{req-count}件')
            unique_count = sum(1 for r in self.talisman_system.sockets.values() if r.rarity in ('unique', 'mythic_unique'))
            if unique_count:
                texts.append(f'✨ 暗金神符: {unique_count} 个')
            self.set_status.config(text='  |  '.join(texts), fg='#4fc3f7')
        else:
            self.set_status.config(text='未装备套装神符', fg='#555555')

    def _refresh_slot_stats(self):
        if self.talisman_system.current_seal:
            total = self.talisman_system.get_available_slots()
            used = len(self.talisman_system.sockets)
            self.slot_stats.config(text=f'插槽: {used}/{total}')
        else:
            self.slot_stats.config(text='插槽: 0/0')

    def _reset_all(self):
        if messagebox.askyesno('确认重置', '确定要重置所有护身符配置吗？'):
            self.talisman_system.equip_seal(None)
            self._refresh_all()

    def _on_data_changed(self):
        self._refresh_all()

    # ---------- 外部接口 ----------
    def set_active_class(self, class_name: str):
        self.class_label.config(text=f'当前配装: {class_name}')
        self.talisman_system.set_active_class(class_name)
        from data.loader import load_seals, load_talisman_runes
        seals = load_seals(class_name)
        runes = load_talisman_runes(class_name)
        # 修正：传递两个独立参数，而不是一个字典
        self.talisman_system.load_data(seals, runes)
        self._refresh_all()  # <-- 确保这一行存在，职业切换后刷新UI和技能树

    def get_total_modifiers(self) -> Dict[str, float]:
        return self.talisman_system.get_total_modifiers()