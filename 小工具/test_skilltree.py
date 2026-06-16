import tkinter as tk
from tkinter import ttk
import json
import os

# 模拟技能数据（直接内嵌，避免文件依赖）
SAMPLE_SKILLS = {
    "巫师": [
        {
            "id": "fire_bolt",
            "name": "火焰弹",
            "type": "基础",
            "max_level": 15,
            "unlock_level": 1,
            "description": "投掷一枚火焰弹，造成伤害并燃烧敌人。",
            "per_level_bonus": {"伤害": 0.1},
            "branch_groups": [
                {"type": "choice_2", "branches": ["b1", "b2"]},
                {"type": "choice_3", "branches": ["b3", "b4", "b5"]},
                {"type": "free", "branches": ["b6", "b7"]}
            ],
            "branches": [
                {"id": "b1", "name": "压制", "description": "生成1层压制。"},
                {"id": "b2", "name": "资源生成", "description": "命中生成2法力。"},
                {"id": "b3", "name": "伤害加成", "description": "燃烧伤害+50%[x]。"},
                {"id": "b4", "name": "萤火虫", "description": "爆炸3次。"},
                {"id": "b5", "name": "双生火焰", "description": "额外一发飞弹。"},
                {"id": "b6", "name": "治疗", "description": "命中回复2%生命。"},
                {"id": "b7", "name": "寒颤", "description": "变为冰霜技能。"}
            ]
        }
    ]
}

class SkillTreeSystem:
    def __init__(self, profession, data=None):
        self.profession = profession
        if data is None:
            data = SAMPLE_SKILLS
        self.skill_list = data.get(profession, [])
        self.skill_levels = {}
        self.skill_branches = {}
        self.available_points = 84
        self.listeners = []
    
    def can_add_skill_level(self, skill_id):
        skill = next((s for s in self.skill_list if s['id'] == skill_id), None)
        if not skill: return False
        current = self.skill_levels.get(skill_id, 0)
        if current >= skill['max_level']: return False
        if self.available_points <= 0: return False
        return True
    
    def add_skill_level(self, skill_id):
        if not self.can_add_skill_level(skill_id): return False
        self.skill_levels[skill_id] = self.skill_levels.get(skill_id, 0) + 1
        self.available_points -= 1
        self._notify_change()
        return True
    
    def can_activate_branch(self, skill_id, branch_id):
        skill = next((s for s in self.skill_list if s['id'] == skill_id), None)
        if not skill: return False
        if self.skill_levels.get(skill_id, 0) < 1: return False
        if branch_id in self.skill_branches.get(skill_id, []): return False
        if self.available_points <= 0: return False
        branch_groups = skill.get('branch_groups', [])
        for group in branch_groups:
            if branch_id in group['branches']:
                if group['type'] in ('choice_2', 'choice_3'):
                    activated = self.skill_branches.get(skill_id, [])
                    for other in group['branches']:
                        if other in activated:
                            return False
                break
        return True
    
    def activate_branch(self, skill_id, branch_id):
        if not self.can_activate_branch(skill_id, branch_id): return False
        skill = next((s for s in self.skill_list if s['id'] == skill_id), None)
        branch_groups = skill.get('branch_groups', [])
        group = None
        for g in branch_groups:
            if branch_id in g['branches']:
                group = g
                break
        if group and group['type'] in ('choice_2', 'choice_3'):
            activated = self.skill_branches.get(skill_id, [])
            for other in group['branches']:
                if other in activated:
                    activated.remove(other)
                    self.available_points += 1
            self.skill_branches[skill_id] = activated
        if skill_id not in self.skill_branches:
            self.skill_branches[skill_id] = []
        self.skill_branches[skill_id].append(branch_id)
        self.available_points -= 1
        self._notify_change()
        return True
    
    def _notify_change(self):
        for listener in self.listeners:
            listener()
    
    def add_listener(self, callback):
        self.listeners.append(callback)


class SkillTreeUI:
    def __init__(self, parent, skill_system):
        self.skill_system = skill_system
        self.frame = tk.Frame(parent, bg='#150808')
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self._build_ui()
        self.skill_system.add_listener(self.refresh)
    
    def _build_ui(self):
        self.points_label = tk.Label(self.frame, text=f"可用技能点: {self.skill_system.available_points}",
                                     font=('微软雅黑',12), fg='#FFD700', bg='#150808')
        self.points_label.pack(anchor='w', pady=5)
        canvas = tk.Canvas(self.frame, bg='#150808', highlightthickness=0)
        scrollbar = tk.Scrollbar(self.frame, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.skills_frame = tk.Frame(canvas, bg='#150808')
        canvas.create_window((0,0), window=self.skills_frame, anchor='nw')
        self.skills_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        self._populate_skills()
    
    def _populate_skills(self):
        for widget in self.skills_frame.winfo_children():
            widget.destroy()
        for skill in self.skill_system.skill_list:
            skill_frame = tk.Frame(self.skills_frame, bg='#150808', bd=1, relief='ridge')
            skill_frame.pack(fill=tk.X, pady=5, padx=5)
            # 技能名和等级
            top_row = tk.Frame(skill_frame, bg='#150808')
            top_row.pack(fill=tk.X, padx=5, pady=2)
            level = self.skill_system.skill_levels.get(skill['id'], 0)
            label = tk.Label(top_row, text=f"{skill['name']}  Lv.{level}/{skill['max_level']}",
                             font=('微软雅黑',10,'bold'), fg='#FFD700', bg='#150808')
            label.pack(side=tk.LEFT)
            btn_plus = tk.Button(top_row, text='+', command=lambda s=skill: self.skill_system.add_skill_level(s['id']),
                                 bg='#2a2a2a', fg='#FFD700', width=3)
            btn_plus.pack(side=tk.RIGHT)
            # 描述
            desc = tk.Label(skill_frame, text=skill['description'], font=('微软雅黑',8),
                            fg='#C0A060', bg='#150808', wraplength=600, justify='left')
            desc.pack(fill=tk.X, padx=5, pady=2)
            # 分支
            groups = skill.get('branch_groups', [])
            branches = {b['id']: b for b in skill.get('branches', [])}
            activated = self.skill_system.skill_branches.get(skill['id'], [])
            for group in groups:
                group_frame = tk.Frame(skill_frame, bg='#150808')
                group_frame.pack(fill=tk.X, padx=5, pady=2)
                if group['type'] == 'choice_2':
                    label = tk.Label(group_frame, text="【二选一】", font=('微软雅黑',8), fg='#FFAA00', bg='#150808')
                    label.pack(side=tk.LEFT)
                elif group['type'] == 'choice_3':
                    label = tk.Label(group_frame, text="【三选一】", font=('微软雅黑',8), fg='#FFAA00', bg='#150808')
                    label.pack(side=tk.LEFT)
                else:
                    label = tk.Label(group_frame, text="【自由】", font=('微软雅黑',8), fg='#88CCFF', bg='#150808')
                    label.pack(side=tk.LEFT)
                for bid in group['branches']:
                    branch = branches.get(bid)
                    if not branch: continue
                    is_active = bid in activated
                    btn = tk.Button(group_frame, text=f"{'✓' if is_active else '+'} {branch['name']}",
                                    font=('微软雅黑',8), bg='#3a6a3a' if is_active else '#2a2a2a',
                                    fg='#FFD700', bd=0, padx=4, pady=2,
                                    command=lambda sid=skill['id'], bid=bid: self.skill_system.activate_branch(sid, bid))
                    btn.pack(side=tk.LEFT, padx=2)
    
    def refresh(self):
        self.points_label.config(text=f"可用技能点: {self.skill_system.available_points}")
        self._populate_skills()


# 测试窗口
if __name__ == '__main__':
    root = tk.Tk()
    root.title("技能树测试")
    root.geometry("600x500")
    skill_sys = SkillTreeSystem("巫师")
    ui = SkillTreeUI(root, skill_sys)
    root.mainloop()