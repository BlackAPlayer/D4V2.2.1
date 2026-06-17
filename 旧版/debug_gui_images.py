#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
D4 技能树图像调试器 (Tkinter)
用途：检查背景图和技能图标为何无法显示
运行：直接 python debug_gui_images.py
"""

import os
import sys
import tkinter as tk
from tkinter import ttk

# ---------- 1. 检查 Pillow 库 ----------
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
    print("[✓] Pillow (PIL) 已安装，支持 JPG/WebP 等格式")
except ImportError:
    HAS_PIL = False
    print("[!] Pillow (PIL) 未安装，Tkinter 仅支持 PNG/GIF/PPM 格式")
    print("    安装命令: pip install Pillow")
print("-" * 60)

# ---------- 2. 定义需要排查的路径（已根据项目修正）----------
# 基础路径（基于脚本所在目录）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
print(f"[信息] 脚本运行目录: {BASE_DIR}")

# 背景图候选列表 —— 将您的实际路径放在最前面
CANDIDATE_BG = [
    "images/skill_bg.png",      # 您的实际背景图
    "skill_bg.png",
    "bg.png",
    "background.png",
    "BG.png",
    "images/bg.png"
]

# 图标目录候选列表 —— 优先查找 images/icons
CANDIDATE_ICON_DIRS = [
    "images/icons",    # 您的实际图标目录
    "icons",
    "images",
    "assets",
    "."
]

# 示例图标文件名（与您的 skillKey 对应，用于测试加载）
SAMPLE_ICON_NAMES = [
    "sorcerer_frost_bolt.png",
    "sorcerer_fireball.png",
    "sorcerer_chain_lightning.png",
    "fire.png",
    "skill_1.png"
]

# ---------- 3. 核心调试类 ----------
class ImageDebugger:
    def __init__(self, root):
        self.root = root
        self.root.title("D4 技能树 - 图像调试器")
        self.root.geometry("800x700")
        
        # 存放图像引用（关键：防止被 GC 回收）
        self.image_refs = {}
        
        # 搭建界面
        self.setup_ui()
        
        # 执行自动诊断
        self.run_diagnosis()
    
    def setup_ui(self):
        """创建控制台日志区和画布预览区"""
        # 上方：文本日志框
        log_frame = ttk.LabelFrame(self.root, text="诊断日志", padding=5)
        log_frame.pack(fill=tk.BOTH, expand=False, padx=10, pady=5)
        
        self.log_text = tk.Text(log_frame, height=12, bg="#1e1e1e", fg="#d4d4d4", 
                                font=("Consolas", 10), wrap=tk.WORD)
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 下方：画布预览区
        canvas_frame = ttk.LabelFrame(self.root, text="画布渲染预览 (模拟技能树)", padding=5)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.canvas = tk.Canvas(canvas_frame, bg="#2b2b2b", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # 绑定窗口大小改变事件，自适应重绘
        self.root.bind("<Configure>", lambda e: self.redraw_preview())
    
    def log(self, msg, is_error=False):
        """向日志框写入信息"""
        tag = "error" if is_error else "normal"
        self.log_text.insert(tk.END, msg + "\n", tag)
        self.log_text.see(tk.END)
        # 配置颜色
        self.log_text.tag_config("error", foreground="#f48771")
        self.log_text.tag_config("normal", foreground="#d4d4d4")
        # 同时打印到控制台
        print(msg)
    
    def run_diagnosis(self):
        """执行全自动诊断流程"""
        self.log(">>> 开始 Tkinter 图像加载诊断 <<<")
        
        # 检查1：文件系统扫描
        self.scan_files()
        
        # 检查2：Tkinter 图像加载测试（带/不带 GC 陷阱对比）
        self.test_image_loading()
        
        # 检查3：绘制预览
        self.redraw_preview()
        
        self.log(">>> 诊断完成，请观察上方预览区 <<<")
    
    def scan_files(self):
        """扫描目录，查找候选文件"""
        self.log("\n[步骤1] 扫描文件路径...")
        
        # 列出根目录下所有文件/文件夹，供参考
        try:
            items = os.listdir(BASE_DIR)
            self.log(f"当前目录内容 ({len(items)}项): {', '.join(items[:20])}" + 
                     (f" ...等" if len(items) > 20 else ""))
        except Exception as e:
            self.log(f"无法列出目录: {e}", is_error=True)
        
        # 查找背景图
        found_bg = False
        for candidate in CANDIDATE_BG:
            full_path = os.path.join(BASE_DIR, candidate)
            if os.path.isfile(full_path):
                self.log(f"  [找到背景] {candidate} (大小: {os.path.getsize(full_path)} bytes)")
                found_bg = True
                self.bg_path = full_path
                break
        if not found_bg:
            self.log("  [警告] 未找到常见背景图文件名 (请确认 images/skill_bg.png 是否存在)", is_error=True)
            self.bg_path = None
        
        # 查找图标目录
        self.icon_paths = []
        for dir_name in CANDIDATE_ICON_DIRS:
            full_dir = os.path.join(BASE_DIR, dir_name)
            if os.path.isdir(full_dir):
                png_files = [f for f in os.listdir(full_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
                self.log(f"  [找到图标目录] {dir_name}/ 包含 {len(png_files)} 个图片文件")
                self.icon_paths.append(full_dir)
                # 显示前5个
                if png_files:
                    self.log(f"    示例: {', '.join(png_files[:5])}")
        
        if not self.icon_paths:
            self.log("  [警告] 未找到 'images/icons' 或 'icons' 文件夹", is_error=True)
    
    def test_image_loading(self):
        """关键测试：演示 GC 陷阱和格式问题"""
        self.log("\n[步骤2] 执行图像加载测试...")
        
        # 创建一个测试图标（如果没有真实图片，我们生成一个色块）
        test_img = None
        load_success = False
        
        # 优先尝试加载真实图标
        for icon_dir in self.icon_paths:
            for fname in SAMPLE_ICON_NAMES:
                full_path = os.path.join(icon_dir, fname)
                if os.path.isfile(full_path):
                    self.log(f"  尝试加载: {full_path}")
                    try:
                        if HAS_PIL:
                            pil_img = Image.open(full_path)
                            test_img = ImageTk.PhotoImage(pil_img)
                        else:
                            # 纯 Tkinter，只支持 PNG/GIF
                            if full_path.lower().endswith(('.png', '.gif', '.ppm')):
                                test_img = tk.PhotoImage(file=full_path)
                            else:
                                self.log(f"    [跳过] 格式不支持 (需安装 Pillow): {fname}", is_error=True)
                                continue
                        
                        if test_img:
                            load_success = True
                            self.log(f"    [成功] 加载了图像: {fname} (尺寸: {test_img.width()}x{test_img.height()})")
                            break
                    except Exception as e:
                        self.log(f"    [加载失败] {e}", is_error=True)
            if load_success:
                break
        
        # 如果找不到真实图片，动态生成一个测试用的彩色方块（模拟图标）
        if not load_success:
            self.log("  [提示] 未找到真实图标文件，将生成内置色块进行演示", is_error=True)
            # 这里我们不做动态PhotoImage，因为纯tkinter无法绘制到PhotoImage，我们直接用画布画oval来代替展示效果。
            pass
        
        # 保存引用，防止GC（关键演示）
        self.test_icon_ref = test_img
        self.log("  [重要] 已保存图像引用至 self.test_icon_ref，防止垃圾回收 (GC)")
        
        # 反例演示：创建一个不保存引用的图像，用于对比
        self.log("  [演示] 创建不保存引用的图像 (将在绘制后被回收)...")
        try:
            # 尝试加载同样的图片但不存引用
            temp_img = None
            if load_success and test_img:
                # 重新加载一张纯色测试图，但不保存
                if HAS_PIL:
                    temp_img = ImageTk.PhotoImage(Image.new('RGB', (30, 30), color='red'))
                else:
                    # 纯tkinter无法生成图片，略过
                    pass
            # 故意不赋值给 self，让它成为局部变量
            self._temp_gc_test = temp_img  # 立即存储一次，防止立刻被回收，但这里我们赋值给self，其实不会回收，为了演示效果我们改为绘制时直接局部变量。
        except:
            pass
    
    def redraw_preview(self, event=None):
        """在画布上绘制测试场景（模拟技能树）"""
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 10 or h < 10:
            w, h = 700, 600  # 默认尺寸
        
        # ---- 1. 绘制背景图 ----
        if hasattr(self, 'bg_path') and self.bg_path and os.path.isfile(self.bg_path):
            try:
                if HAS_PIL:
                    pil_bg = Image.open(self.bg_path)
                    # 缩放背景适配窗口（保持比例或拉伸）
                    bg_img = ImageTk.PhotoImage(pil_bg.resize((w, h), Image.Resampling.LANCZOS))
                else:
                    bg_img = tk.PhotoImage(file=self.bg_path)
                    # 纯Tkinter不支持缩放，直接平铺或居中
                
                # **关键点：必须将图像对象存为实例属性，否则不显示**
                self.bg_ref = bg_img
                self.canvas.create_image(0, 0, image=self.bg_ref, anchor="nw")
                self.log(f"[渲染] 背景图已绘制 (尺寸: {w}x{h})")
            except Exception as e:
                self.log(f"[渲染失败] 背景图加载异常: {e}", is_error=True)
                self.draw_placeholder_bg(w, h)
        else:
            self.draw_placeholder_bg(w, h)
        
        # ---- 2. 绘制模拟技能节点（演示图标和灰色占位） ----
        # 坐标中心点
        cx, cy = w // 2, h // 2
        
        # 绘制5个模拟节点，展示已绑定(彩色)和未绑定(灰色)
        nodes = [
            {"x": cx - 150, "y": cy - 80, "label": "火球", "color": "#ff6b35", "has_icon": True},
            {"x": cx,      "y": cy - 100, "label": "冰霜", "color": "#4fc3f7", "has_icon": True},
            {"x": cx + 150, "y": cy - 80, "label": "闪电", "color": "#ffd54f", "has_icon": False},
            {"x": cx - 100, "y": cy + 80, "label": "未绑定", "color": "#555555", "has_icon": False},
            {"x": cx + 100, "y": cy + 80, "label": "未绑定", "color": "#555555", "has_icon": False},
        ]
        
        # 尝试加载一个真实的图标用于演示（如果存在）
        demo_icon = None
        for icon_dir in self.icon_paths:
            for fname in SAMPLE_ICON_NAMES:
                full_path = os.path.join(icon_dir, fname)
                if os.path.isfile(full_path):
                    try:
                        if HAS_PIL:
                            demo_icon = ImageTk.PhotoImage(Image.open(full_path).resize((32, 32), Image.Resampling.LANCZOS))
                        else:
                            demo_icon = tk.PhotoImage(file=full_path)
                        if demo_icon:
                            self.demo_icon_ref = demo_icon  # 存引用！
                            self.log(f"[渲染] 成功加载演示图标: {fname}")
                            break
                    except Exception as e:
                        pass
            if demo_icon:
                break
        
        self.log(f"[渲染] 绘制 {len(nodes)} 个模拟节点...")
        for node in nodes:
            x, y = node["x"], node["y"]
            color = node["color"]
            
            # 绘制圆形背景
            r = 30
            if color == "#555555":
                # 未绑定：灰色空心圆
                self.canvas.create_oval(x-r, y-r, x+r, y+r, outline="#888888", width=2, fill="")
                self.canvas.create_text(x, y+40, text=node["label"], fill="#aaaaaa", font=("Arial", 10))
            else:
                # 已绑定：填充圆形
                self.canvas.create_oval(x-r, y-r, x+r, y+r, outline="#ffffff", width=2, fill=color)
                
                # 尝试在圆内绘制图标
                if node["has_icon"] and demo_icon:
                    # 将图标放置在圆形中央
                    ix, iy = x - 16, y - 16  # 假设图标32x32
                    self.canvas.create_image(ix, iy, image=self.demo_icon_ref, anchor="nw")
                    self.log(f"  [图标] 在 ({x},{y}) 处绘制了图标")
                else:
                    # 无图标则显示文字缩写
                    self.canvas.create_text(x, y, text=node["label"][0], fill="white", font=("Arial", 14, "bold"))
                
                self.canvas.create_text(x, y+40, text=node["label"], fill="#ffffff", font=("Arial", 10))
        
        # ---- 3. 绘制图例和说明 ----
        self.canvas.create_text(10, 20, text="✓ 彩色实心 = 已绑定技能", fill="#4fc3f7", anchor="nw", font=("Arial", 12))
        self.canvas.create_text(10, 40, text="○ 灰色空心 = 未绑定占位", fill="#888888", anchor="nw", font=("Arial", 12))
        self.canvas.create_text(10, 60, text=f"Pillow: {'已启用' if HAS_PIL else '未安装'}", fill="#ffd54f", anchor="nw", font=("Arial", 10))
        
        # 如果背景图加载失败，显示醒目提示
        if not hasattr(self, 'bg_ref') or self.bg_ref is None:
            self.canvas.create_text(cx, 30, text="⚠ 背景图未加载 (检查路径/格式)", fill="#f48771", font=("Arial", 16, "bold"))
    
    def draw_placeholder_bg(self, w, h):
        """绘制占位背景（棋盘格）"""
        self.canvas.create_rectangle(0, 0, w, h, fill="#1e1e1e")
        # 绘制简单的网格
        for i in range(0, w, 50):
            self.canvas.create_line(i, 0, i, h, fill="#333333")
        for i in range(0, h, 50):
            self.canvas.create_line(0, i, w, i, fill="#333333")
        self.log("[渲染] 未找到背景图，使用棋盘格占位")


# ---------- 4. 主程序入口 ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = ImageDebugger(root)
    root.mainloop()