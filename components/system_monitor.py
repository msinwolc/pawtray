from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot, QTimer
import psutil
import time

class SystemMonitorWorker(QObject):
    """系统监控工作线程"""
    systemInfoUpdated = pyqtSignal(dict)  # 系统信息更新信号
    finished = pyqtSignal()  # 完成信号
    
    def __init__(self):
        super().__init__()
        self.last_net_io = psutil.net_io_counters()
        self.last_net_time = time.time()
        self.running = True  # 控制线程运行的标志
    
    @pyqtSlot()
    def update_system_info(self):
        """更新系统信息"""
        if not self.running:
            self.finished.emit()
            return
            
        try:
            # 获取CPU使用率
            cpu_percent = psutil.cpu_percent(interval=None)
            
            # 获取内存使用率
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # 获取磁盘使用率
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            
            # 获取网络速度
            current_time = time.time()
            current_net_io = psutil.net_io_counters()
            
            net_speed_up = 0.0
            net_speed_down = 0.0
            
            time_delta = current_time - self.last_net_time
            if time_delta > 0:
                # 计算上传和下载速度 (KB/s)
                net_speed_up = (current_net_io.bytes_sent - self.last_net_io.bytes_sent) / 1024 / time_delta
                net_speed_down = (current_net_io.bytes_recv - self.last_net_io.bytes_recv) / 1024 / time_delta
            
            # 更新上次网络数据
            self.last_net_io = current_net_io
            self.last_net_time = current_time
            
            # 发送系统信息更新信号
            system_info = {
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent,
                'net_speed_up': net_speed_up,
                'net_speed_down': net_speed_down
            }
            self.systemInfoUpdated.emit(system_info)
        except Exception as e:
            # print(f"更新系统信息失败: {e}")
            pass
    
    @pyqtSlot()
    def stop(self):
        """停止工作线程"""
        self.running = False
        self.finished.emit()

class SystemMonitor(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        
        # 初始化系统信息
        self.cpu_percent = 0.0
        self.memory_percent = 0.0
        self.disk_percent = 0.0
        self.net_speed_up = 0.0
        self.net_speed_down = 0.0
        
        # 保存线程和工作对象的引用
        self._thread = None
        self._worker = None
        
        # 创建定时器（在主线程中）
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._trigger_update)
        self._update_interval = 1000  # 默认1秒更新一次
        
        # 初始化系统信息
        self.start_monitoring()
    
    def _trigger_update(self):
        """触发工作线程更新系统信息"""
        if self._worker and self._thread and self._thread.isRunning():
            # 通过信号槽机制触发工作线程更新
            QTimer.singleShot(0, self._worker.update_system_info)
    
    def start_monitoring(self, update_interval=1000):
        """开始监控系统信息"""
        # 如果已经在监控，先停止
        self.stop()
        
        # 设置更新间隔
        self._update_interval = update_interval
        
        # 创建新线程和工作对象
        self._thread = QThread()
        self._worker = SystemMonitorWorker()
        self._worker.moveToThread(self._thread)
        
        # 连接信号和槽
        self._worker.systemInfoUpdated.connect(self.update_system_info)
        self._worker.finished.connect(self._thread.quit)
        
        # 确保线程结束时清理
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(lambda: self._cleanup())
        
        # 启动线程
        self._thread.start()
        
        # 立即更新一次
        self._trigger_update()
        
        # 启动定时器（在主线程中）
        self._timer.start(self._update_interval)
    
    def update_system_info_async(self):
        """兼容旧接口，现在不需要单独调用"""
        # 如果监控已经在运行，不需要做任何事
        if self._thread is not None and self._thread.isRunning():
            return
        
        # 如果监控没有运行，启动监控
        self.start_monitoring()
    
    def _cleanup(self):
        """清理线程和工作对象的引用"""
        self._worker = None
        self._thread = None
    
    def stop(self):
        """停止所有线程和定时器"""
        # 停止定时器
        if hasattr(self, '_timer') and self._timer.isActive():
            self._timer.stop()
        
        # 停止工作线程
        if self._worker and self._thread and self._thread.isRunning():
            self._worker.stop()
            
            # 等待线程结束，最多等待1秒
            self._thread.quit()
            if not self._thread.wait(1000):
                self._thread.terminate()
                self._thread.wait()
    
    def set_update_interval(self, interval_ms):
        """设置更新间隔（毫秒）"""
        self._update_interval = interval_ms
        if hasattr(self, '_timer') and self._timer.isActive():
            self._timer.setInterval(interval_ms)
    
    def __del__(self):
        """析构函数，确保线程在对象销毁前停止"""
        self.stop()
    
    @pyqtSlot(dict)
    def update_system_info(self, system_info):
        """更新系统信息"""
        self.cpu_percent = system_info['cpu_percent']
        self.memory_percent = system_info['memory_percent']
        self.disk_percent = system_info['disk_percent']
        self.net_speed_up = system_info['net_speed_up']
        self.net_speed_down = system_info['net_speed_down']