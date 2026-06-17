# -*- coding: utf-8 -*-
# 模块: business/skill_tree

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

from config import resource_path  # 修改：从 config 导入 resource_path

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