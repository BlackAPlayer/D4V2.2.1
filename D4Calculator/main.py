#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""D4计算器 V2.2.1 - 模块化入口"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from ui.main_window import DiabloCalculator
import tkinter as tk

if __name__ == '__main__':
    root = tk.Tk()
    root.title('D4计算器 V2.2.1')
    root.geometry('750x800')
    root.configure(bg='#1a0505')
    app = DiabloCalculator(root)
    root.mainloop()
