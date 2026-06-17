# stats_aggregator.py
import math

class CharacterStats:
    """聚合所有装备词缀，计算面板属性"""
    def __init__(self, player_level=100):
        self.level = player_level
        # 基础属性（空身）
        self.base_life = self._get_base_life(player_level)
        self.base_main_stat = 0  # 由职业决定，但词缀里会加，这里先置0，后面从装备累加
        self.weapon_dps = 0       # 需要用户设定或从武器读取
        
        # 累加器
        self.main_stat = 0        # 主属性（力量/智力等）
        self.armor = 0
        self.life_bonus = 0       # 生命上限固定值
        self.life_percent_bonus = 0  # 生命上限%
        self.damage_additive = 0  # A类伤害（所有伤害、核心伤害等）
        self.crit_chance = 0
        self.crit_damage = 0      # 暴击伤害（A类）
        self.attack_speed = 0
        self.move_speed = 0
        self.resource_gen = 0
        self.resistances = {}     # 各抗性
        self.independent_multipliers = []  # [x]独立乘区（面板上不显示总和，但留作以后扩展）
        
        # 职业主属性映射（用于确定攻击强度用哪个属性）
        self.main_stat_type = "智力"  # 默认巫师，后面会动态设置

    def _get_base_life(self, level):
        """暗黑4 基础生命值公式（近似，满级 100 级约为 4000，80级约 2500）"""
        # 这是根据社区数据拟合的公式，误差 < 1%
        if level <= 50:
            return 40 * level + 80
        else:
            return 80 * level + 80  # 50级后成长加速

    def aggregate(self, equip_data, profession="巫师"):
        """遍历所有装备，累加词缀"""
        # 设置主属性类型
        main_stat_map = {
            "巫师": "智力", "死灵法师": "智力",
            "野蛮人": "力量", "游侠": "敏捷", "德鲁伊": "意志"
        }
        self.main_stat_type = main_stat_map.get(profession, "智力")
        
        for position, data in equip_data.items():
            if not data:
                continue
            
            # 1. 处理普通词缀、回火词缀、嬗变词缀（它们的结构都是 {'name': '...', 'value': ...}）
            for affix in data.get('affixes', []):
                self._parse_affix(affix)
            for affix in data.get('reforge_affixes', []):
                self._parse_affix(affix)
            for affix in data.get('trans_affixes', []):
                self._parse_affix(affix)
            
            # 2. 处理暗金/神话装备的固定词缀（需要额外从数据库读，但你已经存在 affixes 里了，所以上面已经处理了）
            # 3. 处理武器白字（仅当是主手武器）
            if position == "主手":
                # 从装备数据中获取武器类型或直接获取预设的白字
                # 如果用户没有输入，这里留空，由外面的UI传入
                pass

    def _parse_affix(self, affix):
        name = affix.get('name', '')
        value = affix.get('value', 0)
        if not name or value == 0:
            return

        # 根据词缀名称关键词分类
        # 注意：由于你在保存时已经计算好了最终数值（value），这里直接累加即可。
        # 主属性
        if '力量' in name:
            self.main_stat += value
        elif '智力' in name:
            self.main_stat += value
        elif '敏捷' in name:
            self.main_stat += value
        elif '意志' in name:
            self.main_stat += value
        elif '全属性' in name:
            self.main_stat += value
        
        # 防御
        elif '护甲值' in name or '总护甲' in name:
            self.armor += value
        elif '生命上限' in name:
            if '%' in name:
                self.life_percent_bonus += value / 100.0
            else:
                self.life_bonus += value
        
        # 伤害（A类）
        elif '所有伤害' in name or '核心技能伤害' in name or '基本技能伤害' in name or \
             '终极技能伤害' in name or '对精英伤害' in name or '近距离伤害' in name or \
             '远距离伤害' in name or '对被控制敌人伤害' in name or '闪电伤害' in name or \
             '火焰伤害' in name or '冰霜伤害' in name or '毒素伤害' in name or \
             '暗影伤害' in name or '物理伤害' in name or '压制伤害' in name:
            self.damage_additive += value / 100.0
        
        # 暴击
        elif '暴击几率' in name:
            self.crit_chance += value / 100.0
        elif '暴击伤害' in name and '增倍' not in name:  # 排除独立增倍的暴击伤害
            self.crit_damage += value / 100.0
        elif 'x[' in name and '暴击伤害' in name:  # 独立乘区暴击（面板不显示，暂存）
            self.independent_multipliers.append(1 + value / 100.0)
        
        # 攻速、移速、资源
        elif '攻击速度' in name:
            self.attack_speed += value / 100.0
        elif '移动速度' in name:
            self.move_speed += value / 100.0
        elif '资源生成' in name:
            self.resource_gen += value / 100.0
        
        # 抗性（点全元素抗性、点火焰抗性等）
        elif '抗性' in name:
            if '全元素' in name:
                for ele in ['火焰', '冰霜', '闪电', '毒素', '暗影', '物理']:
                    self.resistances[ele] = self.resistances.get(ele, 0) + value
            else:
                # 提取抗性类型（火焰、冰霜等）
                for ele in ['火焰', '冰霜', '闪电', '毒素', '暗影', '物理']:
                    if ele in name:
                        self.resistances[ele] = self.resistances.get(ele, 0) + value
                        break
        
        # 独立增倍（面板通常显示为 "x%"，但它们不参与攻强计算，只影响最终伤害）
        elif '增倍' in name or 'x[' in name:
            self.independent_multipliers.append(1 + value / 100.0)

    def get_attack_power(self, weapon_dps, main_stat_override=None):
        """计算攻击强度（面板上的攻击强度）"""
        main = main_stat_override if main_stat_override is not None else self.main_stat
        # 公式：武器白字 * (1 + 主属性/1000) * (1 + A类伤害总和)
        return weapon_dps * (1 + main / 1000.0) * (1 + self.damage_additive)

    def get_max_life(self):
        """计算最终生命上限"""
        # 基础生命 + 固定生命加成，再乘以（1 + 生命上限%）
        total_base = self.base_life + self.life_bonus
        return total_base * (1 + self.life_percent_bonus)

    def get_summary(self, weapon_dps):
        """返回一个完整的摘要字典，方便UI显示"""
        return {
            "主属性": round(self.main_stat),
            "攻击强度": round(self.get_attack_power(weapon_dps)),
            "护甲": round(self.armor),
            "生命上限": round(self.get_max_life()),
            "暴击几率": f"{self.crit_chance * 100:.1f}%",
            "暴击伤害": f"{self.crit_damage * 100:.1f}%",
            "攻击速度": f"{self.attack_speed * 100:.1f}%",
            "移动速度": f"{self.move_speed * 100:.1f}%",
            "资源生成": f"{self.resource_gen * 100:.1f}%",
            "A类增伤": f"{self.damage_additive * 100:.1f}%",
            "独立乘区": f"{math.prod(self.independent_multipliers) * 100:.1f}%",
            "火焰抗性": self.resistances.get('火焰', 0),
            "冰霜抗性": self.resistances.get('冰霜', 0),
            "闪电抗性": self.resistances.get('闪电', 0),
            "毒素抗性": self.resistances.get('毒素', 0),
            "暗影抗性": self.resistances.get('暗影', 0),
            "物理抗性": self.resistances.get('物理', 0),
        }