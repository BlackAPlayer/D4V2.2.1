# 项目概述
- 项目名称：D4Calculator（暗黑破坏神4 计算器）V2.2.1
- 技术栈：Python 3 + Tkinter，PIL 图片处理，JSON 数据存储
- 核心功能：技能树加点、装备编辑、护身符系统、巅峰盘（占位）

# 目录结构（关键部分）
D4Calculator/
├── main.py                      # 程序入口
├── skill.json                   # 全职业技能数据（含分支、数值）
├── full_database_new.json       # 装备、威能、词缀、暗金等完整数据库
├── skilltree_layout.json        # 技能树节点布局（坐标、连线、边框、被动）
├── skill_tree_editor.html       # 可视化布局编辑器（独立HTML，浏览器使用）
├── business/
│   └── skill_tree.py            # SkillTreeSystem 类（加点、分支、外部加成）
├── ui/
│   ├── main_window.py           # 主窗口，整合所有标签页
│   ├── skill_tree_ui.py         # SkillTreeUI 类（绘制、交互、提示）—— 已优化
│   ├── equipment_ui.py          # 装备UI
│   ├── talisman_ui_tk.py        # 护身符UI
│   └── widgets.py               # 通用UI组件
├── data/
│   └── loader.py                # 加载图片、数据库（含图片缓存）
├── config/
│   └── __init__.py              # resource_path，职业、槽位常量
└── utils/
    └── image_cache.py           # 全局图片缓存字典

# 关键模块与接口
- SkillTreeSystem（business/skill_tree.py）
  - 主要属性：skill_data, skill_levels, branch_levels, available_points, listeners
  - 主要方法：add_level, remove_level, activate_branch, deactivate_branch, reset_all, get_skill_display_info
  - 监听机制：add_listener(callback) 在数据变化时调用

- SkillTreeUI（ui/skill_tree_ui.py）—— 已做轻量级优化
  - 初始化：加载布局，创建画布，绑定事件
  - 绘制：_draw_background, _draw_edges, _draw_all_nodes
  - 交互：点击加点/减点，拖拽平移，悬停提示
  - 优化内容：
    1. 背景图缩放缓存（_bg_cache）
    2. refresh 改为增量更新（只改等级文本，不重建节点）
    3. 未改动结构，保证运行效果不变

- SkillTreeEditor（skill_tree_editor.html）
  - 独立工具，用于可视化编辑布局
  - 支持添加节点、连线、设定技能/分支、上传边框图片、设置被动
  - 可加载/保存 layout.json

# 已完成的工作
- 运行了 `optimize_skill_tree_ui.py` 脚本，对 skill_tree_ui.py 进行了性能优化（背景缓存 + 增量刷新）
- 确认优化不影响原功能

# 待办/待讨论事项（按优先级）
1. 轻量级拆分：将 SkillTreeTooltip 类提取到独立文件（安全且易于维护）
2. 完整模块化拆分：将 SkillTreeUI 拆分为 Renderer、EventHandler、LayoutLoader 等（需要设计）
3. 增强 HTML 编辑器：增加自动布局、撤销/重做、节点对齐等功能
4. 统一图片缓存：所有 load_photo_image 调用迁移到 utils/image_cache.py（目前 data/loader.py 也有自己的缓存）