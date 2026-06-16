import re
import json
from bs4 import BeautifulSoup

# 读取 HTML 文件
with open('skilltree.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

# 提取所有节点
nodes = []
for node in soup.find_all('uni-view', class_=re.compile('skill-tree-node')):
    style = node.get('style', '')
    left = re.search(r'left:\s*([\d.]+)px', style)
    top = re.search(r'top:\s*([\d.]+)px', style)
    left_val = float(left.group(1)) if left else None
    top_val = float(top.group(1)) if top else None
    
    # 节点类型
    classes = node.get('class', [])
    if 'node-skill' in classes and 'node-skill-mod' not in classes:
        node_type = 'skill'
    elif 'node-skill-mod' in classes:
        node_type = 'mod'
    elif 'node-joint' in classes:
        node_type = 'joint'
    elif 'node-root' in classes:
        node_type = 'root'
    else:
        node_type = 'unknown'
    
    # 技能ID（从 tooltip 或背景图中提取）
    tooltip = node.get('tooltip', '')
    skill_id = None
    m = re.search(r'skill:([\w_]+)', tooltip)
    if m:
        skill_id = m.group(1)
    
    nodes.append({
        'type': node_type,
        'left': left_val,
        'top': top_val,
        'skill_id': skill_id,
        'tooltip': tooltip
    })

# 提取连线（普通线和大连线）
lines = []
for line in soup.find_all('uni-view', class_=re.compile('skill-tree-line')):
    style = line.get('style', '')
    left = re.search(r'left:\s*([\d.]+)px', style)
    top = re.search(r'top:\s*([\d.]+)px', style)
    width = re.search(r'width:\s*([\d.]+)px', style)
    rot = re.search(r'rotate\(([\-\d.]+)rad\)', style)
    if left and top and width and rot:
        lines.append({
            'left': float(left.group(1)),
            'top': float(top.group(1)),
            'width': float(width.group(1)),
            'rotation_rad': float(rot.group(1))
        })

# 保存为 JSON
data = {
    'node_count': len(nodes),
    'line_count': len(lines),
    'nodes': nodes,
    'lines': lines
}
with open('skilltree_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"提取完成！共 {len(nodes)} 个节点，{len(lines)} 条连线。")
print("数据已保存到 skilltree_data.json")