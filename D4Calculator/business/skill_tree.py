# -*- coding: utf-8 -*-
# 模块: business/skill_tree

import json
import os
import re
import logging
from config import resource_path


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
        self._load_data()

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

        profession_map = {
            '巫师': 'Sorcerer',
            '野蛮人': 'Barbarian',
            '德鲁伊': 'Druid',
            '游侠': 'Rogue',
            '死灵法师': 'Necromancer',
            '灵巫': 'Spiritborn',
            '圣骑士': 'Paladin',
            '术士': 'Warlock'
        }
        target_char = profession_map.get(self.profession, self.profession)

        for skill in skills_list:
            char = skill.get('char', '')
            if char and char != target_char:
                continue
            skill_id = skill.get('id')
            if skill_id is None:
                continue

            self.skill_data[skill_id] = {
                'id': skill_id,
                'key': skill.get('key', ''),
                'name': skill.get('name', ''),
                'active': skill.get('active', False),
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

    def _safe_convert(self, skill_key):
        if skill_key is None:
            return None
        if isinstance(skill_key, int):
            return skill_key
        if isinstance(skill_key, str):
            try:
                return int(skill_key)
            except ValueError:
                pass
            skill = self._find_skill(skill_key)
            if skill:
                return skill['id']
        logging.warning(f"无法转换 skill_key: {skill_key} (类型: {type(skill_key)})")
        return None

    def _find_skill(self, skill_key):
        if skill_key is None:
            return None
        if isinstance(skill_key, int):
            return self.skill_data.get(skill_key)
        str_key = str(skill_key)
        for sid, skill in self.skill_data.items():
            if str(skill.get('key')) == str_key:
                return skill
            if str(skill.get('icon')) == str_key:
                return skill
            if str(skill.get('id')) == str_key:
                return skill
            if skill.get('name') == str_key:
                return skill
        return None

    def get_base_level(self, skill_key):
        sk = self._safe_convert(skill_key)
        return self.skill_levels.get(sk, 0) if sk is not None else 0

    def get_total_level(self, skill_key):
        sk = self._safe_convert(skill_key)
        if sk is None:
            return 0
        base = self.get_base_level(sk)
        extra = self.external_bonuses['global'].get('all_skills', 0)
        skill = self._find_skill(sk)
        if skill:
            for tag in skill.get('tags', []):
                if '火焰' in tag or 'Fire' in tag:
                    extra += self.external_bonuses['global'].get('fire_skills', 0)
                elif '冰霜' in tag or 'Frost' in tag:
                    extra += self.external_bonuses['global'].get('frost_skills', 0)
                elif '闪电' in tag or 'Shock' in tag:
                    extra += self.external_bonuses['global'].get('shock_skills', 0)
        extra += self.external_bonuses['specific'].get(sk, {}).get('level', 0)
        return base + extra

    def can_add_level(self, skill_key):
        sk = self._safe_convert(skill_key)
        if sk is None:
            return False
        skill = self._find_skill(sk)
        if not skill:
            return False
        if self.available_points <= 0:
            return False
        if self.get_base_level(sk) >= skill.get('base_max_level', 15):
            return False
        return True

    def add_level(self, skill_key):
        # ----- 安全转换 -----
        if skill_key is None:
            return False
        if not isinstance(skill_key, int):
            skill = self._find_skill(skill_key)
            if skill:
                skill_key = skill['id']
            else:
                try:
                    skill_key = int(skill_key)
                except (ValueError, TypeError):
                    return False
        # -------------------
        sk = self._safe_convert(skill_key)
        if sk is None or not self.can_add_level(sk):
            return False
        self.skill_levels[sk] = self.skill_levels.get(sk, 0) + 1
        self.available_points -= 1
        self._notify_change()
        return True

    def remove_level(self, skill_key):
        # ----- 安全转换 -----
        if skill_key is None:
            return False
        if not isinstance(skill_key, int):
            skill = self._find_skill(skill_key)
            if skill:
                skill_key = skill['id']
            else:
                try:
                    skill_key = int(skill_key)
                except (ValueError, TypeError):
                    return False
        # -------------------
        sk = self._safe_convert(skill_key)
        if sk is None or self.get_base_level(sk) <= 0:
            return False
        self.skill_levels[sk] -= 1
        self.available_points += 1
        if self.skill_levels[sk] == 0:
            self.branch_levels.pop(sk, None)
        self._notify_change()
        return True

    def can_activate_branch(self, skill_key, branch_id):
        sk = self._safe_convert(skill_key)
        if sk is None:
            return False
        if self.branch_levels.get(sk, {}).get(branch_id, 0) >= 1:
            return False
        if self.available_points <= 0:
            return False
        return True

    def activate_branch(self, skill_key, branch_id):
        sk = self._safe_convert(skill_key)
        if sk is None or not self.can_activate_branch(sk, branch_id):
            return False
        self.branch_levels.setdefault(sk, {})[branch_id] = 1
        self.available_points -= 1
        self._notify_change()
        return True

    def deactivate_branch(self, skill_key, branch_id):
        sk = self._safe_convert(skill_key)
        if sk is None:
            return False
        if self.branch_levels.get(sk, {}).get(branch_id, 0) == 0:
            return False
        self.branch_levels.setdefault(sk, {}).pop(branch_id, None)
        self.available_points += 1
        self._notify_change()
        return True

    def evaluate_formula(self, formula_str, level):
        try:
            return eval(formula_str, {"level": level, "__builtins__": {}})
        except:
            return 0.0

    def get_skill_display_info(self, skill_key):
        if isinstance(skill_key, dict) and 'mod_data' in skill_key:
            mod_data = skill_key['mod_data']
            mod_name = mod_data.get('name', '未命名分支')
            mod_desc = ' '.join(mod_data.get('desc', ['']))
            mod_desc = re.sub(r'\{c_[^}]+\}|{/c}', '', mod_desc)
            return {
                'name': mod_name,
                'icon': mod_data.get('icon'),
                'base_level': 0,
                'total_level': 0,
                'extra_level': 0,
                'max_level': 1,
                'tags': [],
                'damage_type': '',
                'description': mod_desc,
                'active_branches': {},
                'mod_data': mod_data,
            }

        sk = self._safe_convert(skill_key)
        if sk is None:
            return {
                'name': f"未知技能 ({skill_key})",
                'icon': None,
                'base_level': 0,
                'total_level': 0,
                'extra_level': 0,
                'max_level': 0,
                'tags': [],
                'damage_type': '',
                'description': '未找到技能数据',
                'active_branches': {},
            }

        skill = self._find_skill(sk)
        if not skill:
            return {
                'name': f"未知技能 ({sk})",
                'icon': None,
                'base_level': 0,
                'total_level': 0,
                'extra_level': 0,
                'max_level': 0,
                'tags': [],
                'damage_type': '',
                'description': '未找到技能数据',
                'active_branches': {},
            }

        base_level = self.get_base_level(sk)
        total_level = self.get_total_level(sk)
        extra_level = total_level - base_level
        max_level = skill.get('base_max_level', 15)

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

        base_desc = skill.get('desc_template', '')
        for k, v in vals.items():
            if isinstance(v, (int, float)):
                if isinstance(v, float) and v.is_integer():
                    base_desc = base_desc.replace(f'{{{k}}}', str(int(v)))
                else:
                    base_desc = base_desc.replace(f'{{{k}}}', f"{v:.1f}")
            else:
                base_desc = base_desc.replace(f'{{{k}}}', str(v))

        desc_parts = [base_desc]
        enchant = skill.get('enchant_desc', '')
        if enchant:
            desc_parts.append(f"附魔：{enchant}")

        if skill.get('active', False):
            active_branches = self.branch_levels.get(sk, {})
            if active_branches:
                branch_lines = []
                mods = skill.get('mods', [])
                for mod in mods:
                    mod_id = mod.get('id') or mod.get('modId')
                    if mod_id is None:
                        continue
                    mod_id_str = str(mod_id)
                    if mod_id_str in active_branches and active_branches[mod_id_str] > 0:
                        name = mod.get('name', '')
                        desc_lines = mod.get('desc', [])
                        mod_desc = ' '.join(desc_lines)
                        mod_desc = re.sub(r'\{c_[^}]+\}|{/c}', '', mod_desc)
                        if name and mod_desc:
                            branch_lines.append(f"{name}: {mod_desc}")
                        elif name:
                            branch_lines.append(name)
                        else:
                            branch_lines.append(mod_desc or '分支')
                if branch_lines:
                    desc_parts.append("激活分支效果：")
                    desc_parts.append("\n".join(branch_lines))

        final_desc = "\n\n".join(desc_parts)

        tags = skill.get('tags', [])
        if sk in self.external_bonuses['specific']:
            tags_change = self.external_bonuses['specific'][sk].get('tags_change', {})
            for old, new in tags_change.items():
                if old in tags:
                    tags = [new if t == old else t for t in tags]

        return {
            'name': skill['name'],
            'icon': skill.get('icon'),
            'base_level': base_level,
            'total_level': total_level,
            'extra_level': extra_level,
            'max_level': max_level,
            'tags': tags,
            'damage_type': skill.get('damage_type', ''),
            'description': final_desc,
            'active_branches': {bid: lvl for bid, lvl in self.branch_levels.get(sk, {}).items() if lvl > 0},
        }

    def update_external_bonuses(self, bonus_data):
        if 'global' in bonus_data:
            for k, v in bonus_data['global'].items():
                self.external_bonuses['global'][k] = self.external_bonuses['global'].get(k, 0) + v
        if 'specific' in bonus_data:
            for skill_key, data in bonus_data['specific'].items():
                sk = self._safe_convert(skill_key)
                if sk is None:
                    continue
                if sk not in self.external_bonuses['specific']:
                    self.external_bonuses['specific'][sk] = {}
                for k, v in data.items():
                    self.external_bonuses['specific'][sk][k] = v
        self._notify_change()

    def reset_external_bonuses(self):
        self.external_bonuses = {
            "global": {"all_skills": 0, "fire_skills": 0, "frost_skills": 0, "shock_skills": 0},
            "specific": {}
        }
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