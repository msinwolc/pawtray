from PyQt5.QtWidgets import QMenu, QAction, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTimeEdit, QSystemTrayIcon
from PyQt5.QtCore import QTimer, QTime, QObject

class ReminderManager:
    def __init__(self, pet):
        self.pet = pet
        self.setup_reminders()
        
        # 添加闪烁相关的属性
        self.is_blinking = False
        self.blink_timer = QTimer(self.pet)
        self.blink_timer.timeout.connect(self.toggle_blink_state)
        self.blink_state = False
        self.original_animation = None
        self.active_reminder_message = None  # 存储当前活动的提醒消息
            
    def setup_reminders(self):
        """设置任务提醒功能"""
        self.reminders = []
        
        # 添加提醒菜单
        self.reminder_menu = QMenu("提醒", self.pet)
        
        add_reminder_action = QAction("添加提醒", self.pet)
        add_reminder_action.triggered.connect(self.add_reminder)
        self.reminder_menu.addAction(add_reminder_action)
        
        self.reminder_menu.addSeparator()
        
        # 检查提醒的定时器
        self.reminder_timer = QTimer(self.pet)
        self.reminder_timer.timeout.connect(self.check_reminders)
        self.reminder_timer.start(60000)  # 每分钟检查一次
        
        # 设置托盘图标事件处理
        if hasattr(self.pet, 'tray_icon'):
            # 保存原始工具提示
            self.original_tooltip = self.pet.tray_icon.toolTip()
            
            # 连接鼠标激活事件
            self.pet.tray_icon.activated.connect(self.handle_tray_activation)
    
    def toggle_blink_state(self):
        """切换闪烁状态"""
        if not self.is_blinking:
            return
        
        self.blink_state = not self.blink_state
        
        if self.blink_state:
            # 隐藏图标（设置为透明）
            if hasattr(self.pet, 'tray_icon'):
                from PyQt5.QtGui import QIcon, QPixmap
                from PyQt5.QtCore import Qt
                empty_pixmap = QPixmap(16, 16)
                empty_pixmap.fill(Qt.transparent)
                self.pet.tray_icon.setIcon(QIcon(empty_pixmap))
                
                # 设置提醒内容为工具提示
                if self.active_reminder_message:
                    self.pet.tray_icon.setToolTip(f"提醒: {self.active_reminder_message}")
        else:
            # 显示图标
            if hasattr(self.pet, 'tray_icon') and hasattr(self.pet, 'tray_movie'):
                from PyQt5.QtGui import QIcon
                pixmap = self.pet.tray_movie.currentPixmap()
                self.pet.tray_icon.setIcon(QIcon(pixmap))
                
                # 设置提醒内容为工具提示
                if self.active_reminder_message:
                    self.pet.tray_icon.setToolTip(f"提醒: {self.active_reminder_message}")

    def handle_tray_activation(self, reason):
        """处理托盘图标激活事件"""
        # QSystemTrayIcon.Trigger 表示单击
        # QSystemTrayIcon.Context 表示右键点击
        # QSystemTrayIcon.DoubleClick 表示双击
        # QSystemTrayIcon.MiddleClick 表示中键点击
        # QSystemTrayIcon.Unknown 表示未知原因
                
        # 当用户与托盘图标交互时停止闪烁
        if self.is_blinking:
            self.stop_blinking()
            
            # 确保图标恢复正常
            if hasattr(self.pet, 'tray_icon') and hasattr(self.pet, 'tray_movie'):
                from PyQt5.QtGui import QIcon
                pixmap = self.pet.tray_movie.currentPixmap()
                self.pet.tray_icon.setIcon(QIcon(pixmap))
            
            # 确保工具提示恢复正常
            if hasattr(self.pet, 'tray_icon') and hasattr(self, 'original_tooltip'):
                self.pet.tray_icon.setToolTip(self.original_tooltip)
    
    def start_blinking(self, message):
        """开始托盘图标闪烁，直到用户交互
        
        Args:
            message: 提醒消息，将显示在工具提示中
        """
        if self.is_blinking:
            return  # 已经在闪烁中
                
        # 保存当前动画状态和工具提示
        if hasattr(self.pet, 'current_tray_animation'):
            self.original_animation = self.pet.current_tray_animation
        
        if hasattr(self.pet, 'tray_icon'):
            self.original_tooltip = self.pet.tray_icon.toolTip()
        
        # 设置活动提醒消息
        self.active_reminder_message = message
        
        # 设置工具提示显示提醒内容
        if hasattr(self.pet, 'tray_icon') and self.active_reminder_message:
            self.pet.tray_icon.setToolTip(f"提醒: {self.active_reminder_message}")
        
        self.is_blinking = True
        self.blink_state = False
        
        # 开始闪烁定时器 (每500毫秒切换一次)
        self.blink_timer.start(500)
        
        # 测试托盘图标激活事件是否正常连接
        if hasattr(self.pet, 'tray_icon'):            
            # 手动连接一次，以防之前的连接失效
            try:
                self.pet.tray_icon.activated.disconnect(self.handle_tray_activation)
            except:
                pass  # 如果没有连接，会抛出异常，忽略它
            
            self.pet.tray_icon.activated.connect(self.handle_tray_activation)

    def stop_blinking(self):
        """停止托盘图标闪烁"""
        if not self.is_blinking:
            return
        
        # 停止闪烁定时器
        self.blink_timer.stop()
        
        self.is_blinking = False
        
        # 恢复原来的动画
        if self.original_animation and hasattr(self.pet, 'change_tray_animation'):
            self.pet.change_tray_animation(self.original_animation)
            self.original_animation = None
        
        # 恢复原始工具提示
        if hasattr(self.pet, 'tray_icon') and hasattr(self, 'original_tooltip'):
            self.pet.tray_icon.setToolTip(self.original_tooltip)
        
        # 清除活动提醒消息
        self.active_reminder_message = None
        
        # 确保图标恢复正常
        if hasattr(self.pet, 'tray_icon') and hasattr(self.pet, 'tray_movie'):
            from PyQt5.QtGui import QIcon
            pixmap = self.pet.tray_movie.currentPixmap()
            self.pet.tray_icon.setIcon(QIcon(pixmap))

    def add_reminder(self):
        """添加新提醒"""
        from PyQt5.QtWidgets import QMessageBox
        
        dialog = QDialog(self.pet)
        dialog.setWindowTitle("添加提醒")
        
        layout = QVBoxLayout()
        
        # 提醒内容
        content_layout = QHBoxLayout()
        content_layout.addWidget(QLabel("提醒内容:"))
        content_edit = QLineEdit()
        content_layout.addWidget(content_edit)
        layout.addLayout(content_layout)
        
        # 提醒时间
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("提醒时间:"))
        time_edit = QTimeEdit()
        time_edit.setTime(QTime.currentTime().addSecs(3600))  # 默认1小时后
        time_layout.addWidget(time_edit)
        layout.addLayout(time_layout)
        
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
            content = content_edit.text()
            time = time_edit.time()
            
            if content:
                # 添加到提醒列表
                self.reminders.append({
                    "content": content,
                    "time": time,
                    "active": True
                })
                
                # 添加到提醒菜单
                reminder_action = QAction(f"{time.toString('HH:mm')} - {content}", self.pet)
                reminder_action.setCheckable(True)
                reminder_action.setChecked(True)
                self.reminder_menu.addAction(reminder_action)
    
    def check_reminders(self):
        """检查是否有到期的提醒"""
        from PyQt5.QtWidgets import QMessageBox, QSystemTrayIcon
        import random
        
        try:
            current_time = QTime.currentTime()
            
            for reminder in self.reminders:
                if reminder["active"]:
                    reminder_time = reminder["time"]
                    
                    # 检查时间是否匹配（分钟级别）
                    if (reminder_time.hour() == current_time.hour() and 
                        reminder_time.minute() == current_time.minute()):
                        
                        # 显示系统通知
                        self.show_notification(reminder["content"])
                        
                        # 开始托盘图标闪烁
                        self.start_blinking(reminder["content"])
                        
                        # 5秒后恢复正常表情
                        if hasattr(self.pet, 'update_pet_appearance'):
                            QTimer.singleShot(5000, self.pet.update_pet_appearance)
                        
                        # 标记为已提醒
                        reminder["active"] = False
        except Exception as e:
            print(f"检查提醒时出错: {e}")
    
    def show_notification(self, message):
        """显示系统通知"""
        from PyQt5.QtWidgets import QSystemTrayIcon
        import random
        
        try:
            # 如果有托盘图标，使用它显示通知
            if hasattr(self.pet, 'tray_icon'):
                self.pet.tray_icon.showMessage("提醒", message, QSystemTrayIcon.Information, 5000)
                
                # 如果有动画，切换到提醒动画
                if hasattr(self.pet, 'animations'):
                    # 尝试使用惊讶或兴奋的动画
                    surprise_anims = [a for a in self.pet.animations.keys() 
                                    if a.lower() in ['surprised', 'excited', 'happy', 'jump']]
                    if surprise_anims:
                        anim_type = random.choice(surprise_anims)
                        if hasattr(self.pet, 'manual_change_animation'):
                            self.pet.manual_change_animation(anim_type)
            else:
                # 如果没有托盘图标，使用标准的消息框
                from PyQt5.QtWidgets import QMessageBox
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("提醒")
                msg.setText(message)
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
        except Exception as e:
            print(f"显示通知时出错: {e}")