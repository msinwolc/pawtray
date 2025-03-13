from PyQt5.QtWidgets import QMenu, QAction, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog
from PyQt5.QtCore import QTimer
import subprocess

class QuickLauncher:
    def __init__(self, pet):
        self.pet = pet
        self.setup_quick_launcher()
    
    def setup_quick_launcher(self):
        """设置快捷启动器"""
        # 创建快捷启动菜单
        self.launcher_menu = QMenu("快捷启动", self.pet)
        
        # 添加常用应用
        apps = {
            "浏览器": {
                "command": "start chrome",
                "icon": "🌐"
            },
            "记事本": {
                "command": "notepad",
                "icon": "📝"
            },
            "计算器": {
                "command": "calc",
                "icon": "🧮"
            },
            "资源管理器": {
                "command": "explorer",
                "icon": "📂"
            }
        }
        
        for name, info in apps.items():
            action = QAction(f"{info['icon']} {name}", self.pet)
            action.setData(info["command"])
            action.triggered.connect(self.launch_app)
            self.launcher_menu.addAction(action)
        
        # 添加自定义应用选项
        self.launcher_menu.addSeparator()
        add_custom_action = QAction("添加自定义应用...", self.pet)
        add_custom_action.triggered.connect(self.add_custom_app)
        self.launcher_menu.addAction(add_custom_action)
    
    def launch_app(self):
        """启动应用程序"""
        action = self.pet.sender()
        if action:
            command = action.data()
            try:
                subprocess.Popen(command, shell=True)
                
                # 更改宠物表情
                if hasattr(self.pet, 'set_pet_animation'):
                    self.pet.set_pet_animation("walk")  # 使用行走动画表示启动应用
                else:
                    self.pet.pet_label.setText("🚀")
                    
                QTimer.singleShot(1000, self.pet.update_pet_appearance)
            except Exception as e:
                print(f"启动应用失败: {e}")
    
    def add_custom_app(self):
        """添加自定义应用"""
        dialog = QDialog(self.pet)
        dialog.setWindowTitle("添加自定义应用")
        
        layout = QVBoxLayout()
        
        # 应用名称
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("名称:"))
        name_edit = QLineEdit()
        name_layout.addWidget(name_edit)
        layout.addLayout(name_layout)
        
        # 应用路径
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("路径:"))
        path_edit = QLineEdit()
        path_layout.addWidget(path_edit)
        browse_button = QPushButton("浏览...")
        
        def browse_file():
            file_path, _ = QFileDialog.getOpenFileName(dialog, "选择应用程序", "", "可执行文件 (*.exe)")
            if file_path:
                path_edit.setText(file_path)
        
        browse_button.clicked.connect(browse_file)
        path_layout.addWidget(browse_button)
        layout.addLayout(path_layout)
        
        # 确定和取消按钮
        buttons_layout = QHBoxLayout()
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(dialog.reject)
        ok_button = QPushButton("确定")
        ok_button.clicked.connect(dialog.accept)
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(ok_button)
        layout.addLayout(buttons_layout)
        
        dialog.setLayout(layout)
        
        if dialog.exec_():
            name = name_edit.text()
            path = path_edit.text()
            
            if name and path:
                action = QAction(f"🔹 {name}", self.pet)
                action.setData(path)
                action.triggered.connect(self.launch_app)
                self.launcher_menu.addAction(action)