import os
import json
from PIL import Image

# 输入文件路径（根据你实际存放的位置修改）
FRAME_FILE = 'images/skill-frames-dlc2.png'   # 如果文件在脚本同级目录，可以只写文件名
OUTPUT_DIR = 'images/frames'

# 已知图片尺寸 600x200，切割为 6列2行
W, H = 600, 200
COLS = 6
ROWS = 2
FRAME_W = W // COLS   # 100
FRAME_H = H // ROWS   # 100

print(f"图片尺寸: {W}x{H}, 切割为 {COLS} 列 x {ROWS} 行, 每块 {FRAME_W}x{FRAME_H}")

# 打开图片
img = Image.open(FRAME_FILE)
os.makedirs(OUTPUT_DIR, exist_ok=True)

frames_info = {}
count = 0
for row in range(ROWS):
    for col in range(COLS):
        left = col * FRAME_W
        top = row * FRAME_H
        right = left + FRAME_W
        bottom = top + FRAME_H
        frame = img.crop((left, top, right, bottom))
        filename = f"frame_{row}_{col}.png"
        filepath = os.path.join(OUTPUT_DIR, filename)
        frame.save(filepath)
        frames_info[filename] = {"row": row, "col": col, "width": FRAME_W, "height": FRAME_H}
        print(f"保存: {filename}")
        count += 1

# 保存映射文件
with open('frames_map.json', 'w', encoding='utf-8') as f:
    json.dump(frames_info, f, indent=2)
print(f"完成！共切割 {count} 个边框，保存在 {OUTPUT_DIR}")