from PyQt5.QtWidgets import QLabel, QSizePolicy
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QPainter, QPainterPath, QColor

class InfoBubble(QLabel):
    """独立的信息气泡窗口"""
    def __init__(self):
        super().__init__()
        # 设置窗口无边框和置顶
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 设置样式 - 更小的字体
        self.setFont(QFont("Arial", 7, QFont.Bold))  # 调整字体大小
        
        # 确保文本完全居中
        self.setAlignment(Qt.AlignCenter)
        
        # 设置自动换行
        self.setWordWrap(True)
        
        # 设置大小策略
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # 设置最小尺寸
        self.setMinimumSize(180, 100)
        
        # 设置边距
        self.setMargin(10)
        
        # 设置背景颜色和边框
        self.bg_color = QColor(40, 40, 40, 220)
        self.border_color = QColor(60, 60, 60, 220)
        
        # 初始隐藏
        self.hide()
    
    def update_style(self, cpu_percent):
        """根据CPU使用率更新样式"""
        if cpu_percent < 50:
            self.border_color = QColor(76, 175, 80, 220)  # 绿色
            self.bg_color = QColor(30, 50, 30, 220)
        elif cpu_percent < 80:
            self.border_color = QColor(255, 152, 0, 220)  # 橙色
            self.bg_color = QColor(50, 40, 20, 220)
        else:
            self.border_color = QColor(244, 67, 54, 220)  # 红色
            self.bg_color = QColor(50, 30, 30, 220)
        
        # 触发重绘
        self.update()
    
    def paintEvent(self, event):
        """自定义绘制事件，绘制圆角矩形背景"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 创建圆角矩形路径
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 10, 10)
        
        # 填充背景
        painter.fillPath(path, self.bg_color)
        
        # 绘制边框
        painter.setPen(self.border_color)
        painter.drawPath(path)
        
        # 调用父类的绘制方法绘制文本
        super().paintEvent(event)
    
    def sizeHint(self):
        """提供尺寸提示，确保有足够的空间显示内容"""
        # 获取文本的理想大小
        text_size = super().sizeHint()
        
        # 确保至少有最小尺寸
        width = max(180, text_size.width() + 20)  # 添加一些边距
        height = max(100, text_size.height() + 20)
        
        return QSize(width, height)
    
    def setText(self, text):
        """重写setText方法，设置文本后自动调整大小"""
        super().setText(text)
        self.adjustSize()  # 自动调整大小