import json
from config import resource_path
from business.skill_tree import SkillTreeSystem

# 初始化技能系统（巫师）
skill_system = SkillTreeSystem("巫师")

# 加载布局
with open('skilltree_layout.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

nodes = data.get('nodes', [])

print("节点信息：")
for node in nodes:
    node_id = node.get('id')
    node_type = node.get('nodeType')
    skill_name = node.get('skillName')
    mod_data = node.get('mod_data')
    owner = node.get('ownerSkillKey')
    branch = node.get('branchId')
    
    # 只打印主动节点和分支节点
    if node_type in ('active', 'morph', 'passive'):
        print(f"ID:{node_id} type:{node_type} name:{skill_name} owner:{owner} branch:{branch}")
        if mod_data:
            print(f"   mod_data.name: {mod_data.get('name')}")