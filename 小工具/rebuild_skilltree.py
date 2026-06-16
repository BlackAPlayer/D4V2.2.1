import re
import json
from bs4 import BeautifulSoup

with open('skilltree.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')

nodes = []
# 查找所有 skill-tree-node 容器
for node in soup.find_all('uni-view', class_=re.compile('skill-tree-node')):
    style = node.get('style', '')
    left = re.search(r'left:\s*([\d.]+)px', style)
    top = re.search(r'top:\s*([\d.]+)px', style)
    if not left or not top:
        continue
    
    # 在 node 内部查找 tree-icon，获取 tooltip
    icon = node.find('uni-view', class_='tree-icon')
    skill_id = None
    if icon:
        tooltip = icon.get('tooltip', '')
        m = re.search(r'skill:([\w_]+)', tooltip)
        if m:
            skill_id = m.group(1)
    
    nodes.append({
        'skill_id': skill_id,
        'left': float(left.group(1)),
        'top': float(top.group(1)),
        'type': 'skill'  # 可根据 node 的 class 细化
    })

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

data = {'nodes': nodes, 'lines': lines}
with open('skilltree_data.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
print(f"提取完成：{len(nodes)} 个节点，{len(lines)} 条连线")
print(f"有效 skill_id 数量: {sum(1 for n in nodes if n['skill_id'] is not None)}")