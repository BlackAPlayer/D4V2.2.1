import os
import json

# ========== 配置（请按实际情况修改） ==========
SKILL_JSON_PATH = "skill.json"          # 你的技能 JSON 文件路径
ICON_DIR = "images/icons"               # 图标所在目录
UNMATCHED_LOG = "unmatched.txt"         # 未匹配的文件列表输出

# ========== 加载技能 ID 列表 ==========
def load_skill_keys(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("skill.json 应该是一个数组")
    keys = [item["key"] for item in data if "key" in item]
    return set(keys)

skill_keys = load_skill_keys(SKILL_JSON_PATH)
print(f"已加载 {len(skill_keys)} 个技能 key")

# ========== 扫描图标文件 ==========
if not os.path.isdir(ICON_DIR):
    print(f"错误：目录 {ICON_DIR} 不存在")
    exit(1)

files = [f for f in os.listdir(ICON_DIR) if f.lower().endswith(".png")]
print(f"找到 {len(files)} 个 PNG 文件")

# ========== 建立重命名映射 ==========
rename_map = {}      # 旧名 -> 新名
unmatched = []

# 辅助函数：去掉可能的职业前缀，提取核心名称
def strip_prefix(name):
    prefixes = ["sorcerer_", "barbarian_", "druid_", "rogue_", "necromancer_",
                "paladin_", "warlock_", "spiritborn_"]
    for p in prefixes:
        if name.startswith(p):
            return name[len(p):]
    return name

for fname in files:
    base = fname[:-4]   # 无扩展名
    
    # 情况1：直接匹配完整技能 key
    if base in skill_keys:
        continue
    
    # 情况2：去掉职业前缀后匹配
    core = strip_prefix(base)
    if core in skill_keys:
        new_name = core + ".png"
        rename_map[fname] = new_name
    else:
        # 情况3：base 本身就是核心名称（例如 arc_lash.png）
        if base in skill_keys:
            rename_map[fname] = base + ".png"
        else:
            unmatched.append(fname)

# ========== 输出计划 ==========
print(f"\n需要重命名的文件: {len(rename_map)}")
for old, new in list(rename_map.items())[:20]:
    print(f"  {old} -> {new}")
if len(rename_map) > 20:
    print(f"  ... 还有 {len(rename_map)-20} 个")

print(f"\n无法匹配的文件: {len(unmatched)}")
if unmatched:
    with open(UNMATCHED_LOG, 'w', encoding='utf-8') as f:
        f.write("\n".join(unmatched))
    print(f"已保存到 {UNMATCHED_LOG}")

# ========== 执行重命名 ==========
if rename_map:
    ans = input("\n是否执行重命名？(y/n): ").strip().lower()
    if ans == 'y':
        for old, new in rename_map.items():
            old_path = os.path.join(ICON_DIR, old)
            new_path = os.path.join(ICON_DIR, new)
            if os.path.exists(new_path) and not os.path.samefile(old_path, new_path):
                print(f"跳过 {old} -> {new}，目标文件已存在")
                continue
            os.rename(old_path, new_path)
        print("重命名完成！")
    else:
        print("已取消。")
else:
    print("无需重命名。")