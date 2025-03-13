from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
import time
import urllib.request

class WeatherWorker(QObject):
    """天气更新工作线程"""
    weatherUpdated = pyqtSignal(str)  # 天气更新信号
    finished = pyqtSignal()  # 完成信号
    
    def __init__(self):
        super().__init__()
        self.weather_data = None
    
    @pyqtSlot()
    def update_weather(self):
        self.get_weather()
        self.format_weather_info()

        # 如果有天气信息，发送更新信号
        if self.weather_info:
            self.weatherUpdated.emit(self.weather_info)
        
        # 发送完成信号
        self.finished.emit()

    def get_weather(self):
        """获取天气信息"""
        try:
            # 使用原始的wttr.in API
            url = "http://wttr.in/?format=%l|%t|%C"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = response.read().decode('utf-8').strip()
                parts = data.split('|')
                if len(parts) >= 3:
                    self.weather_data = {
                        'city': parts[0].strip(),
                        'temp': parts[1].strip(),
                        'condition': parts[2].strip()
                    }
                else:
                    raise Exception("wttr.in返回的数据格式不正确")
        except Exception as e:
            self.weatherUpdated.emit("天气更新失败")
            # print(f"获取天气信息失败: {e}")
            pass

    def format_weather_info(self):
        """格式化天气信息"""
        try:
            if self.weather_data:
                temp = self.weather_data.get('temp', '')
                condition = self.weather_data.get('condition', '')
                city = self.weather_data.get('city', '')
                
                # 添加天气图标
                weather_icons = {
                    'clear': '☀️',
                    'sunny': '☀️',
                    'partly cloudy': '⛅',
                    'cloudy': '☁️',
                    'overcast': '☁️',
                    'rain': '🌧️',
                    'shower': '🌦️',
                    'thunder': '⛈️',
                    'snow': '❄️',
                    'mist': '🌫️',
                    'fog': '🌫️'
                }
                
                icon = '🌡️'  # 默认图标
                condition_lower = condition.lower()
                for key, value in weather_icons.items():
                    if key in condition_lower:
                        icon = value
                        break
                
                # 简化城市名称，只保留主要部分
                if ',' in city:
                    city = city.split(',')[0].strip()
                
                # 限制城市名称长度
                if len(city) > 10:
                    city = city[:10] + "..."
                
                # 简化天气信息，使其更短
                self.weather_info = f"{icon} {city} {temp}"
            else:
                self.weather_info = "天气数据不可用"
        except Exception as e:
            self.weather_info = "天气格式化错误"
            print(f"格式化天气信息失败: {e}")

class WeatherManager(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.weather_info = "加载中..."
        
        # 创建线程和工作对象
        self.thread = QThread()
        self.worker = WeatherWorker()
        self.worker.moveToThread(self.thread)
        
        # 连接信号和槽
        self.thread.started.connect(self.worker.update_weather)
        self.worker.weatherUpdated.connect(self.update_weather_info)
        self.worker.finished.connect(self.thread.quit)
        
        # 确保线程结束时清理
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
    
    def update_weather(self):
        """启动天气更新线程"""
        # 如果线程已经在运行，不要再次启动
        if self.thread.isRunning():
            # print("天气更新已在进行中，跳过")
            return
        
        # 启动线程
        self.thread = QThread()
        self.worker = WeatherWorker()
        self.worker.moveToThread(self.thread)
        
        # 连接信号和槽
        self.thread.started.connect(self.worker.update_weather)
        self.worker.weatherUpdated.connect(self.update_weather_info)
        self.worker.finished.connect(self.thread.quit)
        
        # 确保线程结束时清理
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        # 启动线程
        self.thread.start()
    
    def stop(self):
        """停止天气更新线程"""
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.quit()
            if not self.thread.wait(1000):
                self.thread.terminate()
                self.thread.wait()
    
    @pyqtSlot(str)
    def update_weather_info(self, weather_info):
        """更新天气信息"""
        self.weather_info = weather_info