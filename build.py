import os
import shutil
import subprocess
import sys

def resource_path(relative_path):
    """require resource absolute path"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def main():
    print("Start building...")
    
    # clear old build resource
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # create tmp icon
    icon_path = resource_path(os.path.join("cat.ico"))
    if not os.path.exists(icon_path):
        print(f"Warning: icon not exist: {icon_path}")
        print("Using default icon...")
        icon_option = ""
    else:
        icon_option = f"--icon={icon_path}"
    
    # build cmd
    cmd = [
        "pyinstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        f"{icon_option}",
        "--name=PawTray",
        "--add-data=resources;resources",
        "main.py"
    ]
    
    # Filter out empty options
    cmd = [item for item in cmd if item]
    
    # Run build cmd
    print(f"Run cmd: {' '.join(cmd)}")
    subprocess.check_call(cmd)
    
    print("Build finished!")
    print("Output: dist/PawTray.exe")

if __name__ == "__main__":
    main()