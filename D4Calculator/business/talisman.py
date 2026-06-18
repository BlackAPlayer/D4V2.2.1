# -*- coding: utf-8 -*-
# 模块: business/talisman.py
# 护身符系统核心业务逻辑

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
import json
import os
import re
import logging


@dataclass
class SocketedRune:
    """已镶嵌的神符数据"""
    slot_index: int
    rune_id: str
    name: str
    rarity: str  # set / unique / mythic_unique
    affixes: List[Dict]  # 2条词缀
    set_id: Optional[str] = None
    set_tiers: Dict[str, str] = field(default_factory=dict)
    power_reference: Optional[Dict] = None


class TalismanSystem:
    """
    护身符系统核心业务逻辑
    管理封印装备、神符镶嵌、套装检测、词缀汇总
    """

    def __init__(self, skill_system=None, callback=None):
        self.skill_system = skill_system
        self.callback = callback

        self._seal_db: Dict[str, Dict] = {}
        self._rune_db: Dict[str, Dict] = {}

        self.active_class: Optional[str] = None
        self.current_seal: Optional[Dict] = None
        self.sockets: Dict[int, SocketedRune] = {}

        self._set_requirement_reduction: int = 0
        self._socket_count_override: Optional[int] = None
        self._unique_limit_override: Optional[int] = None
        self._dynamic_socket_count: int = 0

        self._last_error: str = ""

    def load_data(self, seals: Dict, runes: Dict):
        self._seal_db = seals.get('seals', {})
        self._rune_db = runes.get('runes', {})
        logging.info("护身符数据加载完成: 封印 %d 个, 神符 %d 个",
                     len(self._seal_db), len(self._rune_db))

    def set_active_class(self, class_name: str):
        if self.active_class != class_name:
            self.active_class = class_name
            self.sockets.clear()
            self.current_seal = None
            self._reset_system_modifiers()
            self._dynamic_socket_count = 0
            self._notify_change()

    def get_available_seals(self) -> List[Dict]:
        if not self.active_class:
            return list(self._seal_db.values())
        available = []
        for seal in self._seal_db.values():
            restriction = seal.get('class_restriction')
            if restriction is None or self.active_class in restriction:
                available.append(seal)
        return available

    def equip_seal(self, seal_id: Optional[str]) -> bool:
        if seal_id is None:
            self.current_seal = None
            self.sockets.clear()
            self._reset_system_modifiers()
            self._dynamic_socket_count = 0
            self._notify_change()
            return True

        seal_data = self._seal_db.get(seal_id)
        if not seal_data:
            self._last_error = "封印不存在"
            return False

        restriction = seal_data.get('class_restriction')
        if restriction and self.active_class not in restriction:
            self._last_error = f"该封印不适用于 {self.active_class}"
            return False

        self.current_seal = seal_data
        self._reset_system_modifiers()

        seal_affix = seal_data.get('seal_affix')
        if seal_affix and seal_affix.get('type') == 'system_modifier':
            self._apply_system_modifier(seal_affix)

        for affix in seal_data.get('set_affixes', []):
            if affix.get('type') == 'system_modifier':
                self._apply_system_modifier(affix)

        base_slots = seal_data.get('slots_base', 6)
        if self._socket_count_override is not None:
            self._dynamic_socket_count = self._socket_count_override
        else:
            self._dynamic_socket_count = base_slots + self._get_socket_bonus_from_affixes(seal_data)

        self.sockets.clear()
        self._notify_change()
        return True

    def _reset_system_modifiers(self):
        self._set_requirement_reduction = 0
        self._socket_count_override = None
        self._unique_limit_override = None

    def _apply_system_modifier(self, affix: Dict):
        modifier_type = affix.get('modifier_type')
        value = affix.get('value')

        if modifier_type == 'set_requirement_reduction':
            self._set_requirement_reduction += value
        elif modifier_type == 'socket_and_unique_override':
            if isinstance(value, dict):
                if 'socket_count' in value:
                    self._socket_count_override = value['socket_count']
                if 'unique_limit' in value:
                    self._unique_limit_override = value['unique_limit']
        elif modifier_type == 'socket_increase':
            if isinstance(value, (int, float)):
                if self._socket_count_override is None:
                    base = self.current_seal.get('slots_base', 6)
                    self._socket_count_override = base + int(value)

    def _get_socket_bonus_from_affixes(self, seal_data: Dict) -> int:
        bonus = 0
        for affix in seal_data.get('set_affixes', []):
            if affix.get('modifier_type') == 'socket_increase':
                bonus += affix.get('value', 0)
        return bonus

    def get_available_runes(self) -> List[Dict]:
        if not self.active_class:
            return list(self._rune_db.values())
        available = []
        for rune in self._rune_db.values():
            restriction = rune.get('class_restriction')
            if restriction is None or self.active_class in restriction:
                available.append(rune)
        return available

    def socket_rune(self, slot_index: int, rune_id: str) -> bool:
        if not self.current_seal:
            self._last_error = "请先装备封印"
            return False

        if slot_index >= self._dynamic_socket_count:
            self._last_error = f"插槽 {slot_index+1} 超出可用范围"
            return False

        if slot_index in self.sockets:
            self._last_error = "该插槽已被占用"
            return False

        rune_data = self._rune_db.get(rune_id)
        if not rune_data:
            self._last_error = "神符不存在"
            return False

        restriction = rune_data.get('class_restriction')
        if restriction and self.active_class not in restriction:
            self._last_error = f"该神符不适用于 {self.active_class}"
            return False

        rune_name = rune_data.get('name')
        for existing in self.sockets.values():
            if existing.name == rune_name:
                self._last_error = f"同名神符 '{rune_name}' 已镶嵌，不能重复"
                return False

        rarity = rune_data.get('rarity')
        if rarity in ('unique', 'mythic_unique'):
            current_unique = sum(1 for r in self.sockets.values()
                                 if r.rarity in ('unique', 'mythic_unique'))
            limit = self._unique_limit_override if self._unique_limit_override is not None else 1
            if current_unique >= limit:
                self._last_error = f"暗金神符已达上限 ({limit}个)"
                return False

        rune_obj = SocketedRune(
            slot_index=slot_index,
            rune_id=rune_id,
            name=rune_data.get('name', '未知'),
            rarity=rarity,
            affixes=rune_data.get('affixes', []),
            set_id=rune_data.get('set_id'),
            set_tiers=rune_data.get('set_tiers', {}),
            power_reference=rune_data.get('power_reference')
        )

        self.sockets[slot_index] = rune_obj
        self._notify_change()
        return True

    def remove_rune(self, slot_index: int) -> bool:
        if slot_index not in self.sockets:
            self._last_error = "该插槽为空"
            return False

        del self.sockets[slot_index]
        self._notify_change()
        return True

    def get_last_error(self) -> str:
        return self._last_error

    def get_available_slots(self) -> int:
        return self._dynamic_socket_count

    def get_required_count_for_tier(self, tier: int) -> int:
        required = tier - self._set_requirement_reduction
        return max(2, required)

    def get_active_set_bonuses(self) -> Dict[str, List[str]]:
        set_counts: Dict[str, int] = {}
        set_tiers_map: Dict[str, Dict[str, str]] = {}

        for rune in self.sockets.values():
            if rune.set_id:
                set_counts[rune.set_id] = set_counts.get(rune.set_id, 0) + 1
                if rune.set_id not in set_tiers_map:
                    set_tiers_map[rune.set_id] = rune.set_tiers

        result: Dict[str, List[str]] = {}
        for set_id, count in set_counts.items():
            tiers = set_tiers_map.get(set_id, {})
            active_descs = []

            if count >= self.get_required_count_for_tier(5) and '5' in tiers:
                active_descs.append(f"(5) {tiers['5']}")
            if count >= self.get_required_count_for_tier(3) and '3' in tiers:
                active_descs.append(f"(3) {tiers['3']}")
            if count >= self.get_required_count_for_tier(2) and '2' in tiers:
                active_descs.append(f"(2) {tiers['2']}")

            if active_descs:
                result[set_id] = active_descs

        return result

    def get_seal_affix_modifiers(self) -> Dict[str, float]:
        modifiers: Dict[str, float] = {}
        if not self.current_seal:
            return modifiers

        for affix in self.current_seal.get('set_affixes', []):
            self._apply_affix_to_modifiers(modifiers, affix)

        seal_affix = self.current_seal.get('seal_affix')
        if seal_affix:
            self._apply_affix_to_modifiers(modifiers, seal_affix)

        return modifiers

    def get_rune_affix_modifiers(self) -> Dict[str, float]:
        modifiers: Dict[str, float] = {}
        for rune in self.sockets.values():
            for affix in rune.affixes:
                self._apply_affix_to_modifiers(modifiers, affix)
        return modifiers

    def get_total_modifiers(self) -> Dict[str, float]:
        total: Dict[str, float] = {}
        total.update(self.get_seal_affix_modifiers())
        total.update(self.get_rune_affix_modifiers())
        return total

    def _apply_affix_to_modifiers(self, modifiers: Dict[str, float], affix: Dict):
        affix_type = affix.get('type')
        target = affix.get('target')
        value = affix.get('value', 0)

        if affix_type == 'stat_bonus' and target:
            modifiers[target] = modifiers.get(target, 0) + value
        elif affix_type == 'skill_rank' and target:
            modifiers[target] = modifiers.get(target, 0) + value
        elif affix_type == 'conditional_damage':
            condition = affix.get('condition', '')
            if condition:
                key = f"conditional_{condition}"
                modifiers[key] = modifiers.get(key, 0) + value

    def update_skill_bonuses(self):
        """更新技能树的外部加成（精确解析 skill_rank 词缀，先重置再应用）"""
        if not self.skill_system:
            return

        modifiers = self.get_total_modifiers()
        specific: Dict[str, int] = {}
        all_skills_bonus = 0

        for key, value in modifiers.items():
            if key == "all_skills":
                all_skills_bonus = int(value)
                continue

            if "_" in key and not key.startswith(("conditional_", "set_")):
                specific[key] = int(value) if isinstance(value, float) and value.is_integer() else value

        bonus = {
            'global': {
                'all_skills': all_skills_bonus,
                'fire_skills': int(modifiers.get('fire_skills', 0)),
                'frost_skills': int(modifiers.get('frost_skills', 0)),
                'shock_skills': int(modifiers.get('shock_skills', 0)),
            },
            'specific': specific
        }

        self.skill_system.reset_external_bonuses()
        self.skill_system.update_external_bonuses(bonus)

    def _notify_change(self):
        self.update_skill_bonuses()
        if self.callback:
            self.callback()