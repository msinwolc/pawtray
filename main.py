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
        
        # 设置天气更新定时器 - 使用持续运行的定时器
        self.weather_timer = QTimer(self)
        self.weather_timer.timeout.connect(self.update_weather)
        # 延迟5秒后开始加载天气，然后每15分钟更新一次
        QTimer.singleShot(5000, self.initial_weather_update)  # 5秒后初始加载
        
        # 记录是否处于休息状态
        self.is_resting = False
        
        # 设置鼠标跟踪定时器
        self.mouse_track_timer = QTimer(self)
        self.mouse_track_timer.timeout.connect(self.check_mouse_over_tray)
        self.mouse_track_timer.start(500)  # 每0.5秒检查一次
        
        # 记录鼠标是否在托盘图标上
        self.mouse_over_tray = False
        
        # print("宠物初始化完成 - 纯托盘模式")
    
    def load_animations(self):
        """加载所有GIF动画"""
        animations = {}
        
        # 直接检查resources目录
        resources_dir = resource_path("resources")
        
        if os.path.exists(resources_dir) and os.path.isdir(resources_dir):
            # 列出目录中的所有GIF文件
            gif_files = [f for f in os.listdir(resources_dir) if f.lower().endswith('.gif')]
            
            # 如果找到GIF文件，使用它们
            if gif_files:
                # 为每个GIF文件分配一个动画类型
                for gif_file in gif_files:
                    anim_type = gif_file.split('.')[0]  # 使用文件名作为动画类型
                    path = os.path.join(resources_dir, gif_file)
                    
                    try:
                        movie = QMovie(path)
                        if movie.isValid():
                            # 增加缓存模式和质量设置
                            movie.setCacheMode(QMovie.CacheAll)
                            # 设置更新速率，减少闪烁
                            movie.setSpeed(100)  # 100%的正常速度
                            movie.setScaledSize(QSize(32, 32))  # 设置大小
                            animations[anim_type] = movie
                        else:
                            pass
                    except Exception as e:
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
        """更新系统信息和气泡内容 - 确保同步更新"""
        # 不需要再调用异步更新，因为SystemMonitor已经在后台持续更新
        # 只需要使用最新的数据更新UI
        
        # 更新托盘图标提示文本
        if hasattr(self, 'tray_icon') and hasattr(self, 'system_monitor'):
            # 使用系统监控的最新数据
            cpu = self.system_monitor.cpu_percent
            memory = self.system_monitor.memory_percent
            self.tray_icon.setToolTip(f"CPU: {cpu:.1f}% | 内存: {memory:.1f}%")
        
        # 更新托盘菜单中的系统信息
        if hasattr(self, 'tray_cpu_action') and hasattr(self, 'system_monitor'):
            self.tray_cpu_action.setText(f"CPU: {self.system_monitor.cpu_percent:.1f}%")
        if hasattr(self, 'tray_memory_action') and hasattr(self, 'system_monitor'):
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

        # 添加开机自启动选项
        self.autostart_action = QAction("开机自启动", self)
        self.autostart_action.setCheckable(True)
        self.autostart_action.setChecked(self.is_autostart_enabled())
        self.autostart_action.triggered.connect(self.toggle_autostart_action)
        self.tray_menu.addAction(self.autostart_action)
        
        self.tray_menu.addSeparator()
        
        # 添加退出选项
        exit_action = QAction("退出", self)
        exit_action.triggered.connect(QApplication.quit)
        self.tray_menu.addAction(exit_action)
        
        # 设置托盘菜单
        self.tray_icon.setContextMenu(self.tray_menu)
        
        # 设置托盘图标提示
        # self.tray_icon.setToolTip("桌面宠物")
        
        # 显示托盘图标
        self.tray_icon.show()
        
        # 连接托盘图标的激活信号
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # 当前托盘动画
        self.current_tray_animation = "idle"

    def toggle_autostart_action(self, checked):
        """处理开机自启动选项的点击事件"""
        success = self.toggle_autostart(checked)
        if not success:
            # 如果设置失败，恢复复选框状态
            self.autostart_action.setChecked(not checked)
    
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
                # 断开之前的连接，防止信号累积
                try:
                    self.tray_movie.frameChanged.disconnect(self.update_tray_icon)
                except:
                    pass
            
            # 设置新动画
            self.tray_movie = self.animations[animation_type]
            # 重新连接信号
            self.tray_movie.frameChanged.connect(self.update_tray_icon)
            # 重置动画到第一帧
            self.tray_movie.jumpToFrame(0)
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
        """更新气泡内容 - 确保使用最新数据"""
        if not hasattr(self, 'info_bubble'):
            return
        
        try:
            # 预先准备内容字符串，避免多次字符串连接
            content_parts = ["<div style='color: #FFFFFF;'>"]  # 设置所有文字为白色
            
            # 添加系统信息 - 直接使用system_monitor的最新数据
            if hasattr(self, 'system_monitor'):
                # 获取最新数据
                cpu = self.system_monitor.cpu_percent
                memory = self.system_monitor.memory_percent
                disk = self.system_monitor.disk_percent
                net_up = self.system_monitor.net_speed_up
                net_down = self.system_monitor.net_speed_down
                
                if hasattr(self, 'display_settings') and self.display_settings.display_options.get('cpu', True):
                    content_parts.append(f"<b>CPU:</b> {cpu:.1f}%<br>")
                
                if hasattr(self, 'display_settings') and self.display_settings.display_options.get('memory', True):
                    content_parts.append(f"<b>内存:</b> {memory:.1f}%<br>")
                
                if hasattr(self, 'display_settings') and self.display_settings.display_options.get('disk', False):
                    content_parts.append(f"<b>磁盘:</b> {disk:.1f}%<br>")
                
                if hasattr(self, 'display_settings') and self.display_settings.display_options.get('network', False):
                    content_parts.append(f"<b>网络:</b> ↓{net_down:.1f}KB/s ↑{net_up:.1f}KB/s<br>")
            
            # 添加天气信息
            if hasattr(self, 'weather_manager') and hasattr(self, 'display_settings') and self.display_settings.display_options.get('weather', True):
                content_parts.append(f"<b>天气:</b> {self.weather_manager.weather_info}<br>")
            
            # 添加本地IP地址信息
            if hasattr(self, 'display_settings') and self.display_settings.display_options.get('ip', True):
                local_ip = self.get_local_ip()
                content_parts.append(f"<b>本地IP:</b> {local_ip}<br>")
            
            content_parts.append("</div>")
            
            # 一次性连接所有内容
            content = "".join(content_parts)
            
            # 设置气泡内容
            self.info_bubble.setText(content)
            
            # 设置气泡背景颜色
            self.info_bubble.setStyleSheet("background-color: rgba(0, 0, 0, 180); border-radius: 10px; padding: 10px;")
        except Exception as e:
            print(f"更新气泡内容时出错: {e}")
    
    def get_local_ip(self):
        """获取本地IP地址（192.168开头）"""
        import socket
        try:
            # 创建一个临时socket连接来获取本地IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # 不需要真正连接
            s.connect(('8.8.8.8', 1))
            local_ip = s.getsockname()[0]
            s.close()
            
            # 只返回192开头的IP
            if local_ip.startswith('192.'):
                return local_ip
            else:
                # 尝试获取所有网络接口
                for interface in socket.getaddrinfo(socket.gethostname(), None):
                    ip = interface[4][0]
                    if ip.startswith('192.'):
                        return ip
                
                return "未找到192开头的IP"
        except Exception as e:
            print(f"获取本地IP出错: {e}")
            return "获取IP失败"
    
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

    def initial_weather_update(self):
        """初始天气更新并启动定期更新"""
        if hasattr(self, 'weather_manager'):
            self.weather_manager.update_weather()
        
        # 启动定期更新定时器（每15分钟）
        if hasattr(self, 'weather_timer'):
            self.weather_timer.start(15 * 60 * 1000)  # 15分钟 = 900,000毫秒
            # self.weather_timer.start(30 * 1000)  # 本地测试，30秒
            # print("天气定时更新已启动，间隔15分钟")

    def update_weather(self):
        """定期更新天气信息"""
        if hasattr(self, 'weather_manager'):
            self.weather_manager.update_weather()
            print("定时天气更新已执行")

    def closeEvent(self, event):
        """处理窗口关闭事件"""
        # 停止所有线程
        if hasattr(self, 'system_monitor'):
            self.system_monitor.stop()
        
        if hasattr(self, 'weather_manager') and hasattr(self.weather_manager, 'stop'):
            self.weather_manager.stop()
        
        # 接受关闭事件
        event.accept()

    def toggle_autostart(self, enabled):
        """启用或禁用开机自启动"""
        import os
        import sys
        import winreg as reg
        
        try:
            # 获取当前执行文件的路径
            if getattr(sys, 'frozen', False):
                # PyInstaller打包后的路径
                app_path = sys.executable
            else:
                # 开发环境中的路径
                app_path = os.path.abspath(sys.argv[0])
            
            # 打开注册表键
            key = reg.OpenKey(
                reg.HKEY_CURRENT_USER, 
                r"Software\Microsoft\Windows\CurrentVersion\Run", 
                0, 
                reg.KEY_SET_VALUE | reg.KEY_QUERY_VALUE
            )
            
            app_name = "PawTray"
            
            if enabled:
                # 添加到开机自启动
                reg.SetValueEx(key, app_name, 0, reg.REG_SZ, f'"{app_path}"')
                # print(f"已添加到开机自启动: {app_path}")
            else:
                # 从开机自启动中移除
                try:
                    reg.DeleteValue(key, app_name)
                    # print("已从开机自启动中移除")
                except FileNotFoundError:
                    # 如果键不存在，忽略错误
                    pass
            
            reg.CloseKey(key)
            return True
        except Exception as e:
            # print(f"设置开机自启动失败: {e}")
            return False

    def is_autostart_enabled(self):
        """检查是否已启用开机自启动"""
        import sys
        import winreg as reg
        
        try:
            # 获取当前执行文件的路径
            if getattr(sys, 'frozen', False):
                # PyInstaller打包后的路径
                app_path = sys.executable
            else:
                # 开发环境中的路径
                app_path = os.path.abspath(sys.argv[0])
            
            # 打开注册表键
            key = reg.OpenKey(
                reg.HKEY_CURRENT_USER, 
                r"Software\Microsoft\Windows\CurrentVersion\Run", 
                0, 
                reg.KEY_QUERY_VALUE
            )
            
            app_name = "PawTray"
            
            try:
                value, _ = reg.QueryValueEx(key, app_name)
                # 检查路径是否匹配
                is_enabled = f'"{app_path}"' == value
            except FileNotFoundError:
                is_enabled = False
            
            reg.CloseKey(key)
            return is_enabled
        except Exception as e:
            # print(f"检查开机自启动失败: {e}")
            return False

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