# -*- coding: utf-8 -*-
# 模块: ui/widgets

import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import gc
import sys
import re
import math
import copy
from PIL import Image, ImageTk
import logging


def filter_combobox(event, combobox, all_values):
    if hasattr(combobox, '_filter_after_id') and combobox._filter_after_id:
        try:
            combobox.after_cancel(combobox._filter_after_id)
        except ValueError:
            pass
    def do_filter():
        entry_text = combobox.get().lower()
        if not entry_text:
            combobox['values'] = all_values
        else:
            filtered = [item for item in all_values if entry_text in item.lower()]
            combobox['values'] = filtered
        combobox.after(10, lambda: combobox.event_generate('<Down>'))
        combobox._filter_after_id = None
    combobox._filter_after_id = combobox.after(300, do_filter)

