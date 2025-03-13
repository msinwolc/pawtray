import os
import shutil
import subprocess
import sys

def resource_path(relative_path):
    """获取资源的绝对路径"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def main():
    print("开始打包桌面宠物应用...")
    
    # 清理之前的构建文件
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # 创建临时图标文件
    icon_path = resource_path(os.path.join("cat.ico"))
    if not os.path.exists(icon_path):
        print(f"警告: 图标文件不存在: {icon_path}")
        print("使用默认图标...")
        icon_option = ""
    else:
        icon_option = f"--icon={icon_path}"
    
    # 构建命令
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        f"{icon_option}",
        "--name=DesktopPet",
        "--add-data=resources;resources",
        "main.py"
    ]
    
    # 过滤掉空选项
    cmd = [item for item in cmd if item]
    
    # 执行打包命令
    print(f"执行命令: {' '.join(cmd)}")
    subprocess.call(cmd)
    
    print("打包完成!")
    print("可执行文件位于: dist/pawtray.exe")

if __name__ == "__main__":
    main()