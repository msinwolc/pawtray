from PyQt5.QtWidgets import QAction
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QGuiApplication

class ScreenshotManager:
    def __init__(self, parent=None):
        self.parent = parent
        
        # Create screenshot action
        self.screenshot_action = QAction("截图", parent)
        self.screenshot_action.triggered.connect(self.take_screenshot)
        
        # Initialize variables
        self.screenshot_timer = QTimer(parent)
        self.screenshot_timer.setSingleShot(True)
        self.screenshot_timer.timeout.connect(self.capture_screen)
    
    def take_screenshot(self):
        """Prepare to take a screenshot after a short delay"""
        # Hide the parent window if it exists
        if self.parent and hasattr(self.parent, 'hide'):
            self.parent.hide()
        
        # Hide the tray icon menu if it exists
        if hasattr(self.parent, 'tray_menu') and self.parent.tray_menu.isVisible():
            self.parent.tray_menu.hide()
        
        # Wait a moment for UI to hide
        self.screenshot_timer.start(200)
    
    def capture_screen(self):
        """Capture the screen and save to clipboard only"""
        try:
            # Capture the entire screen
            screen = QGuiApplication.primaryScreen()
            pixmap = screen.grabWindow(0)
            
            # Copy to clipboard
            clipboard = QGuiApplication.clipboard()
            clipboard.setPixmap(pixmap)
            
            print("Screenshot copied to clipboard")
        except Exception as e:
            print(f"Error taking screenshot: {e}")
        finally:
            # Show the parent window again if it exists
            if self.parent and hasattr(self.parent, 'show'):
                self.parent.show()