from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
import time
import urllib.request
import json

class WeatherWorker(QObject):
    """天气更新工作线程"""
    weatherUpdated = pyqtSignal(str)  # 天气更新信号
    finished = pyqtSignal()  # 完成信号
    weatherDataUpdated = pyqtSignal(dict)  # 天气数据更新信号
    
    def __init__(self):
        super().__init__()
        self.weather_data = None
        self.weather_info = None
        self.api_key = "11000f2da7a4454fbf523903251703"  # WeatherAPI.com API密钥
    
    @pyqtSlot()
    def update_weather(self):
        """更新天气信息"""
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
            # 使用WeatherAPI.com API
            url = f"https://api.weatherapi.com/v1/current.json?key={self.api_key}&q=auto:ip"
            
            with urllib.request.urlopen(url, timeout=5) as response:
                data = response.read().decode('utf-8')
                weather_json = json.loads(data)
                
                # 提取需要的数据
                self.weather_data = {
                    'city': weather_json['location']['name'],
                    'temp': f"{weather_json['current']['temp_c']}°C",
                    'condition': weather_json['current']['condition']['text'],
                    'wind_dir': weather_json['current']['wind_dir'],
                    'wind_kph': weather_json['current']['wind_kph'],
                }
                
        except Exception as e:
            self.weatherUpdated.emit("天气更新失败")
            print(f"获取天气信息失败: {e}")

    def format_weather_info(self):
        """格式化天气信息"""
        try:
            if self.weather_data:
                temp = self.weather_data.get('temp', '')
                condition = self.weather_data.get('condition', '')
                city = self.weather_data.get('city', '')
                wind_dir = self.weather_data.get('wind_dir', '')
                wind_kph = self.weather_data.get('wind_kph', '')
                
                # 添加天气图标
                weather_icons = {
                    'sunny': '☀️',
                    'clear': '☀️',
                    'partly cloudy': '⛅',
                    'cloudy': '☁️',
                    'overcast': '☁️',
                    'mist': '🌫️',
                    'fog': '🌫️',
                    'rain': '🌧️',
                    'light rain': '🌦️',
                    'moderate rain': '🌧️',
                    'heavy rain': '🌧️',
                    'patchy rain': '🌦️',
                    'shower': '🌦️',
                    'thunder': '⛈️',
                    'thunderstorm': '⛈️',
                    'snow': '❄️',
                    'sleet': '🌨️',
                    'blizzard': '❄️'
                }

                wind_level = 0
                if wind_kph < 1:
                    wind_level = 0
                elif wind_kph < 6:
                    wind_level = 1
                elif wind_kph < 12:
                    wind_level = 2
                elif wind_kph < 20:
                    wind_level = 3
                elif wind_kph < 29:
                    wind_level = 4
                elif wind_kph < 39:
                    wind_level = 5
                elif wind_kph < 50:
                    wind_level = 6
                elif wind_kph < 62:
                    wind_level = 7
                elif wind_kph < 75:
                    wind_level = 8
                elif wind_kph < 89:
                    wind_level = 9
                elif wind_kph < 103:
                    wind_level = 10
                elif wind_kph < 118:
                    wind_level = 11
                else:
                    wind_level = 12

                # 风向中文映射
                wind_dir_cn = {
                    'N': '北',
                    'NNE': '东北偏北',
                    'NE': '东北',
                    'ENE': '东北偏东',
                    'E': '东',
                    'ESE': '东南偏东',
                    'SE': '东南',
                    'SSE': '东南偏南',
                    'S': '南',
                    'SSW': '西南偏南',
                    'SW': '西南',
                    'WSW': '西南偏西',
                    'W': '西',
                    'WNW': '西北偏西',
                    'NW': '西北',
                    'NNW': '西北偏北'
                }

                # 获取中文风向
                wind_dir_text = wind_dir_cn.get(wind_dir, wind_dir)
                
                # 构建风向风力字符串
                wind_info = f"{wind_dir_text}风{wind_level}级"
                    
                
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
                self.weather_info = f"{icon} {city} {temp} {wind_info}"
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
        self.weather_data = {}  # 初始化为空字典
        self.thread = None  # 初始化为None
        self.worker = None  # 初始化为None
    
    def update_weather(self):
        """启动天气更新线程"""
        # 检查线程是否存在且正在运行
        if self.thread is not None and self.thread.isRunning():
            print("天气更新已在进行中，跳过")
            return
        
        # 创建新的线程和工作对象
        self.thread = QThread()
        self.worker = WeatherWorker()
        self.worker.moveToThread(self.thread)
        
        # 连接信号和槽
        self.thread.started.connect(self.worker.update_weather)
        self.worker.weatherUpdated.connect(self.update_weather_info)
        self.worker.weatherDataUpdated.connect(self.update_weather_data)
        self.worker.finished.connect(self.thread.quit)
        
        # 确保线程结束时清理
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.finished.connect(self.clear_thread)  # 添加清理回调
        
        # 启动线程
        self.thread.start()
    
    def clear_thread(self):
        """清理线程引用"""
        self.thread = None
        self.worker = None
        print("天气线程已清理")
    
    def stop(self):
        """停止天气更新线程"""
        if self.thread is not None and self.thread.isRunning():
            self.thread.quit()
            if not self.thread.wait(1000):
                self.thread.terminate()
                self.thread.wait()
            self.clear_thread()
    
    @pyqtSlot(str)
    def update_weather_info(self, weather_info):
        """更新天气信息（用于托盘文本）"""
        self.weather_info = weather_info
    
    @pyqtSlot(dict)
    def update_weather_data(self, weather_data):
        """更新天气数据（包含完整信息）"""
        self.weather_data = weather_data