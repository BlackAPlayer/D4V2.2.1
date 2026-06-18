# check_layout.py
import json

with open('skilltree_layout.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

nodes = data.get('nodes')
if not nodes:
    print("⚠️ 没有找到节点数据")
    exit()

# 兼容列表和字典两种结构
if isinstance(nodes, list):
    xs = [n['x'] for n in nodes if 'x' in n]
    ys = [n['y'] for n in nodes if 'y' in n]
elif isinstance(nodes, dict):
    xs = [n['x'] for n in nodes.values() if 'x' in n]
    ys = [n['y'] for n in nodes.values() if 'y' in n]
else:
    print("⚠️ 未知的节点格式")
    exit()

if not xs:
    print("⚠️ 没有找到有效的坐标数据")
    exit()

print(f"📊 技能树节点范围:")
print(f"  X: {min(xs):.0f} ~ {max(xs):.0f}  (宽度: {max(xs)-min(xs):.0f})")
print(f"  Y: {min(ys):.0f} ~ {max(ys):.0f}  (高度: {max(ys)-min(ys):.0f})")
print(f"\n📐 推荐背景图尺寸 (含边距60px):")
print(f"  {int(max(xs)-min(xs)+120)} × {int(max(ys)-min(ys)+120)}")
print(f"\n📐 推荐画布尺寸 (含边距60px):")
print(f"  width={int(max(xs)-min(xs)+120)}, height={int(max(ys)-min(ys)+120)}")