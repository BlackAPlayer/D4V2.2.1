import json, os

# 读取 skilltree_data.json
with open('skilltree_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
nodes = data.get('nodes', [])
skill_ids = set(node.get('skill_id') for node in nodes if node.get('skill_id'))
print(f"skilltree_data.json 中的技能数量: {len(skill_ids)}")
print("前20个:", list(skill_ids)[:20])

# 读取 skills.json（可能是 UTF-8）
with open('skills.json', 'r', encoding='utf-8') as f:
    skills_data = json.load(f)
if '巫师' in skills_data:
    skill_list = skills_data['巫师']
    if isinstance(skill_list, dict) and 'skills' in skill_list:
        skill_list = skill_list['skills']
    known_ids = set(s['id'] for s in skill_list)
    print(f"skills.json 中的技能数量: {len(known_ids)}")
    missing = skill_ids - known_ids
    if missing:
        print(f"缺失的技能ID: {missing}")
    else:
        print("所有技能ID都匹配！")
else:
    print("skills.json 中没有找到'巫师'")

# 检查图标目录
icons_dir = 'images/icons'
if os.path.exists(icons_dir):
    icon_files = set(f[:-4] for f in os.listdir(icons_dir) if f.endswith('.png'))
    print(f"icons 目录中的图标数量: {len(icon_files)}")
    missing_icons = skill_ids - icon_files
    if missing_icons:
        print(f"缺失图标的技能ID: {missing_icons}")
    else:
        print("所有技能都有图标！")
else:
    print("images/icons 目录不存在")