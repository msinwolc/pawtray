from PyQt5.QtCore import QTimer

class WeatherManager:
    def __init__(self, pet):
        self.pet = pet
        self.weather_info = "获取中..."
        self.weather_data = {}
        
        # 每1小时获取一次天气
        self.weather_timer = QTimer(self.pet)
        self.weather_timer.timeout.connect(self.get_weather)
        self.weather_timer.start(3600000)  # 每1小时
        self.get_weather()  # 立即获取一次天气
    
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
    
    def get_weather(self):
        """获取天气信息"""
        try:
            # 尝试多种方法获取天气
            self._try_multiple_weather_apis()
            
            # 格式化天气信息
            self.format_weather_info()
            
        except Exception as e:
            self.weather_info = "天气服务不可用"
            print(f"天气获取错误: {e}")
    
    def _try_multiple_weather_apis(self):
        """尝试多种天气API"""
        # 尝试方法1: wttr.in
        try:
            self._get_weather_wttrin()
            return
        except Exception as e:
            print(f"wttr.in API失败: {e}")
        
        # 尝试方法2: 使用IP定位 + 简单天气
        try:
            self._get_weather_ip_based()
            return
        except Exception as e:
            print(f"IP定位天气失败: {e}")
    
    def _get_weather_wttrin(self):
        """使用wttr.in获取天气"""
        import urllib.request
        
        # 使用HTTP而不是HTTPS避免SSL问题
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
    
    def _get_weather_ip_based(self):
        """基于IP的简单天气"""
        import urllib.request
        import json
        
        # 获取位置
        with urllib.request.urlopen("http://ip-api.com/json") as response:
            data = json.loads(response.read().decode('utf-8'))
            city = data.get('city', 'Unknown')
            country = data.get('country', '')
            
            self.weather_data = {
                'city': city,
                'temp': '未知',
                'condition': '未知'
            }

    def update_weather(self):
        """更新天气信息"""
        try:
            # 调用现有的天气获取方法
            self.get_weather()  # 这个方法会更新self.weather_data
            
            # 格式化天气信息
            self.format_weather_info()  # 这个方法会更新self.weather_info
            
            print(f"天气信息已更新: {self.weather_info}")
            return self.weather_info
        except Exception as e:
            self.weather_info = "天气网络错误"
            print(f"获取天气信息出错: {e}")
            return self.weather_info