import sys
import os
import random
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMenu, QAction, QSystemTrayIcon
from PyQt5.QtCore import Qt, QTimer, QSettings, QSize, QPoint, QEvent
from PyQt5.QtGui import QFont, QIcon, QFontDatabase, QPixmap, QMovie, QCursor

# 导入工具函数
from utils.resource_path import resource_path

# 导入组件
from components.info_bubble import InfoBubble
from components.reminders import ReminderManager
from components.screenshot import ScreenshotManager
from components.launcher import QuickLauncher
from components.weather import WeatherManager
from components.system_monitor import SystemMonitor
from components.display_settings import DisplaySettings

class TrayPet(QWidget):
    """只有系统托盘的宠物应用"""
    def __init__(self):
        super().__init__()
        
        # 检测是否是打包环境
        self.is_frozen = getattr(sys, 'frozen', False)
        
        # 设置窗口无边框和置顶
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 加载GIF动画
        self.animations = self.load_animations()
        self.current_animation = "idle"
        self.previous_animation = "idle"  # 记录上一个非休息状态的动画
        
        # 创建独立的信息气泡
        self.info_bubble = InfoBubble()
        
        # 添加悬浮显示气泡的设置
        self.hover_bubble = True
        self.show_bubble = False
        
        # 加载设置
        self.load_settings()
        
        # 初始化组件
        self.system_monitor = SystemMonitor(self)
        self.reminder_manager = ReminderManager(self)
        self.screenshot_manager = ScreenshotManager(self)
        self.launcher = QuickLauncher(self)
        self.weather_manager = WeatherManager(self)
        # 设置天气信息为待加载状态
        self.weather_manager.weather_info = "--"
        
        self.display_settings = DisplaySettings(self)
        
        # 创建系统托盘图标 - 在组件初始化之后创建，确保可以引用组件
        self.create_tray_icon()
        
        # 设置定时器进行系统监控和更新
        self.action_timer = QTimer(self)
        self.action_timer.timeout.connect(self.update_system_and_bubble)
        self.action_timer.start(5000)  # 每5秒更新一次
        
        # 设置动画切换定时器
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.switch_to_idle_animation)
        self.animation_timer.start(60000)  # 每1分钟切换一次
        
        # 设置天气更新定时器
        self.weather_timer = QTimer(self)
        self.weather_timer.timeout.connect(self.update_weather)
        # 延迟5秒后开始加载天气，然后每15分钟更新一次
        self.weather_timer.setSingleShot(True)
        self.weather_timer.start(5000)  # 5秒后加载天气
        
        # 记录是否处于休息状态
        self.is_resting = False
        
        # 设置鼠标跟踪定时器
        self.mouse_track_timer = QTimer(self)
        self.mouse_track_timer.timeout.connect(self.check_mouse_over_tray)
        self.mouse_track_timer.start(500)  # 每0.5秒检查一次
        
        # 记录鼠标是否在托盘图标上
        self.mouse_over_tray = False
        
        # 隐藏主窗口 - 只显示托盘图标
        self.hide()
        
        # print("宠物初始化完成 - 纯托盘模式")
    
    def load_animations(self):
        """加载所有GIF动画"""
        animations = {}
        
        # 直接检查resources目录
        resources_dir = resource_path("resources")
        # print(f"检查资源目录: {resources_dir}")
        
        if os.path.exists(resources_dir) and os.path.isdir(resources_dir):
            # 列出目录中的所有GIF文件
            gif_files = [f for f in os.listdir(resources_dir) if f.lower().endswith('.gif')]
            # print(f"找到GIF文件: {gif_files}")
            
            # 如果找到GIF文件，使用它们
            if gif_files:
                # 为每个GIF文件分配一个动画类型
                for gif_file in gif_files:
                    anim_type = gif_file.split('.')[0]  # 使用文件名作为动画类型
                    path = os.path.join(resources_dir, gif_file)
                    
                    try:
                        movie = QMovie(path)
                        if movie.isValid():
                            movie.setCacheMode(QMovie.CacheAll)
                            movie.setScaledSize(QSize(32, 32))  # 设置大小
                            animations[anim_type] = movie
                            # print(f"成功加载动画: {anim_type} ({path})")
                        else:
                            # print(f"动画文件无效: {path}")
                            pass
                    except Exception as e:
                        # print(f"加载动画失败: {path}, 错误: {e}")
                        pass
        else:
            # print(f"资源目录不存在: {resources_dir}")
            pass
        
        # 如果没有找到任何动画，使用备用方案
        if not animations:
            # print("未找到动画文件，使用emoji作为备用")
            return None
        
        return animations
    
    def load_settings(self):
        """加载设置"""
        try:
            settings = QSettings("PawTray", "Settings")
            
            # 加载显示模式设置
            hover_mode = settings.value("display/hover_mode", "hover")
            # print(f"加载显示模式设置: {hover_mode}")
            
            if hover_mode == "always":
                self.hover_bubble = False
                self.show_bubble = True
            elif hover_mode == "never":
                self.hover_bubble = False
                self.show_bubble = False
            else:  # hover
                self.hover_bubble = True
                self.show_bubble = False
            
            # print("成功加载设置")
        except Exception as e:
            # print(f"加载设置失败: {e}")
            pass
    
    def update_system_and_bubble(self):
        """更新系统信息和气泡内容"""
        # 更新托盘图标提示文本
        if hasattr(self, 'tray_icon'):
            self.tray_icon.setToolTip(f"CPU: {self.system_monitor.cpu_percent:.1f}% | 内存: {self.system_monitor.memory_percent:.1f}%")
        
        # 更新托盘菜单中的系统信息
        if hasattr(self, 'tray_cpu_action'):
            self.tray_cpu_action.setText(f"CPU: {self.system_monitor.cpu_percent:.1f}%")
        if hasattr(self, 'tray_memory_action'):
            self.tray_memory_action.setText(f"内存: {self.system_monitor.memory_percent:.1f}%")
        
        # 根据CPU使用率更改托盘图标动画
        self.update_tray_animation_by_cpu()
        
        # 更新气泡内容
        self.update_bubble_content()
    
    def update_tray_animation_by_cpu(self):
        """根据CPU使用率更新托盘图标动画"""
        if not self.animations:
            return
        
        if self.system_monitor.cpu_percent > 90:
            # 非常高的CPU使用率
            high_load_anims = [a for a in self.animations.keys() 
                              if a.lower() in ['cry', 'sad', 'surprised']]
            if high_load_anims:
                self.change_tray_animation(random.choice(high_load_anims))
        elif self.system_monitor.cpu_percent > 70:
            # 高CPU使用率
            medium_load_anims = [a for a in self.animations.keys() 
                                if a.lower() in ['waiting', 'excited']]
            if medium_load_anims:
                self.change_tray_animation(random.choice(medium_load_anims))
    
    def create_tray_icon(self):
        """创建系统托盘图标"""
        # 创建托盘图标
        self.tray_icon = QSystemTrayIcon(self)
        
        # 设置初始图标
        if self.animations:
            # 优先使用idle动画
            if 'idle' in self.animations:
                self.tray_movie = self.animations['idle']
            else:
                # 使用第一个可用的动画
                first_anim_type = list(self.animations.keys())[0]
                self.tray_movie = self.animations[first_anim_type]
            
            # 获取第一帧作为初始图标
            self.tray_movie.jumpToFrame(0)
            pixmap = QPixmap(self.tray_movie.currentPixmap())
            self.tray_icon.setIcon(QIcon(pixmap))
            
            # 设置帧变化处理
            self.tray_movie.frameChanged.connect(self.update_tray_icon)
            self.tray_movie.start()
        else:
            # 如果没有动画，使用默认图标
            self.tray_icon.setIcon(QIcon.fromTheme("applications-system"))
        
        # 创建托盘菜单
        self.tray_menu = QMenu()
        
        # 如果有动画，添加切换动画选项
        if self.animations:
            animation_menu = QMenu("切换动画", self)
            
            for anim_type in self.animations.keys():
                # 排除休息类动画，这些会自动切换
                if anim_type.lower() not in ['sleepy', 'laydown', 'sleep', 'rest', 'lazy']:
                    action = QAction(anim_type, self)
                    action.triggered.connect(lambda checked, a=anim_type: self.manual_change_animation(a))
                    animation_menu.addAction(action)
        
            self.tray_menu.addMenu(animation_menu)
        
        # 添加显示设置菜单
        if hasattr(self, 'display_settings') and hasattr(self.display_settings, 'display_menu'):
            self.tray_menu.addMenu(self.display_settings.display_menu)
        
        # 添加提醒菜单
        if hasattr(self, 'reminder_manager') and hasattr(self.reminder_manager, 'reminder_menu'):
            self.tray_menu.addMenu(self.reminder_manager.reminder_menu)
        
        # 添加快捷启动菜单
        if hasattr(self, 'launcher') and hasattr(self.launcher, 'launcher_menu'):
            self.tray_menu.addMenu(self.launcher.launcher_menu)
        
        # 添加截图选项
        if hasattr(self, 'screenshot_manager') and hasattr(self.screenshot_manager, 'screenshot_action'):
            self.tray_menu.addAction(self.screenshot_manager.screenshot_action)
        
        self.tray_menu.addSeparator()
        
        # 添加退出选项
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(QApplication.quit)
        self.tray_menu.addAction(exit_action)
        
        # 设置托盘菜单
        self.tray_icon.setContextMenu(self.tray_menu)
        
        # 设置托盘图标提示
        self.tray_icon.setToolTip("桌面宠物")
        
        # 显示托盘图标
        self.tray_icon.show()
        
        # 连接托盘图标的激活信号
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # 当前托盘动画
        self.current_tray_animation = "idle"
    
    def update_tray_icon(self):
        """更新托盘图标的帧"""
        if hasattr(self, 'tray_movie'):
            pixmap = QPixmap(self.tray_movie.currentPixmap())
            self.tray_icon.setIcon(QIcon(pixmap))
    
    def change_tray_animation(self, animation_type):
        """更改托盘图标动画"""
        if not self.animations:
            return
        
        if animation_type in self.animations:
            # 停止当前动画
            if hasattr(self, 'tray_movie'):
                self.tray_movie.stop()
            
            # 设置新动画
            self.tray_movie = self.animations[animation_type]
            self.tray_movie.frameChanged.connect(self.update_tray_icon)
            self.tray_movie.start()
            self.current_tray_animation = animation_type
            # print(f"切换托盘动画: {animation_type}")
        else:
            # print(f"找不到托盘动画类型: {animation_type}")
            pass
    
    def switch_to_idle_animation(self):
        """定时切换到休息动画"""
        if not self.animations:
            return
        
        # 如果鼠标在托盘图标上，不切换到休息状态
        if self.mouse_over_tray:
            return
        
        # 保存当前非休息状态的动画
        current_anim = self.current_tray_animation
        if current_anim.lower() not in ['sleepy', 'laydown', 'sleep', 'rest', 'lazy']:
            self.previous_animation = current_anim
        
        # 获取可用的休息动画
        rest_animations = [anim for anim in self.animations.keys() 
                          if anim.lower() in ['sleepy', 'laydown', 'sleep', 'rest', 'lazy']]
        
        if rest_animations:
            # 随机选择一个休息动画
            rest_anim = random.choice(rest_animations)
            self.change_tray_animation(rest_anim)
            self.is_resting = True
            # print(f"定时切换到休息动画: {rest_anim}")
        else:
            # 如果没有找到休息动画，使用idle
            if 'idle' in self.animations:
                self.change_tray_animation('idle')
                # print("没有找到休息动画，使用idle")
    
    def tray_icon_activated(self, reason):
        """处理托盘图标的激活事件"""
        if reason == QSystemTrayIcon.Trigger:  # 单击
            # 显示/隐藏气泡
            self.toggle_bubble()
        # elif reason == QSystemTrayIcon.DoubleClick:  # 双击
        #     # 双击时可以执行其他操作，例如显示设置
        #     if hasattr(self, 'display_settings'):
        #         self.display_settings.display_menu.exec_(QCursor.pos())
    
    def toggle_bubble(self):
        """切换气泡显示/隐藏状态"""
        if hasattr(self, 'info_bubble'):
            if self.info_bubble.isVisible():
                self.info_bubble.hide()
                self.show_bubble = False
                # print("气泡隐藏")
            else:
                self.update_bubble_content()
                self.update_bubble_position()
                
                # 设置气泡透明度
                self.info_bubble.setWindowOpacity(0.8)  # 设置为80%不透明度
                
                self.info_bubble.show()
                self.show_bubble = True
                # print("气泡显示")
    
    def update_bubble_position(self):
        """更新气泡位置 - 固定在托盘图标上方"""
        if hasattr(self, 'info_bubble') and hasattr(self, 'tray_icon'):
            # 获取托盘图标的位置
            geo = self.tray_icon.geometry()
            tray_pos = geo.topLeft()
            
            # 将气泡固定在托盘图标上方
            bubble_pos = QPoint(tray_pos)
            bubble_pos.setY(tray_pos.y() - self.info_bubble.height())
            
            # 水平居中
            bubble_pos.setX(tray_pos.x() + geo.width() // 2 - self.info_bubble.width() // 2)
            
            # 移动气泡到托盘图标上方
            self.info_bubble.move(bubble_pos)
            # print(f"气泡位置更新: {bubble_pos.x()}, {bubble_pos.y()}")
    
    def update_bubble_content(self):
        """更新气泡内容"""
        if not hasattr(self, 'info_bubble'):
            return
        
        content = "<div style='color: #FFFFFF;'>"  # 设置所有文字为白色
        
        # 添加系统信息
        if hasattr(self, 'system_monitor'):
            if hasattr(self, 'display_settings') and self.display_settings.display_options.get('cpu', True):
                content += f"<b>CPU:</b> {self.system_monitor.cpu_percent:.1f}%<br>"
            
            if hasattr(self, 'display_settings') and self.display_settings.display_options.get('memory', True):
                content += f"<b>内存:</b> {self.system_monitor.memory_percent:.1f}%<br>"
            
            if hasattr(self, 'display_settings') and self.display_settings.display_options.get('disk', False):
                content += f"<b>磁盘:</b> {self.system_monitor.disk_percent:.1f}%<br>"
            
            if hasattr(self, 'display_settings') and self.display_settings.display_options.get('network', False):
                content += f"<b>网络:</b> ↓{self.system_monitor.net_speed_down:.1f}KB/s ↑{self.system_monitor.net_speed_up:.1f}KB/s<br>"
        
        # 添加天气信息
        if hasattr(self, 'weather_manager') and hasattr(self, 'display_settings') and self.display_settings.display_options.get('weather', True):
            content += f"<b>天气:</b> {self.weather_manager.weather_info}<br>"
        
        # 添加时间信息
        if hasattr(self, 'display_settings') and self.display_settings.display_options.get('time', True):
            from datetime import datetime
            now = datetime.now()
            content += f"<b>时间:</b> {now.strftime('%H:%M:%S')}<br>"
            content += f"<b>日期:</b> {now.strftime('%Y-%m-%d')}<br>"
        
        content += "</div>"
        
        # 设置气泡内容
        self.info_bubble.setText(content)
        
        # 设置气泡背景颜色
        self.info_bubble.setStyleSheet("background-color: rgba(0, 0, 0, 180); border-radius: 10px; padding: 10px;")
    
    def show_display_settings(self):
        """显示显示设置菜单"""
        if hasattr(self, 'display_settings'):
            self.display_settings.display_menu.exec_(self.tray_icon.geometry().center())
    
    def show_reminder_settings(self):
        """显示提醒设置菜单"""
        if hasattr(self, 'reminder_manager'):
            self.reminder_manager.reminder_menu.exec_(self.tray_icon.geometry().center())
    
    def show_launcher_settings(self):
        """显示快捷启动设置菜单"""
        if hasattr(self, 'launcher'):
            self.launcher.launcher_menu.exec_(self.tray_icon.geometry().center())
    
    def take_screenshot(self):
        """截图"""
        if hasattr(self, 'screenshot_manager'):
            self.screenshot_manager.take_screenshot()

    def contextMenuEvent(self, event):
        """右键菜单 - 使用托盘菜单"""
        if hasattr(self, 'tray_menu'):
            self.tray_menu.exec_(event.globalPos())
        else:
            super().contextMenuEvent(event)

    def manual_change_animation(self, animation_type):
        """手动切换动画，并重置定时器"""
        # 保存非休息状态的动画
        if animation_type.lower() not in ['sleepy', 'laydown', 'sleep', 'rest', 'lazy']:
            self.previous_animation = animation_type
            self.is_resting = False
        else:
            self.is_resting = True
        
        self.change_tray_animation(animation_type)
        
        # 重置动画切换定时器
        if hasattr(self, 'animation_timer'):
            self.animation_timer.stop()
            self.animation_timer.start(60000)  # 重新开始1分钟计时

    def _show_launcher_menu(self):
        """显示快捷启动菜单"""
        if hasattr(self, 'launcher'):
            self.launcher.launcher_menu.exec_(QCursor.pos())

    def check_mouse_over_tray(self):
        """检查鼠标是否在托盘图标上"""
        if not hasattr(self, 'tray_icon'):
            return
        
        # 获取托盘图标的几何区域
        tray_geo = self.tray_icon.geometry()
        
        # 获取当前鼠标位置
        cursor_pos = QCursor.pos()
        
        # 检查鼠标是否在托盘图标上
        mouse_over = tray_geo.contains(cursor_pos)
        
        # 如果状态发生变化
        if mouse_over != self.mouse_over_tray:
            self.mouse_over_tray = mouse_over
            
            if mouse_over:
                # 鼠标进入托盘图标
                self.on_tray_icon_hover_enter()
            else:
                # 鼠标离开托盘图标
                self.on_tray_icon_hover_leave()

    def on_tray_icon_hover_enter(self):
        """鼠标悬停在托盘图标上时的处理"""
        # print("鼠标进入托盘图标区域")
        
        # 如果当前是休息状态，切换到之前的状态
        if self.is_resting:
            if self.previous_animation and self.previous_animation in self.animations:
                self.change_tray_animation(self.previous_animation)
                # print(f"鼠标悬停，从休息状态切换到: {self.previous_animation}")
            else:
                # 如果没有之前的状态，使用idle
                if 'idle' in self.animations:
                    self.change_tray_animation('idle')
                    # print("鼠标悬停，从休息状态切换到: idle")
        
        # 不再自动显示气泡
        # 移除了自动显示气泡的代码

    def on_tray_icon_hover_leave(self):
        """鼠标离开托盘图标时的处理"""
        # print("鼠标离开托盘图标区域")
        
        # 如果之前是休息状态，回到休息状态
        if self.is_resting:
            # 获取可用的休息动画
            rest_animations = [anim for anim in self.animations.keys() 
                              if anim.lower() in ['sleepy', 'laydown', 'sleep', 'rest', 'lazy']]
            
            if rest_animations:
                # 随机选择一个休息动画
                rest_anim = random.choice(rest_animations)
                self.change_tray_animation(rest_anim)
                # print(f"鼠标离开，回到休息状态: {rest_anim}")
        
        # 如果气泡是显示状态，自动隐藏
        if hasattr(self, 'info_bubble') and self.info_bubble.isVisible():
            self.info_bubble.hide()
            self.show_bubble = False
            # print("鼠标离开，自动隐藏气泡")

    def update_weather(self):
        """更新天气信息"""
        if hasattr(self, 'weather_manager'):
            # 调用天气管理器的更新方法
            self.weather_manager.update_weather()
            # print(f"天气信息已更新: {self.weather_manager.weather_info}")
            
            # 更新气泡内容
            if hasattr(self, 'info_bubble') and self.info_bubble.isVisible():
                self.update_bubble_content()
            
            # 如果是第一次加载天气，设置定期更新
            if self.weather_timer.isSingleShot():
                self.weather_timer.setSingleShot(False)
                self.weather_timer.start(900000)  # 15分钟 = 900000毫秒
                # print("天气更新定时器已设置为每15分钟更新一次")

    def closeEvent(self, event):
        """重写关闭事件处理函数，防止主窗口关闭导致程序退出"""
        # print("主窗口关闭事件被触发")
        # 如果是用户点击了关闭按钮，我们只隐藏窗口而不是关闭它
        if event.spontaneous():
            self.hide()
            event.ignore()
            # print("主窗口关闭事件被忽略，窗口已隐藏")
        else:
            # 如果是程序调用close()，我们允许关闭
            event.accept()
            # print("主窗口关闭事件被接受")

if __name__ == "__main__":
    # 创建应用程序对象
    app = QApplication(sys.argv)
    
    # 设置应用程序不会在最后一个窗口关闭时退出
    app.setQuitOnLastWindowClosed(False)
    
    # 加载字体
    font_path = resource_path(os.path.join("resources", "segoeui.ttf"))
    if os.path.exists(font_path):
        # print(f"字体文件存在: {font_path}")
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            # print("字体加载成功")
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            app.setFont(QFont(font_family, 10))
    
    # 创建托盘宠物
    pet = TrayPet()
    
    # 保持对托盘宠物的引用，防止被垃圾回收
    import builtins
    builtins._pet = pet
    
    # 启动事件循环
    sys.exit(app.exec_())