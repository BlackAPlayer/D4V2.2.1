# -*- coding: utf-8 -*-
# 模块: ui/skill_tree_tooltip
# 职责: 管理技能和分支的悬停提示窗口

import tkinter as tk
from tkinter import ttk
from typing import Any, Dict, Optional

class SkillTreeTooltip:
    """技能树悬停提示管理器"""

    def __init__(self, parent: tk.Widget, skill_system):
        self.parent = parent
        self.skill_system = skill_system
        self.tip_window = None

    def show_skill_tip(self, event, skill_key: str):
        if not skill_key:
            return
        self.hide()
        info = self.skill_system.get_skill_display_info(skill_key)
        if not info or info.get('name', '').startswith('未知技能'):
            return

        tip = tk.Toplevel(self.parent)
        tip.wm_overrideredirect(True)
        tip.geometry(f"+{event.x_root+15}+{event.y_root+15}")

        bg = '#1a1a1a'
        fg = '#DDDDDD'
        title_color = '#FFD700'
        frame = tk.Frame(tip, bg=bg, bd=1, relief='solid')
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)

        tk.Label(frame, text=info['name'], font=('微软雅黑', 12, 'bold'),
                 fg=title_color, bg=bg).pack(anchor='w')

        tk.Label(frame, text=f"等级: {info['base_level']} / {info['total_level']} (额外 +{info['extra_level']})",
                 font=('微软雅黑', 9), fg='#88FF88', bg=bg).pack(anchor='w')

        if info['tags']:
            tk.Label(frame, text=f"标签: {', '.join(info['tags'])}", font=('微软雅黑', 8),
                     fg='#888888', bg=bg).pack(anchor='w')
        if info['damage_type']:
            tk.Label(frame, text=f"伤害类型: {info['damage_type']}", font=('微软雅黑', 8),
                     fg='#888888', bg=bg).pack(anchor='w')

        tk.Frame(frame, height=1, bg='#333333').pack(fill=tk.X, pady=5)

        desc = info['description']
        if len(desc) > 300:
            desc = desc[:300] + '...'
        tk.Label(frame, text=desc, font=('微软雅黑', 9), fg=fg, bg=bg,
                 wraplength=280, justify='left').pack(anchor='w')

        tip.update_idletasks()
        x = event.x_root + 15
        y = event.y_root + 15
        w = tip.winfo_width()
        h = tip.winfo_height()
        screen_w = tip.winfo_screenwidth()
        screen_h = tip.winfo_screenheight()
        if x + w > screen_w:
            x = event.x_root - w - 15
        if y + h > screen_h:
            y = event.y_root - h - 15
        tip.geometry(f"+{x}+{y}")

        self.tip_window = tip

    def show_branch_tip(self, event, skill_key: str, branch_id: str):
        self.hide()
        branches = self.skill_system.get_branches(skill_key)
        branch = branches.get(branch_id)
        if not branch:
            return
        tip = tk.Toplevel(self.parent)
        tip.wm_overrideredirect(True)
        tip.geometry(f"+{event.x_root+15}+{event.y_root+15}")

        label = tk.Label(tip, text=f"{branch['name']}\n{branch.get('desc', '')}",
                         font=('微软雅黑', 9), bg='#2a2a2a', fg='#FFFFFF',
                         wraplength=200, justify='left')
        label.pack(padx=5, pady=5)

        self.tip_window = tip

    def hide(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None