import psutil
import time
from PyQt5.QtCore import QTimer

class SystemMonitor:
    def __init__(self, pet):
        self.pet = pet
        
        # 缓存系统信息，确保所有地方使用相同的数据
        self.cpu_percent = 0
        self.memory_percent = 0
        self.disk_percent = 0
        self.net_speed_down = 0
        self.net_speed_up = 0
        
        # 初始化网络监控变量
        self.last_net_io = psutil.net_io_counters()
        self.last_net_time = time.time()
        
        # 设置定时器进行系统监控
        self.system_timer = QTimer(self.pet)
        self.system_timer.timeout.connect(self.update_system_info)
        self.system_timer.start(2000)  # 每2秒更新一次系统信息
        
        # 立即更新一次系统信息（但不调用宠物的方法）
        self.update_system_info_initial()
    
    def update_system_info_initial(self):
        """初始化时更新系统信息，但不调用宠物的方法"""
        # 获取CPU使用率
        self.cpu_percent = psutil.cpu_percent(interval=0.5)
        
        # 获取内存使用率
        memory = psutil.virtual_memory()
        self.memory_percent = memory.percent
        
        # 获取磁盘使用率
        disk = psutil.disk_usage('/')
        self.disk_percent = disk.percent
        
        # 获取网络信息已在__init__中初始化
    
    def update_system_info(self):
        """更新系统信息"""
        # 获取CPU使用率
        self.cpu_percent = psutil.cpu_percent(interval=0.5)
        
        # 获取内存使用率
        memory = psutil.virtual_memory()
        self.memory_percent = memory.percent
        
        # 获取磁盘使用率
        disk = psutil.disk_usage('/')
        self.disk_percent = disk.percent
        
        # 获取网络信息
        net_io = psutil.net_io_counters()
        current_time = time.time()
        
        time_delta = current_time - self.last_net_time
        self.net_speed_down = (net_io.bytes_recv - self.last_net_io.bytes_recv) / time_delta / 1024  # KB/s
        self.net_speed_up = (net_io.bytes_sent - self.last_net_io.bytes_sent) / time_delta / 1024  # KB/s
        
        self.last_net_io = net_io
        self.last_net_time = current_time
        
        # 更新宠物外观
        if hasattr(self.pet, 'update_pet_appearance'):
            self.pet.update_pet_appearance()
        
        # 更新气泡内容
        if hasattr(self.pet, 'update_bubble_content'):
            self.pet.update_bubble_content()
        
        # 更新托盘图标菜单中的信息
        if hasattr(self.pet, 'tray_cpu_action'):
            self.pet.tray_cpu_action.setText(f"CPU: {self.cpu_percent:.1f}%")
        if hasattr(self.pet, 'tray_memory_action'):
            self.pet.tray_memory_action.setText(f"内存: {self.memory_percent:.1f}%")
        
        # 更新托盘图标提示
        if hasattr(self.pet, 'tray_icon'):
            self.pet.tray_icon.setToolTip(f"CPU: {self.cpu_percent:.1f}% | 内存: {self.memory_percent:.1f}%")