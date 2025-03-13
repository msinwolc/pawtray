import os
import sys

def resource_path(relative_path):
    """获取资源的绝对路径，适用于开发环境和打包后的环境"""
    if getattr(sys, 'frozen', False):
        # 如果是打包后的应用
        base_path = sys._MEIPASS
    else:
        # 如果是开发环境
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)