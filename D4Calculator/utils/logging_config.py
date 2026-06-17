# -*- coding: utf-8 -*-
# 模块: utils/logging_config

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


logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
