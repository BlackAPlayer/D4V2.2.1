# -*- coding: utf-8 -*-
# 模块: ui/skill_tree_ui

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

from config import resource_path
from data.loader import load_photo_image

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

        # 背景相关
        self.bg_image = None
        self.bg_photo = None
        self._load_background_image()

        self.zoom = 1.0
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.view_x = 0.0
        self.view_y = 0.0

        self.nodes = []
        self.edges = []
        self.line_style = {}
        self.node_refs = {}
        self.background_margin = 500

        # 标志：首次绘制是否完成
        self._first_draw_done = False

        # 绑定 Configure 事件（用于首次绘制和后续 resize）
        self.canvas.bind('<Configure>', self._on_canvas_configure)

        self._load_layout(layout_file)

        self.canvas.bind('<ButtonPress-1>', self._on_drag_start)
        self.canvas.bind('<B1-Motion>', self._on_drag_move)
        self.canvas.bind('<MouseWheel>', self._on_mousewheel)
        self.canvas.bind('<Button-4>', self._on_mousewheel)
        self.canvas.bind('<Button-5>', self._on_mousewheel)

        self.skill_system.add_listener(self.refresh)
        self.refresh()

        # 延迟检查以确保标签页可见时绘制
        self.canvas.after(100, self._check_and_draw)

    def _check_and_draw(self):
        """延迟检查画布尺寸，确保标签页可见时触发绘制"""
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w > 1 and h > 1:
            if not self._first_draw_done:
                print("[DEBUG] 延迟检查触发首次绘制")
                self._on_first_draw()
        else:
            if not hasattr(self, '_check_count'):
                self._check_count = 0
            self._check_count += 1
            if self._check_count < 50:
                self.canvas.after(100, self._check_and_draw)
            else:
                print("[DEBUG] 检查超时，强制绘制（可能存在布局问题）")
                self._on_first_draw()

    def _on_canvas_configure(self, event):
        """画布尺寸变化事件（包括首次布局）"""
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w > 1 and h > 1:
            if not self._first_draw_done:
                self._on_first_draw()
            else:
                # 后续 resize 重绘
                self._redraw_all()

    def _on_first_draw(self):
        """首次有效绘制"""
        print(f"[DEBUG] 首次绘制，画布尺寸 {self.canvas.winfo_width()}x{self.canvas.winfo_height()}")
        self._first_draw_done = True
        self._redraw_all()

    def _load_background_image(self):
        """加载默认背景图（作为回退）"""
        bg_path = resource_path('images/skill_bg.png')
        if os.path.exists(bg_path):
            try:
                self.bg_image = Image.open(bg_path)
                self.bg_photo = None
                print(f"[DEBUG] 默认背景图加载成功: {bg_path}，尺寸 {self.bg_image.size}")
                logging.info("默认背景图加载成功: %s", bg_path)
            except Exception as e:
                self.bg_image = None
                print(f"[DEBUG] 默认背景图加载失败: {e}")
                logging.warning("默认背景图加载失败: %s", e)
        else:
            self.bg_image = None
            print(f"[DEBUG] 默认背景图文件不存在: {bg_path}")
            logging.warning("默认背景图文件不存在: %s", bg_path)

    def _load_background_image_from_path(self, path):
        if not path:
            self._load_background_image()
            return
        full_path = resource_path(path)
        if os.path.exists(full_path):
            try:
                self.bg_image = Image.open(full_path)
                self.bg_photo = None
                print(f"[DEBUG] 从布局路径加载背景图成功: {full_path}")
                logging.info("从布局路径加载背景图成功: %s", full_path)
                return
            except Exception as e:
                print(f"[DEBUG] 加载路径背景图失败: {e}")
                logging.warning("加载路径背景图失败: %s", e)
        print(f"[DEBUG] 背景图不存在或无法加载: {full_path}，回退到默认背景")
        logging.warning("背景图不存在或无法加载: %s，回退到默认背景", full_path)
        self._load_background_image()

    def _load_layout(self, layout_file):
        full_path = resource_path(layout_file)
        if not os.path.exists(full_path):
            logging.warning("布局文件不存在，使用自动布局")
            self._auto_layout()
            return
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            logging.warning("布局文件解析失败: %s", e)
            self._auto_layout()
            return

        if isinstance(data, dict):
            self.background_margin = data.get('backgroundMargin', 250)
            logging.info("背景图边距设置为: %d", self.background_margin)
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
        unmatched = []

        for nd in nodes_data:
            skill_id = nd.get('skill_id') or nd.get('skillKey')
            branch_skill = nd.get('branch_skill') or nd.get('branchSkill')
            branch_id = nd.get('branch_id') or nd.get('branchId')
            icon_id = nd.get('iconId')
            x = nd.get('left') or nd.get('x')
            y = nd.get('top') or nd.get('y')
            if x is None or y is None:
                continue
            if skill_id is None:
                node = {
                    'id': nd.get('id'),
                    'skill_key': None,
                    'skill': None,
                    'x': x,
                    'y': y,
                    'type': nd.get('type', 'skill'),
                    'internal_id': f"branch_{x}_{y}",
                    'branch_skill': branch_skill,
                    'branch_id': branch_id,
                    'icon_id': icon_id,
                    'borderImage': nd.get('borderImage'),
                    'isPassive': nd.get('isPassive', False),
                }
                self.nodes.append(node)
                continue
            skill = self.skill_system.skill_data.get(skill_id)
            if skill is None:
                unmatched.append(skill_id)
            node = {
                'id': nd.get('id'),
                'skill_key': skill_id if skill else None,
                'skill': skill,
                'x': x,
                'y': y,
                'type': nd.get('type', 'skill'),
                'internal_id': skill_id if skill_id else f"token_{x}_{y}",
                'branch_skill': branch_skill,
                'branch_id': branch_id,
                'icon_id': icon_id,
                'borderImage': nd.get('borderImage'),
                'isPassive': nd.get('isPassive', False),
            }
            self.nodes.append(node)

        if unmatched:
            logging.info("未匹配 %d 个技能节点，示例：%s", len(unmatched), unmatched[:10])
        logging.info("成功加载 %d 个技能节点，%d 条连线", len(self.nodes), len(self.edges))

        # 不直接绘制，由 Configure 事件或延迟检查触发

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
                        'internal_id': key if key else f"auto_{x}_{current_y+row*row_height}",
                        'branch_skill': None,
                        'branch_id': None,
                        'icon_id': None,
                        'borderImage': None,
                        'isPassive': False,
                    })
                    node_id += 1
                    x += col_width
            current_y += row_count * row_height + 40
        # 不直接绘制，等待事件

    def _get_icon_path(self, skill_key, skill, icon_id=None):
        if skill_key:
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
        if skill and skill.get('icon'):
            icon_path = resource_path(f'images/icons/{skill["icon"]}.png')
            if os.path.exists(icon_path):
                return icon_path
        return None

    def _draw_edges(self):
        if not self.edges:
            return
        self._draw_solid_edges()

    def _draw_solid_edges(self):
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
            # 直接使用世界坐标
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
        """完整重绘：先设视口，再绘制，最后扩展视口包含背景"""
        self.canvas.delete('all')
        self.canvas.update_idletasks()

        # 1. 先建立基于节点的 scrollregion
        self._update_viewport(center=True)

        # 2. 绘制所有内容
        self._draw_background()
        self._draw_edges()
        self._draw_all_nodes()

        self.canvas.tag_lower('bg')
        self.canvas.tag_raise('edge')
        self.canvas.tag_raise('node')

        # 3. 扩展 scrollregion 包含背景图区域（但不再居中）
        self._update_viewport(center=False)

        print("[DEBUG] 重绘完成")

    def _update_viewport(self, center=True):
        if not self.nodes:
            return
        xs = [n['x'] for n in self.nodes]
        ys = [n['y'] for n in self.nodes]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        min_y -= 500
        max_y += 500

        margin = self.background_margin
        left = min_x - margin
        top = min_y - margin
        right = max_x + margin
        bottom = max_y + margin

        if hasattr(self, 'bg_left'):
            left = min(left, self.bg_left)
            top = min(top, self.bg_top)
            right = max(right, self.bg_left + self.bg_width)
            bottom = max(bottom, self.bg_top + self.bg_height)

        self.canvas.config(scrollregion=(left, top, right, bottom))

        if center:
            cw = self.canvas.winfo_width()
            ch = self.canvas.winfo_height()
            if cw > 1 and ch > 1 and (right - left) > 0 and (bottom - top) > 0:
                center_x = (min_x + max_x) / 2
                center_y = (min_y + max_y) / 2
                self.canvas.xview_moveto((center_x - left - cw/2) / (right-left))
                self.canvas.yview_moveto((center_y - top - ch/2) / (bottom-top))
            self.view_x = self.canvas.xview()[0]
            self.view_y = self.canvas.yview()[0]

    def _draw_background(self):
        """绘制背景图（使用世界坐标，随滚动/缩放自动适配）"""
        if not self.bg_image:
            print("[DEBUG] _draw_background: 背景图为空，跳过")
            return

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w <= 1 or h <= 1:
            print(f"[DEBUG] _draw_background: 画布尺寸 {w}x{h} 无效，跳过")
            return

        img_w, img_h = self.bg_image.size
        if img_w <= 0 or img_h <= 0:
            print("[DEBUG] _draw_background: 图片尺寸无效")
            return

        # ---- 无节点：居中绘制（屏幕坐标） ----
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
            print(f"[DEBUG] 无节点背景绘制完成，位置 ({offset_x}, {offset_y})，尺寸 {draw_w}x{draw_h}")
            return

        # ---- 有节点：基于节点边界 + 边距（世界坐标） ----
        xs = [n['x'] for n in self.nodes]
        ys = [n['y'] for n in self.nodes]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)

        min_y -= 500
        max_y += 500

        margin = self.background_margin
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        width = max_x - min_x + 2 * margin
        height = max_y - min_y + 2 * margin

        if width <= 0 or height <= 0:
            print("[DEBUG] _draw_background: 计算的宽度或高度 <= 0")
            return

        left = center_x - width / 2
        top = center_y - height / 2

        # 调试输出
        print(f"[DEBUG] 背景参数: 左={left}, 顶={top}, 宽={width}, 高={height}, 图片原始尺寸={img_w}x{img_h}")

        try:
            scaled = self.bg_image.resize((int(width), int(height)), Image.Resampling.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(scaled)
            self.canvas.create_image(left, top, image=self.bg_photo, anchor='nw', tags=('bg',))
            # 保存世界坐标边界
            self.bg_left = left
            self.bg_top = top
            self.bg_width = width
            self.bg_height = height
            print("[DEBUG] 背景图绘制成功（有节点）")
        except Exception as e:
            print(f"[DEBUG] 绘制背景图异常: {e}")

    def _draw_all_nodes(self):
        BASE_NODE_RADIUS = 32
        BASE_ICON_SIZE = 28
        self.node_refs.clear()

        if not hasattr(self, '_border_photos'):
            self._border_photos = []

        for node in self.nodes:
            x, y = node['x'], node['y']
            skill = node.get('skill')
            internal_id = node['internal_id']
            is_branch = node.get('branch_skill') is not None and node.get('branch_id') is not None
            icon_id = node.get('icon_id')

            is_passive = node.get('isPassive', False)
            passive_scale = 0.65 if is_passive else 1.0

            ICON_SIZE = BASE_ICON_SIZE * passive_scale
            BORDER_SIZE = int(ICON_SIZE * 1.6)
            NODE_RADIUS = BASE_NODE_RADIUS * passive_scale
            FONT_SIZE_NAME = int(12 * passive_scale)
            FONT_SIZE_LEVEL = int(8 * passive_scale)
            FONT_SIZE_BRANCH = int(12 * passive_scale)

            has_icon = False
            icon_path = None
            if not is_branch:
                icon_path = self._get_icon_path(node['skill_key'], skill, icon_id)
                if icon_path and os.path.exists(icon_path):
                    has_icon = True

            if is_branch:
                oval = self.canvas.create_oval(
                    x - NODE_RADIUS, y - NODE_RADIUS,
                    x + NODE_RADIUS, y + NODE_RADIUS,
                    fill='#1a3a5a', outline='#66CCFF', width=max(1, int(2 * passive_scale)),
                    tags=(internal_id, 'node')
                )
            else:
                oval = None

            border_img_obj = None
            border_image_path = node.get('borderImage')
            if border_image_path:
                full_path = resource_path(border_image_path)
                if os.path.exists(full_path):
                    photo = load_photo_image(full_path, size=(BORDER_SIZE, BORDER_SIZE))
                    if photo:
                        border_img_obj = self.canvas.create_image(x, y, image=photo, tags=(internal_id, 'node'))
                        self._border_photos.append(photo)

            icon_obj = None
            if is_branch:
                branches = self.skill_system.get_branches(node['branch_skill'])
                branch = branches.get(node['branch_id'])
                display_text = branch['name'][:2] if branch else 'BR'
                icon_obj = self.canvas.create_text(x, y, text=display_text, fill='#88CCFF',
                                                   font=('微软雅黑', int(FONT_SIZE_BRANCH), 'bold'),
                                                   tags=(internal_id, 'node'))
                is_active = self.skill_system.branch_levels.get(node['branch_skill'], {}).get(node['branch_id'], 0) > 0
                self.canvas.create_text(x, y + NODE_RADIUS + int(6 * passive_scale), text='✓' if is_active else '',
                                        fill='#88FF88', font=('微软雅黑', int(10 * passive_scale), 'bold'),
                                        tags=(internal_id, 'node'))
            else:
                if has_icon:
                    photo = load_photo_image(icon_path, size=(int(ICON_SIZE), int(ICON_SIZE)))
                    if photo:
                        icon_obj = self.canvas.create_image(x, y, image=photo,
                                                            tags=(internal_id, 'node'))
                if not icon_obj and skill:
                    text = skill['name'][:2]
                    icon_obj = self.canvas.create_text(x, y, text=text, fill='white',
                                                       font=('微软雅黑', int(FONT_SIZE_BRANCH), 'bold'),
                                                       tags=(internal_id, 'node'))
                elif not icon_obj and not skill:
                    icon_obj = self.canvas.create_text(x, y, text='?', fill='#888888',
                                                       font=('微软雅黑', int(FONT_SIZE_BRANCH + 2), 'bold'),
                                                       tags=(internal_id, 'node'))

            lv_bg = None
            lv_text = None
            if skill and skill.get('type') == 'active' and not is_branch and not is_passive:
                lv_bg = self.canvas.create_rectangle(
                    x + int(20 * passive_scale), y + int(20 * passive_scale),
                    x + NODE_RADIUS, y + NODE_RADIUS,
                    fill='#00000080', outline='',
                    tags=(internal_id, 'node')
                )
                lv_text = self.canvas.create_text(
                    x + int(26 * passive_scale), y + int(26 * passive_scale),
                    text='', fill='#88FF88',
                    font=('微软雅黑', int(FONT_SIZE_LEVEL), 'bold'), anchor='se',
                    tags=(internal_id, 'node')
                )

            hitbox = self.canvas.create_rectangle(
                x - NODE_RADIUS, y - NODE_RADIUS,
                x + NODE_RADIUS, y + NODE_RADIUS,
                fill='', outline='', tags=(internal_id, 'hitbox', 'node')
            )
            if is_branch:
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
                'icon': icon_obj,
                'lv_bg': lv_bg,
                'lv_text': lv_text,
                'hitbox': hitbox,
                'node': node,
                'is_branch': is_branch,
                'branch_skill': node.get('branch_skill'),
                'branch_id': node.get('branch_id'),
                'border_image': border_img_obj,
                'is_passive': is_passive,
            }

    def _on_drag_start(self, event):
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

    # ---------- 关键修正：缩放时保持鼠标焦点 ----------
    def _on_mousewheel(self, event):
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        if cw <= 1 or ch <= 1:
            return

        # 获取鼠标在世界坐标系中的位置（缩放前）
        world_x = self.canvas.canvasx(event.x)
        world_y = self.canvas.canvasy(event.y)

        # 计算缩放倍数
        if event.delta:
            delta = event.delta / 120
        else:
            if event.num == 4:
                delta = 1
            elif event.num == 5:
                delta = -1
            else:
                return
        scale = 1.1 ** delta
        new_zoom = self.zoom * scale
        if new_zoom < 0.2 or new_zoom > 3.0:
            return
        self.zoom = new_zoom

        # 以鼠标位置为中心缩放
        self.canvas.scale('node', world_x, world_y, scale, scale)
        self.canvas.scale('edge', world_x, world_y, scale, scale)
        self.canvas.scale('bg', world_x, world_y, scale, scale)

        # 更新滚动区域
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

        # 调整视图，使缩放前的 world_x, world_y 仍位于鼠标位置
        bbox = self.canvas.bbox('all')
        if bbox:
            left, top, right, bottom = bbox
            if right > left and bottom > top:
                # 计算目标视图偏移
                view_left = world_x - (event.x / cw) * (right - left)
                view_top = world_y - (event.y / ch) * (bottom - top)
                frac_x = (view_left - left) / (right - left)
                frac_y = (view_top - top) / (bottom - top)
                # 限制范围
                frac_x = max(0, min(1, frac_x))
                frac_y = max(0, min(1, frac_y))
                self.canvas.xview_moveto(frac_x)
                self.canvas.yview_moveto(frac_y)
                self.view_x = frac_x
                self.view_y = frac_y
    # ---------- 修正结束 ----------

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

    def _show_tooltip(self, event, skill_key):
        self._hide_tooltip()
        if not skill_key:
            return
        info = self.skill_system.get_skill_display_info(skill_key)
        if not info:
            return
        self.tooltip = tk.Toplevel(self.parent)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.geometry(f"+{event.x_root+15}+{event.y_root+15}")
        bg = '#1a1a1a'
        fg = '#DDDDDD'
        title_color = '#FFD700'
        frame = tk.Frame(self.tooltip, bg=bg, bd=1, relief='solid')
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        tk.Label(frame, text=info['name'], font=('微软雅黑', 12, 'bold'),
                 fg=title_color, bg=bg).pack(anchor='w')
        tk.Label(frame, text=f"等级: {info['base_level']} / {info['total_level']} (额外 +{info['extra_level']})",
                 font=('微软雅黑', 9), fg='#88FF88', bg=bg).pack(anchor='w')
        if info['tags']:
            tk.Label(frame, text=f"标签: {', '.join(info['tags'])}", font=('微软雅黑',8),
                     fg='#888888', bg=bg).pack(anchor='w')
        if info['damage_type']:
            tk.Label(frame, text=f"伤害类型: {info['damage_type']}", font=('微软雅黑',8),
                     fg='#888888', bg=bg).pack(anchor='w')
        tk.Frame(frame, height=1, bg='#333333').pack(fill=tk.X, pady=5)
        desc = info['description']
        if len(desc) > 300:
            desc = desc[:300] + '...'
        tk.Label(frame, text=desc, font=('微软雅黑', 9), fg=fg, bg=bg,
                 wraplength=280, justify='left').pack(anchor='w')

        if info['active_branches']:
            tk.Frame(frame, height=1, bg='#333333').pack(fill=tk.X, pady=3)
            tk.Label(frame, text="激活分支:", font=('微软雅黑', 9, 'bold'),
                     fg='#66CCFF', bg=bg).pack(anchor='w')
            for bid, lvl in info['active_branches'].items():
                branch = info['all_branches'].get(bid)
                if branch:
                    tk.Label(frame, text=f"  • {branch['name']}", font=('微软雅黑',9),
                             fg='#88CCFF', bg=bg).pack(anchor='w')
        self.tooltip.update_idletasks()
        x = event.x_root + 15
        y = event.y_root + 15
        w = self.tooltip.winfo_width()
        h = self.tooltip.winfo_height()
        screen_w = self.tooltip.winfo_screenwidth()
        screen_h = self.tooltip.winfo_screenheight()
        if x + w > screen_w:
            x = event.x_root - w - 15
        if y + h > screen_h:
            y = event.y_root - h - 15
        self.tooltip.geometry(f"+{x}+{y}")

    def _hide_tooltip(self, event=None):
        if hasattr(self, 'tooltip') and self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

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
                if not skill or skill.get('type') != 'active' or node.get('isPassive', False):
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