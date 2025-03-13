from PyQt5.QtWidgets import QAction, QApplication
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap
import datetime
import os

class ScreenshotManager:
    def __init__(self, pet):
        self.pet = pet
        self.setup_screenshot_feature()
    
    def setup_screenshot_feature(self):
        """设置屏幕截图功能"""
        self.screenshot_action = QAction("屏幕截图", self.pet)
        self.screenshot_action.triggered.connect(self.take_screenshot)
    
    def take_screenshot(self):
        """捕获屏幕截图"""
        # 临时隐藏宠物和气泡
        self.pet.hide()
        if hasattr(self.pet, 'info_bubble'):
            was_visible = self.pet.info_bubble.isVisible()
            self.pet.info_bubble.hide()
        
        # 等待一小段时间确保窗口完全隐藏
        QTimer.singleShot(200, lambda: self._capture_screen(was_visible))
    
    def _capture_screen(self, bubble_was_visible):
        """实际捕获屏幕的函数"""
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0)
        
        # 生成文件名
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        
        # 保存截图
        screenshot.save(filename, "PNG")
        
        # 显示宠物和气泡
        self.pet.show()
        if hasattr(self.pet, 'info_bubble') and bubble_was_visible:
            self.pet.info_bubble.show()
        
        # 显示成功消息
        if hasattr(self.pet, 'set_pet_animation'):
            self.pet.set_pet_animation("jump")  # 使用跳跃动画表示成功
        else:
            self.pet.pet_label.setText("📸")
        
        # 5秒后恢复正常表情
        QTimer.singleShot(5000, self.pet.update_pet_appearance)
        
        # 可选：打开截图
        os.startfile(os.path.abspath(filename))