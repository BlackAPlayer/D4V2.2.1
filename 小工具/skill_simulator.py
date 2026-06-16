import json

class SkillTreeSim:
    def __init__(self, nodes, edges):
        self.nodes = nodes
        self.edges = edges      # 列表 of (from_idx, to_idx)
        self.points = [0] * len(nodes)   # 每个节点的点数（0或1，简化版）
    
    def can_upgrade(self, idx):
        # 检查所有指向该节点的前置节点是否都至少有1点
        for src, dst in self.edges:
            if dst == idx and self.points[src] == 0:
                return False
        return self.points[idx] == 0   # 只能点一次
    
    def upgrade(self, idx):
        if self.can_upgrade(idx):
            self.points[idx] = 1
            return True
        return False
    
    def print_status(self):
        print("当前加点状态（技能名，如果无名称则显示类型）:")
        for i, node in enumerate(self.nodes):
            if self.points[i] == 1:
                name = node.get('skill_id') or node['type']
                print(f"  {i}: {name}")

# 加载数据
with open('skilltree_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
nodes = data['nodes']

# 加载连线关系（上一步生成的 edges.json）
try:
    with open('edges.json', 'r', encoding='utf-8') as f:
        edges = json.load(f)
except FileNotFoundError:
    print("请先运行 find_edges.py 生成 edges.json")
    exit()

# 创建模拟器
sim = SkillTreeSim(nodes, edges)

# 示例：尝试加点
print("尝试升级节点0...")
if sim.upgrade(0):
    print("成功！")
else:
    print("失败（前置未满足或已点过）")

sim.print_status()

# 再试一个节点（比如索引1）
print("\n尝试升级节点1...")
if sim.upgrade(1):
    print("成功！")
else:
    print("失败")
sim.print_status()