import json
import matplotlib.pyplot as plt

# 读取数据
with open('skilltree_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

nodes = data['nodes']

# 按类型设置不同颜色
colors = {
    'skill': 'blue',
    'mod': 'green',
    'joint': 'gray',
    'root': 'red',
    'unknown': 'black'
}

plt.figure(figsize=(14, 10))

# 遍历所有节点，绘制散点
for node in nodes:
    if node['left'] is None or node['top'] is None:
        continue
    color = colors.get(node['type'], 'black')
    plt.scatter(node['left'], node['top'], c=color, s=20, alpha=0.7)

# 因为 HTML 中 top 越大越往下，所以翻转 Y 轴，让图形符合直觉
plt.gca().invert_yaxis()
plt.xlabel('X (px)')
plt.ylabel('Y (px)')
plt.title('Skill Tree Node Positions')
plt.grid(True, linestyle=':', alpha=0.3)

# 显示图形
plt.show()