import os
import json
import re
from PIL import Image
from bs4 import BeautifulSoup

# 配置
SPRITE_FILE = 'images/skill-sprite.png'
OUTPUT_DIR = 'images/icons_full'
HTML_FILE = 'skilltree.html'   # 用于匹配技能ID（可选，如果没有可以忽略）

# 已知参数
SPRITE_W, SPRITE_H = 1408, 1280
ICON_SIZE = 64
COLS = SPRITE_W // ICON_SIZE   # 22
ROWS = SPRITE_H // ICON_SIZE   # 20

print(f"精灵图尺寸: {SPRITE_W}x{SPRITE_H}, 图标尺寸: {ICON_SIZE}x{ICON_SIZE}")
print(f"网格: {COLS} 列 x {ROWS} 行, 共 {COLS * ROWS} 个图标")

# 创建输出目录
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 可选: 从 HTML 中解析已有技能图标的位置映射，用于标注
skill_to_position = {}  # { (col, row): skill_id }
if os.path.exists(HTML_FILE):
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        html = f.read()
    soup = BeautifulSoup(html, 'html.parser')
    # 收集所有唯一百分比
    x_percents = set()
    y_percents = set()
    temp_data = []
    for icon_div in soup.find_all('uni-view', class_='tree-icon'):
        style = icon_div.get('style', '')
        tooltip = icon_div.get('tooltip', '')
        m = re.search(r'skill:([\w_]+)', tooltip)
        if not m:
            continue
        skill_id = m.group(1)
        pos_match = re.search(r'background-position:\s*([\d.]+)%\s+([\d.]+)%', style)
        if not pos_match:
            continue
        xp = float(pos_match.group(1))
        yp = float(pos_match.group(2))
        temp_data.append((skill_id, xp, yp))
        x_percents.add(round(xp, 4))
        y_percents.add(round(yp, 4))
    # 排序并建立映射
    sorted_x = sorted(x_percents)
    sorted_y = sorted(y_percents)
    x_to_col = {x: i for i, x in enumerate(sorted_x)}
    y_to_row = {y: i for i, y in enumerate(sorted_y)}
    for skill_id, xp, yp in temp_data:
        col = x_to_col[round(xp, 4)]
        row = y_to_row[round(yp, 4)]
        skill_to_position[(col, row)] = skill_id
    print(f"从 HTML 中解析到 {len(skill_to_position)} 个技能位置映射")
else:
    print(f"未找到 {HTML_FILE}，将不生成技能映射")

# 加载精灵图
sprite = Image.open(SPRITE_FILE)

# 遍历所有行列，切割并保存
full_map = {}
for row in range(ROWS):
    for col in range(COLS):
        left = col * ICON_SIZE
        top = row * ICON_SIZE
        right = left + ICON_SIZE
        bottom = top + ICON_SIZE
        icon = sprite.crop((left, top, right, bottom))
        filename = f"row{row:02d}_col{col:02d}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        icon.save(filepath)
        # 记录信息
        skill_id = skill_to_position.get((col, row))  # 注意 (col, row) 顺序
        full_map[filename] = {
            "row": row,
            "col": col,
            "skill_id": skill_id,
            "x_percent": round(100 * col / COLS, 4) if COLS > 0 else 0,
            "y_percent": round(100 * row / ROWS, 4) if ROWS > 0 else 0,
        }
        if skill_id:
            print(f"row{row:02d}_col{col:02d} -> 技能: {skill_id}")

print(f"\n全部切割完成！共 {len(full_map)} 个图标，保存在 {OUTPUT_DIR}")

# 保存映射表
with open('full_icon_map.json', 'w', encoding='utf-8') as f:
    json.dump(full_map, f, indent=2, ensure_ascii=False)
print("已生成 full_icon_map.json")