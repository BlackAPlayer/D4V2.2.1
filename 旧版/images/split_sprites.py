import re
import json
import os
from PIL import Image

# ========== 配置区 ==========
JS_FILE = "database-item.CRnjveyv.js"   # 存放 icons 数据的 JS 文件名
SPRITE_FILE = "skill-sprite.png"          # 精灵图文件名
OUTPUT_DIR = "output_icons"            # 输出文件夹名
# ===========================

def extract_data_from_js(js_path):
    """从 JS 文件中提取 icons 数组、cols、rows"""
    with open(js_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 提取 icons 数组（例如 icons = [7099689, 7199608, ...]）
    icons_match = re.search(r'icons\s*=\s*\[([^\]]+)\]', content)
    if not icons_match:
        raise ValueError("未找到 icons 数组，请检查 JS 文件内容")
    # 解析数组内容（注意可能有换行和注释）
    icons_str = icons_match.group(1)
    # 用正则提取所有数字
    icons = [int(x) for x in re.findall(r'\d+', icons_str)]
    print(f"提取到 {len(icons)} 个图标 ID")

    # 提取 cols 和 rows
    cols_match = re.search(r'cols\s*=\s*(\d+)', content)
    rows_match = re.search(r'rows\s*=\s*(\d+)', content)
    if not cols_match or not rows_match:
        raise ValueError("未找到 cols 或 rows")
    cols = int(cols_match.group(1))
    rows = int(rows_match.group(1))
    print(f"精灵图网格: {cols} 列 x {rows} 行")

    return icons, cols, rows

def main():
    # 1. 从 JS 提取数据
    try:
        icons, cols, rows = extract_data_from_js(JS_FILE)
    except Exception as e:
        print(f"❌ 解析 JS 文件失败: {e}")
        return

    # 2. 打开精灵图
    try:
        sprite = Image.open(SPRITE_FILE)
    except FileNotFoundError:
        print(f"❌ 找不到精灵图文件: {SPRITE_FILE}")
        return

    img_width, img_height = sprite.size
    icon_width = img_width // cols
    icon_height = img_height // rows
    print(f"图片尺寸: {img_width}x{img_height}, 每个图标大小: {icon_width}x{icon_height}")

    # 3. 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 4. 遍历每个 ID 进行切割
    total = len(icons)
    for idx, icon_id in enumerate(icons):
        row = idx // cols
        col = idx % cols
        left = col * icon_width
        upper = row * icon_height
        right = left + icon_width
        lower = upper + icon_height

        # 裁剪
        try:
            icon_img = sprite.crop((left, upper, right, lower))
            # 保存为 ID.png
            out_path = os.path.join(OUTPUT_DIR, f"{icon_id}.png")
            icon_img.save(out_path)
        except Exception as e:
            print(f"⚠️ 处理 ID {icon_id} 时出错: {e}")
            continue

        # 进度提示
        if (idx + 1) % 100 == 0:
            print(f"已处理 {idx + 1}/{total} 个图标")

    print(f"✅ 完成！共处理 {total} 个图标，保存在 '{OUTPUT_DIR}' 文件夹")

if __name__ == "__main__":
    main()