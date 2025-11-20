"""
Custom Qt widgets for the Human Detection System
"""

from PyQt6.QtWidgets import QLabel, QPushButton
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from ui.styles import StyleSheets, Colors
from config import (
    DETECTION_BUTTON_WIDTH,
    DETECTION_BUTTON_HEIGHT,
    BLINK_TIMER_INTERVAL,
    ACTIVITY_BLINK_INTERVAL,
    ACTIVITY_BLINK_COUNT
)


class DetectionButton(QPushButton):
    """Custom button for detection display (HUMAN/NON-HUMAN)"""
    
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFixedSize(DETECTION_BUTTON_WIDTH, DETECTION_BUTTON_HEIGHT)
        self.reset_style()
        
        # Blink state
        self.blink_state = False
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self._blink)
        self.blink_timer.setInterval(BLINK_TIMER_INTERVAL)
        
        # Store button type
        self.button_type = text.lower()
    
    def reset_style(self):
        """Reset to default gray style"""
        self.setStyleSheet(StyleSheets.detection_button_default())
        self.blink_state = False
    
    def start_blinking(self):
        """Start blinking animation"""
        self.blink_state = False
        self.blink_timer.start()
    
    def stop_blinking(self):
        """Stop blinking animation"""
        self.blink_timer.stop()
    
    def _blink(self):
        """Toggle blink state"""
        if self.button_type == "human":
            if self.blink_state:
                self.setStyleSheet(StyleSheets.detection_button_human_active())
            else:
                self.setStyleSheet(StyleSheets.detection_button_human_dark())
        elif self.button_type == "non-human":
            if self.blink_state:
                self.setStyleSheet(StyleSheets.detection_button_non_human_active())
            else:
                self.setStyleSheet(StyleSheets.detection_button_non_human_dark())
        
        self.blink_state = not self.blink_state


class StatusLabel(QLabel):
    """Custom label for status display with styling"""
    
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.set_idle()
    
    def set_idle(self):
        """Set to idle state (gray)"""
        self.setStyleSheet(StyleSheets.status_label(Colors.STATUS_IDLE))
    
    def set_active(self, bg_color):
        """Set to active state with custom background color"""
        self.setStyleSheet(StyleSheets.status_label_active(bg_color))
    
    def set_color(self, color):
        """Set text color only"""
        self.setStyleSheet(StyleSheets.status_label(color))


class ActivityIndicator(QLabel):
    """Activity indicator with blinking animation"""
    
    def __init__(self, parent=None):
        super().__init__("IDLE", parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(StyleSheets.activity_indicator_idle())
        
        # Blink state
        self.blink_state = False
        self.blink_count = 0
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self._blink)
        self.blink_timer.setInterval(ACTIVITY_BLINK_INTERVAL)
    
    def trigger_activity(self):
        """Trigger activity animation"""
        self.blink_count = 0
        self.blink_state = False
        self.blink_timer.start()
    
    def _blink(self):
        """Toggle blink state"""
        if self.blink_count < ACTIVITY_BLINK_COUNT:
            if self.blink_state:
                self.setText("ACTIVE!")
                self.setStyleSheet(StyleSheets.activity_indicator_active())
            else:
                self.setText("ACTIVE!")
                self.setStyleSheet(StyleSheets.activity_indicator_flash())
            
            self.blink_state = not self.blink_state
            self.blink_count += 1
        else:
            self.blink_timer.stop()
            self.setText("IDLE")
            self.setStyleSheet(StyleSheets.activity_indicator_idle())
    
    def reset(self):
        """Reset to idle state"""
        self.blink_timer.stop()
        self.setText("IDLE")
        self.setStyleSheet(StyleSheets.activity_indicator_idle())


class LEDStatusLabel(StatusLabel):
    """LED status label with ON/OFF states"""
    
    def __init__(self, parent=None):
        super().__init__("OFF", parent)
        self.set_off()
    
    def set_on(self):
        """Set LED to ON state (green)"""
        self.setText("ON")
        self.set_active(Colors.STATUS_ACTIVE)
    
    def set_off(self):
        """Set LED to OFF state (gray)"""
        self.setText("OFF")
        self.set_idle()