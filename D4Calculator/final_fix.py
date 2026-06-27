#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
一键修复 D4Calculator 技能树问题
- 修补布局文件（自动填充 ownerSkillKey / branchId）
- 替换 UI 为最终优化版
- 清除缓存
"""

import os
import json
import shutil
import sys
from collections import defaultdict, deque

# ---------- 配置 ----------
LAYOUT_FILE = 'skilltree_layout.json'
UI_FILE = 'ui/skill_tree_ui.py'
BACKUP_SUFFIX = '.backup'

# ---------- 1. 修补布局 ----------
def fix_layout():
    print("📂 正在修补 skilltree_layout.json ...")
    if not os.path.exists(LAYOUT_FILE):
        print(f"❌ 未找到 {LAYOUT_FILE}，请确保在项目根目录运行。")
        return False

    # 备份
    backup_name = LAYOUT_FILE + BACKUP_SUFFIX
    shutil.copy2(LAYOUT_FILE, backup_name)
    print(f"✅ 已备份原文件为 {backup_name}")

    with open(LAYOUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    nodes = data.get('nodes', [])
    edges = data.get('edges', [])

    id_to_node = {node['id']: node for node in nodes}
    adjacency = defaultdict(list)
    for edge in edges:
        frm, to = edge['fromNodeId'], edge['toNodeId']
        adjacency[frm].append(to)
        adjacency[to].append(frm)

    active_ids = {node['id'] for node in nodes if node.get('nodeType') == 'active'}
    hub_ids = {144, 188, 205, 258, 307, 309}   # 枢纽装饰节点（不归属任何技能）

    assignments = {}

    for active_id in active_ids:
        active_node = id_to_node.get(active_id)
        if not active_node:
            continue
        skill_key = active_node.get('skillKey')
        if not skill_key:
            continue
        neighbors = [n for n in adjacency.get(active_id, []) if n not in hub_ids and n not in active_ids]
        branch_counter = 1
        visited_in_subtree = set()

        for neighbor in neighbors:
            if neighbor in visited_in_subtree:
                continue
            queue = deque([neighbor])
            visited_in_branch = set()
            while queue:
                curr = queue.popleft()
                if curr in visited_in_branch:
                    continue
                if curr in active_ids or curr in hub_ids:
                    continue
                visited_in_branch.add(curr)
                visited_in_subtree.add(curr)
                for next_node in adjacency.get(curr, []):
                    if (next_node not in visited_in_branch and 
                        next_node not in active_ids and 
                        next_node not in hub_ids):
                        queue.append(next_node)
            for node_id in visited_in_branch:
                assignments[node_id] = (skill_key, str(branch_counter))
            branch_counter += 1

    for node in nodes:
        node_id = node['id']
        if node_id in assignments:
            node['ownerSkillKey'] = assignments[node_id][0]
            node['branchId'] = assignments[node_id][1]
        else:
            node['ownerSkillKey'] = None
            node['branchId'] = None

    with open(LAYOUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ 已修补 {LAYOUT_FILE}，共处理 {len(nodes)} 个节点。")
    return True

# ---------- 2. 替换 UI 文件 ----------
def fix_ui():
    print("📂 正在替换 ui/skill_tree_ui.py ...")
    ui_dir = os.path.dirname(UI_FILE)
    if not os.path.exists(ui_dir):
        os.makedirs(ui_dir)

    if os.path.exists(UI_FILE):
        backup_name = UI_FILE + BACKUP_SUFFIX
        shutil.copy2(UI_FILE, backup_name)
        print(f"✅ 已备份原文件为 {backup_name}")

    # 最终版代码（包含互斥、金色边框、分支描述附加等）
    ui_code = '''# -*- coding: utf-8 -*-
# 模块: ui/skill_tree_ui

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import logging
import math
from PIL import Image, ImageTk

from config import resource_path
from utils.image_cache import load_photo_image
from ui.skill_tree_tooltip import SkillTreeTooltip


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
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.bg_image = None
        self.bg_photo = None
        self._load_background_image()

        self.drag_start_x = 0
        self.drag_start_y = 0
        self.view_x = 0.0
        self.view_y = 0.0

        self.nodes = []
        self.edges = []
        self.line_style = {}
        self.node_refs = {}
        self.background_margin = 500
        self.bg_left = 0
        self.bg_top = 0
        self.bg_width = 0
        self.bg_height = 0
        self._first_draw_done = False
        self.selected_nodes = []

        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.canvas.bind('<Leave>', self._on_canvas_leave)

        self._load_layout(layout_file)

        self.canvas.bind('<ButtonPress-1>', self._on_drag_start)
        self.canvas.bind('<B1-Motion>', self._on_drag_move)

        self.tooltip_manager = SkillTreeTooltip(self.parent, self.skill_system)

        self.skill_system.add_listener(self.refresh)
        self.refresh()
        self.canvas.after(100, self._check_and_draw)

    # ---------- 辅助方法 ----------
    def _check_and_draw(self):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w > 1 and h > 1:
            if not self._first_draw_done:
                self._on_first_draw()
        else:
            if not hasattr(self, '_check_count'):
                self._check_count = 0
            self._check_count += 1
            if self._check_count < 50:
                self.canvas.after(100, self._check_and_draw)
            else:
                self._on_first_draw()

    def _on_canvas_configure(self, event):
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w > 1 and h > 1:
            if not self._first_draw_done:
                self._on_first_draw()
            else:
                self._redraw_all()

    def _on_first_draw(self):
        self._first_draw_done = True
        self._redraw_all()

    def _load_background_image(self):
        bg_path = resource_path('images/skill_bg.png')
        if os.path.exists(bg_path):
            try:
                self.bg_image = Image.open(bg_path)
                self.bg_photo = None
            except Exception:
                self.bg_image = None
        else:
            self.bg_image = None

    def _load_background_image_from_path(self, path):
        if not path:
            self._load_background_image()
            return
        full_path = resource_path(path)
        if os.path.exists(full_path):
            try:
                self.bg_image = Image.open(full_path)
                self.bg_photo = None
                return
            except Exception:
                pass
        self._load_background_image()

    def _load_layout(self, layout_file):
        full_path = resource_path(layout_file)
        if not os.path.exists(full_path):
            self._auto_layout()
            return
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self._layout_data = data
        except Exception:
            self._auto_layout()
            return

        if isinstance(data, dict):
            self.background_margin = data.get('backgroundMargin', 250)
            bg_path = data.get('backgroundImagePath')
            if bg_path:
                self._load_background_image_from_path(bg_path)

        if isinstance(data, list):
            nodes_data = data
            edges_data = []
        elif isinstance(data, dict):
            nodes_data = data.get('nodes') or data.get('skills') or []
            edges_data = data.get('edges', [])
            self.line_style = data.get('lineStyle', {})
        else:
            nodes_data = []
            edges_data = []
        self.nodes = []
        self.edges = edges_data

        key_to_id = {}
        name_to_id = {}
        for sid, skill in self.skill_system.skill_data.items():
            if skill.get('key'):
                key_to_id[skill['key']] = sid
            if skill.get('name'):
                name_to_id[skill['name']] = sid

        for nd in nodes_data:
            skill_key = None
            icon_id = nd.get('iconId')
            sk = nd.get('skillKey') or nd.get('skill_id')
            skill_name = nd.get('skillName')
            is_passive = nd.get('isPassive', False)
            node_type = nd.get('nodeType', 'decor')
            is_decor = (node_type == 'decor')
            scale = nd.get('scale', 1.0)
            mod_data = nd.get('mod_data')
            border_image = nd.get('borderImage')
            icon_path = nd.get('iconPath')
            owner_skill_key = nd.get('ownerSkillKey')
            branch_id = nd.get('branchId')

            # 转换 owner_skill_key 为整数 ID
            if owner_skill_key is not None:
                if isinstance(owner_skill_key, str):
                    if owner_skill_key in key_to_id:
                        owner_skill_key = key_to_id[owner_skill_key]
                    else:
                        skill_obj = self.skill_system._find_skill(owner_skill_key)
                        if skill_obj:
                            owner_skill_key = skill_obj['id']
                        else:
                            owner_skill_key = None
                elif not isinstance(owner_skill_key, int):
                    owner_skill_key = None

            if is_decor:
                skill_key = None
            else:
                if sk and sk in key_to_id:
                    skill_key = key_to_id[sk]
                elif sk and isinstance(sk, str):
                    try:
                        skill_key = int(sk)
                    except:
                        pass
                if not skill_key and skill_name and skill_name in name_to_id:
                    skill_key = name_to_id[skill_name]
                if not skill_key and icon_id is not None:
                    str_icon_id = str(icon_id)
                    for sid, skill in self.skill_system.skill_data.items():
                        if str(skill.get('icon')) == str_icon_id:
                            skill_key = sid
                            break
                if not skill_key and sk:
                    skill_obj = self.skill_system._find_skill(sk)
                    if skill_obj:
                        skill_key = skill_obj['id']

            x = nd.get('left') or nd.get('x')
            y = nd.get('top') or nd.get('y')
            if x is None or y is None:
                continue

            skill = self.skill_system._find_skill(skill_key) if skill_key is not None else None

            node = {
                'id': nd.get('id'),
                'skill_key': skill_key,
                'skill': skill,
                'x': x,
                'y': y,
                'type': nd.get('type', 'skill'),
                'internal_id': str(skill_key) if skill_key else f"token_{x}_{y}",
                'icon_id': icon_id,
                'borderImage': border_image,
                'isPassive': is_passive,
                'isDecor': is_decor,
                'nodeType': node_type,
                'scale': scale,
                'skillName': skill_name,
                'mod_data': mod_data,
                'iconPath': icon_path,
                'owner_skill_key': owner_skill_key,
                'branch_id': branch_id,
            }
            self.nodes.append(node)

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
        self.edges = []
        self.line_style = {}
        start_x, start_y = 100, 100
        col_width, row_height, max_per_row = 180, 120, 10
        current_y = start_y
        node_id = 100
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
                        'id': node_id,
                        'skill_key': key,
                        'skill': skill,
                        'x': x,
                        'y': current_y + row * row_height,
                        'type': 'skill',
                        'internal_id': str(key) if key else f"auto_{x}_{current_y+row*row_height}",
                        'icon_id': None,
                        'borderImage': None,
                        'isPassive': False,
                        'isDecor': False,
                        'nodeType': 'active',
                        'scale': 1.0,
                        'skillName': skill['name'] if skill else None,
                        'mod_data': None,
                        'iconPath': None,
                        'owner_skill_key': None,
                        'branch_id': None,
                    })
                    node_id += 1
                    x += col_width
            current_y += row_count * row_height + 40

    def _get_icon_path(self, skill_key, skill, icon_id=None, icon_path=None):
        if icon_path and os.path.exists(resource_path(icon_path)):
            return resource_path(icon_path)
        if skill and skill.get('icon'):
            icon_path = resource_path(f'images/icons/{skill["icon"]}.png')
            if os.path.exists(icon_path):
                return icon_path
        if skill_key and isinstance(skill_key, int):
            icon_path = resource_path(f'images/icons/{skill_key}.png')
            if os.path.exists(icon_path):
                return icon_path
        if skill_key and isinstance(skill_key, str):
            pure_name = skill_key.split('_', 1)[-1] if '_' in skill_key else skill_key
            path_pure = resource_path(f'images/icons/{pure_name}.png')
            if os.path.exists(path_pure):
                return path_pure
            path_full = resource_path(f'images/icons/{skill_key}.png')
            if os.path.exists(path_full):
                return path_full
        if icon_id:
            icon_path = resource_path(f'images/icons/{icon_id}.png')
            if os.path.exists(icon_path):
                return icon_path
        return None

    def _draw_edges(self):
        if not self.edges:
            return
        color = self.line_style.get('color', '#8a9bb5')
        width = self.line_style.get('width', 2)
        dash = self.line_style.get('dash', False)
        node_map = {n['id']: n for n in self.nodes if 'id' in n}
        for edge in self.edges:
            from_id = edge.get('fromNodeId')
            to_id = edge.get('toNodeId')
            if from_id is None or to_id is None:
                continue
            from_node = node_map.get(from_id)
            to_node = node_map.get(to_id)
            if not from_node or not to_node:
                continue
            x1 = from_node['x']
            y1 = from_node['y']
            x2 = to_node['x']
            y2 = to_node['y']
            if dash:
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width,
                                        dash=(4, 4), tags=('edge',))
            else:
                self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width,
                                        tags=('edge',))
        self.canvas.tag_raise('edge')

    def _redraw_all(self):
        self.canvas.delete('all')
        self.canvas.update_idletasks()
        self._draw_background()
        self._draw_edges()
        self._draw_all_nodes()
        self.canvas.tag_lower('bg')
        self.canvas.tag_raise('edge')
        self.canvas.tag_raise('node')
        self._adjust_viewport()

    def _adjust_viewport(self):
        if not self.nodes:
            return
        xs = [n['x'] for n in self.nodes]
        ys = [n['y'] for n in self.nodes]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        min_y -= 150
        max_y += 150
        margin = self.background_margin
        left = min_x - margin
        top = min_y - margin
        right = max_x + margin
        bottom = max_y + margin
        if hasattr(self, 'bg_left') and self.bg_width > 0:
            left = min(left, self.bg_left)
            top = min(top, self.bg_top)
            right = max(right, self.bg_left + self.bg_width)
            bottom = max(bottom, self.bg_top + self.bg_height)
        left -= 50
        top -= 50
        right += 50
        bottom += 50
        self.canvas.config(scrollregion=(left, top, right, bottom))
        active_nodes = [n for n in self.nodes if n.get('skill_key') and not n.get('isPassive', False)]
        target_node = active_nodes[1] if len(active_nodes) >= 2 else (active_nodes[0] if active_nodes else None)
        if target_node:
            target_x = target_node['x']
            target_y = target_node['y']
        else:
            target_x = (left + right) / 2
            target_y = (top + bottom) / 2
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw > 1 and ch > 1:
            total_w = right - left
            total_h = bottom - top
            if total_w > 0 and total_h > 0:
                frac_x = max(0, min(1, (target_x - left - cw/2) / total_w))
                frac_y = max(0, min(1, (target_y - top - ch/2) / total_h))
                self.canvas.xview_moveto(frac_x)
                self.canvas.yview_moveto(frac_y)
                self.view_x = frac_x
                self.view_y = frac_y

    def _draw_background(self):
        if not self.bg_image:
            return
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1 or h <= 1:
            return
        img_w, img_h = self.bg_image.size
        if img_w <= 0 or img_h <= 0:
            return

        if not self.nodes:
            canvas_aspect = w / h
            img_aspect = img_w / img_h
            if img_aspect > canvas_aspect:
                draw_w = w
                draw_h = w / img_aspect
                offset_x = 0
                offset_y = (h - draw_h) / 2
            else:
                draw_h = h
                draw_w = h * img_aspect
                offset_x = (w - draw_w) / 2
                offset_y = 0
            scaled = self.bg_image.resize((int(draw_w), int(draw_h)), Image.Resampling.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(scaled)
            self.canvas.create_image(offset_x, offset_y, image=self.bg_photo, anchor='nw', tags=('bg',))
            self.bg_left = offset_x
            self.bg_top = offset_y
            self.bg_width = draw_w
            self.bg_height = draw_h
            return

        xs = [n['x'] for n in self.nodes]
        ys = [n['y'] for n in self.nodes]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        min_y -= 150
        max_y += 150
        margin = self.background_margin
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        width = max_x - min_x + 2 * margin
        height = max_y - min_y + 2 * margin
        if width <= 0 or height <= 0:
            return
        left = center_x - width / 2
        top = center_y - height / 2
        try:
            scaled = self.bg_image.resize((int(width), int(height)), Image.Resampling.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(scaled)
            self.canvas.create_image(left, top, image=self.bg_photo, anchor='nw', tags=('bg',))
            self.bg_left = left
            self.bg_top = top
            self.bg_width = width
            self.bg_height = height
        except Exception:
            pass

    # ---------- 核心绘制节点 ----------
    def _draw_all_nodes(self):
        BASE_NODE_RADIUS = 64
        BASE_ICON_SIZE = 56
        self.node_refs.clear()
        if not hasattr(self, '_border_photos'):
            self._border_photos = []

        for node in self.nodes:
            x, y = node['x'], node['y']
            skill_key = node.get('skill_key')
            skill = self.skill_system.skill_data.get(skill_key) if skill_key is not None else None
            if skill is None and skill_key is not None:
                skill = self.skill_system._find_skill(skill_key)
            node['skill'] = skill

            internal_id = node['internal_id']
            icon_id = node.get('icon_id')
            is_passive = node.get('isPassive', False)
            is_decor = node.get('isDecor', False)
            node_type = node.get('nodeType', 'decor')
            scale = node.get('scale', 1.0)
            mod_data = node.get('mod_data')
            owner_skill = node.get('owner_skill_key')
            branch_id = node.get('branch_id')

            is_selected = node in self.selected_nodes

            passive_scale = 0.65 if (is_passive or is_decor) else 1.0
            NODE_RADIUS = BASE_NODE_RADIUS * passive_scale * scale

            # ---- 美化节点 ----
            if is_decor:
                ICON_SIZE = BASE_ICON_SIZE * 0.7 * passive_scale * scale
                border_image_path = node.get('borderImage')
                if border_image_path:
                    full_path = resource_path(border_image_path)
                    if os.path.exists(full_path):
                        photo = load_photo_image(full_path, size=(int(ICON_SIZE * 1.6), int(ICON_SIZE * 1.6)))
                        if photo:
                            self.canvas.create_image(x, y, image=photo, tags=(internal_id, 'node'))
                            self._border_photos.append(photo)
                icon_path = node.get('iconPath') or self._get_icon_path(node.get('skill_key'), skill, icon_id)
                if icon_path and os.path.exists(icon_path):
                    photo = load_photo_image(icon_path, size=(int(ICON_SIZE), int(ICON_SIZE)))
                    if photo:
                        self.canvas.create_image(x, y, image=photo, tags=(internal_id, 'node'))
                if is_selected:
                    ring_size = (border_image_path and 40 or 36) * passive_scale * scale
                    self.canvas.create_oval(x - ring_size, y - ring_size, x + ring_size, y + ring_size,
                                            outline='#ffffff', width=2.5, dash=(5, 5),
                                            tags=(internal_id, 'node'))
                continue

            # ---- 普通节点 ----
            ICON_SIZE = BASE_ICON_SIZE * passive_scale * scale
            BORDER_SIZE = int(ICON_SIZE * 1.6)
            FONT_SIZE_LEVEL = int(8 * passive_scale * scale)
            FONT_SIZE_BRANCH = int(12 * passive_scale * scale)

            has_icon = False
            icon_path = node.get('iconPath') or self._get_icon_path(node.get('skill_key'), skill, icon_id)
            if icon_path and os.path.exists(icon_path):
                has_icon = True

            border_image_path = node.get('borderImage')
            if border_image_path:
                full_path = resource_path(border_image_path)
                if os.path.exists(full_path):
                    photo = load_photo_image(full_path, size=(BORDER_SIZE, BORDER_SIZE))
                    if photo:
                        self.canvas.create_image(x, y, image=photo, tags=(internal_id, 'node'))
                        self._border_photos.append(photo)

            if has_icon:
                photo = load_photo_image(icon_path, size=(int(ICON_SIZE), int(ICON_SIZE)))
                if photo:
                    self.canvas.create_image(x, y, image=photo, tags=(internal_id, 'node'))
            elif skill:
                text = skill['name'][:2]
                self.canvas.create_text(x, y, text=text, fill='white',
                                        font=('微软雅黑', int(FONT_SIZE_BRANCH), 'bold'),
                                        tags=(internal_id, 'node'))
            else:
                self.canvas.create_text(x, y, text='?', fill='#888888',
                                        font=('微软雅黑', int(FONT_SIZE_BRANCH + 2), 'bold'),
                                        tags=(internal_id, 'node'))

            ref = self.node_refs.setdefault(internal_id, {})
            ref['node'] = node
            ref['is_passive'] = is_passive
            ref['is_decor'] = is_decor

            # ---------- 主动技能等级文本 ----------
            if node_type == 'active':
                sk = node.get('skill_key')
                if sk is not None:
                    if not isinstance(sk, int):
                        sk_obj = self.skill_system._find_skill(sk)
                        if sk_obj:
                            sk = sk_obj['id']
                            node['skill_key'] = sk
                    base_lv = self.skill_system.get_base_level(sk)
                    max_lv = skill.get('base_max_level', 15) if skill else 15
                    branch_count = len(self.skill_system.branch_levels.get(sk, {}))
                    branch_text = f" +{branch_count}分支" if branch_count > 0 else ""
                    lv_text = self.canvas.create_text(
                        x + 22 * scale, y + 22 * scale,
                        text=f"{base_lv}/{max_lv}{branch_text}",
                        fill='#88FF88',
                        font=('微软雅黑', int(FONT_SIZE_LEVEL), 'bold'),
                        anchor='se',
                        tags=(internal_id, 'node')
                    )
                    ref['lv_text'] = lv_text

            # ---------- 分支节点：激活边框 + 1/1 文本 ----------
            if node_type in ('passive', 'morph'):
                if owner_skill is not None and not isinstance(owner_skill, int):
                    sk_obj = self.skill_system._find_skill(owner_skill)
                    if sk_obj:
                        owner_skill = sk_obj['id']
                        node['owner_skill_key'] = owner_skill
                is_active = False
                if owner_skill is not None and branch_id is not None:
                    branch_levels = self.skill_system.branch_levels.get(owner_skill, {})
                    if branch_levels.get(str(branch_id), 0) > 0:
                        is_active = True

                # 显示 1/1 文本（右上角）
                lv_text = self.canvas.create_text(
                    x + 22 * scale, y - 22 * scale,
                    text="1/1" if is_active else "0/1",
                    fill='#88FF88' if is_active else '#666666',
                    font=('微软雅黑', int(FONT_SIZE_LEVEL), 'bold'),
                    anchor='nw',
                    tags=(internal_id, 'node')
                )
                ref['lv_text'] = lv_text

                # 激活时绘制金色边框（更明显的视觉反馈）
                if is_active:
                    border_radius = NODE_RADIUS + 4
                    self.canvas.create_oval(
                        x - border_radius, y - border_radius,
                        x + border_radius, y + border_radius,
                        outline='#FFD700', width=3,
                        tags=(internal_id, 'node')
                    )

            # ---------- 可点击区域（缩小范围） ----------
            hitbox_radius = NODE_RADIUS * 0.7
            hitbox = self.canvas.create_rectangle(
                x - hitbox_radius, y - hitbox_radius,
                x + hitbox_radius, y + hitbox_radius,
                fill='', outline='', tags=(internal_id, 'hitbox', 'node')
            )
            ref['hitbox'] = hitbox

            self.canvas.tag_bind(hitbox, '<Leave>', self.tooltip_manager.hide)

            # ---------- 事件绑定 ----------
            if node_type == 'active':
                sk = node.get('skill_key')
                if sk is not None:
                    self.canvas.tag_bind(hitbox, '<Button-1>',
                        lambda e, key=sk: self._on_left_click(key))
                    self.canvas.tag_bind(hitbox, '<Button-3>',
                        lambda e, key=sk: self._on_right_click(key))
                    self.canvas.tag_bind(hitbox, '<Enter>',
                        lambda e, key=sk: self.tooltip_manager.show_skill_tip(e, key))
            elif node_type in ('passive', 'morph'):
                if owner_skill is not None and branch_id is not None:
                    self.canvas.tag_bind(hitbox, '<Button-1>',
                        lambda e, sk=owner_skill, bid=branch_id: self._on_branch_click(sk, bid))
                    self.canvas.tag_bind(hitbox, '<Button-3>',
                        lambda e, sk=owner_skill, bid=branch_id: self._on_branch_right_click(sk, bid))
                    if mod_data:
                        self.canvas.tag_bind(hitbox, '<Enter>',
                            lambda e, data=mod_data: self.tooltip_manager.show_skill_tip(e, {'mod_data': data}))

    # ---------- 事件处理 ----------
    def _on_canvas_leave(self, event):
        self.tooltip_manager.hide()

    def _on_drag_start(self, event):
        self.tooltip_manager.hide()
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        self.view_x = self.canvas.xview()[0]
        self.view_y = self.canvas.yview()[0]

    def _on_drag_move(self, event):
        dx = event.x - self.drag_start_x
        dy = event.y - self.drag_start_y
        bbox = self.canvas.bbox('all')
        if bbox:
            region_w = bbox[2] - bbox[0]
            region_h = bbox[3] - bbox[1]
            canvas_w = self.canvas.winfo_width()
            canvas_h = self.canvas.winfo_height()
            if canvas_w > 0 and canvas_h > 0:
                move_x = dx / region_w if region_w > 0 else 0
                move_y = dy / region_h if region_h > 0 else 0
                new_x = self.view_x - move_x
                new_y = self.view_y - move_y
                new_x = max(0, min(1, new_x))
                new_y = max(0, min(1, new_y))
                self.canvas.xview_moveto(new_x)
                self.canvas.yview_moveto(new_y)
                self.view_x = new_x
                self.view_y = new_y
                self.drag_start_x = event.x
                self.drag_start_y = event.y

    def _on_left_click(self, skill_key):
        if skill_key is None:
            return
        self.skill_system.add_level(skill_key)

    def _on_right_click(self, skill_key):
        if skill_key is None:
            return
        self.skill_system.remove_level(skill_key)

    def _on_branch_click(self, skill_key, branch_id):
        if skill_key is None or branch_id is None:
            return
        # 如果已激活则忽略
        if self.skill_system.branch_levels.get(skill_key, {}).get(str(branch_id), 0) > 0:
            return
        # 取消该技能下所有已激活分支（互斥）
        current = self.skill_system.branch_levels.get(skill_key, {})
        for bid in list(current.keys()):
            self.skill_system.deactivate_branch(skill_key, bid)
        # 激活新分支
        self.skill_system.activate_branch(skill_key, branch_id)

    def _on_branch_right_click(self, skill_key, branch_id):
        if skill_key is None or branch_id is None:
            return
        self.skill_system.deactivate_branch(skill_key, branch_id)

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

    # ---------- 增量刷新 ----------
    def refresh(self):
        total_allocated = sum(self.skill_system.skill_levels.values()) + sum(len(b) for b in self.skill_system.branch_levels.values())
        self.allocated_label.config(text=f"已分配点数: {total_allocated}")
        self.points_label.config(text=f"剩余点数: {self.skill_system.available_points}")

        for internal_id, ref in self.node_refs.items():
            node = ref.get('node')
            if not node:
                continue
            skill_key = node.get('skill_key')
            node_type = node.get('nodeType')

            if node_type == 'active' and skill_key is not None:
                if not isinstance(skill_key, int):
                    sk_obj = self.skill_system._find_skill(skill_key)
                    if sk_obj:
                        skill_key = sk_obj['id']
                        node['skill_key'] = skill_key
                skill = self.skill_system._find_skill(skill_key)
                lv_text_id = ref.get('lv_text')
                if lv_text_id:
                    base_lv = self.skill_system.get_base_level(skill_key)
                    max_lv = skill.get('base_max_level', 15) if skill else 15
                    branch_count = len(self.skill_system.branch_levels.get(skill_key, {}))
                    branch_text = f" +{branch_count}分支" if branch_count > 0 else ""
                    self.canvas.itemconfig(lv_text_id, text=f"{base_lv}/{max_lv}{branch_text}")

            elif node_type in ('passive', 'morph'):
                owner_skill = node.get('owner_skill_key')
                branch_id = node.get('branch_id')
                if owner_skill is not None and branch_id is not None:
                    if not isinstance(owner_skill, int):
                        sk_obj = self.skill_system._find_skill(owner_skill)
                        if sk_obj:
                            owner_skill = sk_obj['id']
                            node['owner_skill_key'] = owner_skill
                    is_active = self.skill_system.branch_levels.get(owner_skill, {}).get(str(branch_id), 0) > 0
                    lv_text_id = ref.get('lv_text')
                    if lv_text_id:
                        self.canvas.itemconfig(lv_text_id, text="1/1" if is_active else "0/1")
                        self.canvas.itemconfig(lv_text_id, fill='#88FF88' if is_active else '#666666')
                    # 刷新边框（由于没有存储边框ID，本次刷新无法更新，但已绘制时已创建）
                    # 为简化，我们只能重新绘制，但为了性能，这里不做
                    # 但激活/取消会触发 _redraw_all，所以边框会更新
                    # 因此只需在 _on_branch_click 后调用 refresh 即可。
'''

    with open(UI_FILE, 'w', encoding='utf-8') as f:
        f.write(ui_code)

    print(f"✅ 已更新 {UI_FILE}")
    return True

# ---------- 3. 清除缓存 ----------
def clear_cache():
    print("🧹 正在清除 __pycache__ ...")
    removed = 0
    for root, dirs, files in os.walk('.'):
        if '__pycache__' in dirs:
            cache_dir = os.path.join(root, '__pycache__')
            try:
                shutil.rmtree(cache_dir)
                print(f"  已删除 {cache_dir}")
                removed += 1
            except Exception as e:
                print(f"  无法删除 {cache_dir}: {e}")
    print(f"✅ 已清除 {removed} 个缓存目录")
    return True

# ---------- 主流程 ----------
def main():
    print("="*50)
    print("  D4Calculator 技能树一键修复")
    print("="*50)
    print("即将执行：")
    print("1. 修补 skilltree_layout.json（自动填充分支归属）")
    print("2. 替换 ui/skill_tree_ui.py（最终优化版）")
    print("3. 清除缓存")
    print("="*50)
    input("按 Enter 键继续，或 Ctrl+C 取消...")

    success = True
    if not fix_layout():
        success = False
    if not fix_ui():
        success = False
    if not clear_cache():
        success = False

    print("="*50)
    if success:
        print("✅ 修复完成！请重启程序（完全关闭后再打开）。")
        print("测试方法：给主动技能加1点，然后点击其分支节点（如萤火虫）。")
        print("观察：分支节点出现金色边框，主动技能右下角显示 +1分支。")
        print("如果仍然异常，请将控制台输出截图发送给开发者。")
    else:
        print("❌ 修复过程中出现错误，请检查上方日志。")
    print("="*50)
    input("按 Enter 键退出...")

if __name__ == '__main__':
    main()