# -*- coding: utf-8 -*-
# 模块: utils/image_cache

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


IMAGE_CACHE = {}

def load_photo_image(path, size=None):
    key = (os.path.abspath(path), None if size is None else tuple(size))
    if key in IMAGE_CACHE:
        return IMAGE_CACHE[key]
    try:
        img = Image.open(path)
        if size:
            img = img.resize(size, Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        IMAGE_CACHE[key] = photo
        return photo
    except Exception as e:
        logging.debug("加载图片失败 %s -> %s", path, e)
        return None

