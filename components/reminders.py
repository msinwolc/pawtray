from PyQt5.QtWidgets import QMenu, QAction, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTimeEdit
from PyQt5.QtCore import QTimer, QTime

class ReminderManager:
    def __init__(self, pet):
        self.pet = pet
        self.setup_reminders()
    
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
                        
                        # 5秒后恢复正常表情
                        if hasattr(self.pet, 'update_pet_appearance'):
                            QTimer.singleShot(5000, self.pet.update_pet_appearance)
                        
                        # 标记为已提醒
                        reminder["active"] = False
        except Exception as e:
            # print(f"检查提醒时出错: {e}")
            pass

    def show_notification(self, message):
        """显示系统通知"""
        from PyQt5.QtWidgets import QSystemTrayIcon
        import random
        
        try:
            # 如果有托盘图标，使用它显示通知
            if hasattr(self.pet, 'tray_icon'):
                self.pet.tray_icon.showMessage("提醒", message, QSystemTrayIcon.Information, 5000)
                # print(f"托盘通知: {message}")
                
                # 如果有动画，切换到提醒动画
                if hasattr(self.pet, 'animations'):
                    # 尝试使用惊讶或兴奋的动画
                    surprise_anims = [a for a in self.pet.animations.keys() 
                                    if a.lower() in ['surprised', 'excited', 'happy', 'jump']]
                    if surprise_anims:
                        anim_type = random.choice(surprise_anims)
                        if hasattr(self.pet, 'manual_change_animation'):
                            self.pet.manual_change_animation(anim_type)
                            print(f"切换到动画: {anim_type}")
            else:
                # 如果没有托盘图标，使用标准的消息框
                from PyQt5.QtWidgets import QMessageBox
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("提醒")
                msg.setText(message)
                msg.setStandardButtons(QMessageBox.Ok)
                msg.exec_()
                # print(f"消息框通知: {message}")
        except Exception as e:
            # print(f"显示通知时出错: {e}")
            pass