from PyQt5.QtWidgets import QMenu, QAction, QDialog, QVBoxLayout, QCheckBox, QPushButton, QHBoxLayout, QLabel
from PyQt5.QtCore import QSettings

class DisplaySettings:
    def __init__(self, pet):
        self.pet = pet
        
        # 默认显示设置
        self.display_options = {
            'cpu': True,
            'memory': True,
            'disk': False,
            'network': False,
            'weather': False,
            'time': False,
            'battery': False
        }

        # 气泡位置设置
        self.bubble_position = 'top'  # 'top', 'bottom', 'left', 'right'
        
        # 加载保存的设置
        self.load_settings()
        
        # 创建设置菜单
        self.setup_display_settings()
    
    def setup_display_settings(self):
        """设置显示内容选项"""
        self.display_menu = QMenu("显示设置", self.pet)
        
        # 添加自定义显示选项
        customize_action = QAction("自定义显示内容...", self.pet)
        customize_action.triggered.connect(self.show_display_dialog)
        self.display_menu.addAction(customize_action)
        
        # 添加预设
        self.display_menu.addSeparator()
        
        minimal_action = QAction("最小化显示 (仅CPU)", self.pet)
        minimal_action.triggered.connect(lambda: self.apply_preset('minimal'))
        self.display_menu.addAction(minimal_action)
        
        standard_action = QAction("标准显示 (CPU+内存)", self.pet)
        standard_action.triggered.connect(lambda: self.apply_preset('standard'))
        self.display_menu.addAction(standard_action)
        
        full_action = QAction("完整显示 (所有信息)", self.pet)
        full_action.triggered.connect(lambda: self.apply_preset('full'))
        self.display_menu.addAction(full_action)

    def set_bubble_position(self, position):
        """设置气泡位置"""
        self.bubble_position = position
        self.save_settings()
        self.pet.update_bubble_position()
    
    def save_settings(self):
        """保存显示设置到配置文件"""
        try:
            settings = QSettings("PawTray", "DisplaySettings")
            
            # 保存显示选项
            for key, value in self.display_options.items():
                settings.setValue(f"display/{key}", value)
            
            # 保存气泡位置
            settings.setValue("display/bubble_position", self.bubble_position)
            
            print(f"保存气泡位置设置: {self.bubble_position}")
        except Exception as e:
            print(f"保存显示设置失败: {e}")

    def load_settings(self):
        """从配置文件加载显示设置"""
        try:
            settings = QSettings("PawTray", "DisplaySettings")
            
            # 加载显示选项
            for key in self.display_options.keys():
                if settings.contains(f"display/{key}"):
                    self.display_options[key] = settings.value(f"display/{key}", type=bool)
            
            # 加载气泡位置
            if settings.contains("display/bubble_position"):
                self.bubble_position = settings.value("display/bubble_position", type=str)
                print(f"加载气泡位置设置: {self.bubble_position}")
            else:
                print("未找到气泡位置设置，使用默认值")
        except Exception as e:
            print(f"加载显示设置失败: {e}")
    
    def show_display_dialog(self):
        """显示自定义显示内容对话框"""
        dialog = QDialog(self.pet)
        dialog.setWindowTitle("自定义显示内容")
        
        layout = QVBoxLayout()
        
        # 添加标题
        title_label = QLabel("选择要在气泡中显示的信息:")
        layout.addWidget(title_label)
        
        # 创建复选框
        checkboxes = {}
        
        options = [
            ('cpu', 'CPU使用率'),
            ('memory', '内存使用率'),
            ('disk', '磁盘使用率'),
            ('network', '网络速度'),
            ('weather', '天气信息'),
            ('time', '当前时间'),
            ('battery', '电池状态')
        ]
        
        for key, label in options:
            checkbox = QCheckBox(label)
            checkbox.setChecked(self.display_options.get(key, False))
            checkboxes[key] = checkbox
            layout.addWidget(checkbox)
        
        # 添加按钮
        buttons_layout = QHBoxLayout()
        
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(dialog.reject)
        
        apply_button = QPushButton("应用")
        apply_button.setDefault(True)
        
        def on_apply():
            # 保存设置
            for key, checkbox in checkboxes.items():
                self.display_options[key] = checkbox.isChecked()
            
            # 保存到配置
            self.save_settings()
            
            # 更新显示
            self.pet.update_bubble_content()
            
            dialog.accept()
        
        apply_button.clicked.connect(on_apply)
        
        buttons_layout.addWidget(cancel_button)
        buttons_layout.addWidget(apply_button)
        
        layout.addLayout(buttons_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def apply_preset(self, preset):
        """应用预设显示设置"""
        # 重置所有选项
        for key in self.display_options:
            self.display_options[key] = False
        
        # 应用预设
        if preset == 'minimal':
            self.display_options['cpu'] = True
        elif preset == 'standard':
            self.display_options['cpu'] = True
            self.display_options['memory'] = True
        elif preset == 'full':
            for key in self.display_options:
                self.display_options[key] = True
        
        # 保存设置
        self.save_settings()
        
        # 更新显示
        self.pet.update_bubble_content()