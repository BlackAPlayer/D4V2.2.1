import json

# 检查 skilltree_data.json
with open('skilltree_data.json', 'r', encoding='utf-8') as f:
    tree = json.load(f)
tree_ids = set()
for node in tree['nodes']:
    sid = node.get('skill_id')
    if sid:
        tree_ids.add(sid)
print(f"skilltree_data.json 中的 skill_id 数量: {len(tree_ids)}")
print("前5个:", list(tree_ids)[:5])

# 检查 skill.json
with open('skill.json', 'r', encoding='utf-8') as f:
    skills = json.load(f)
if '巫师' in skills:
    wizard_skills = skills['巫师']
    if isinstance(wizard_skills, dict) and 'skills' in wizard_skills:
        wizard_skills = wizard_skills['skills']
    skill_ids = {s['id'] for s in wizard_skills}
    print(f"skill.json 中的巫师技能 id 数量: {len(skill_ids)}")
    print("前5个:", list(skill_ids)[:5])
else:
    print("skill.json 中没有找到'巫师'")

# 检查匹配情况（去除前缀后）
matched = 0
for tid in tree_ids:
    # 去除职业前缀
    for prefix in ['sorcerer_', 'barbarian_', 'druid_', 'rogue_', 'necromancer_']:
        if tid.startswith(prefix):
            tid = tid[len(prefix):]
            break
    if tid in skill_ids:
        matched += 1
print(f"匹配上的技能数量: {matched}")