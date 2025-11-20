"""
UI styling constants and color schemes
"""

from PyQt6.QtGui import QColor

# ============================================================================
# Color Palette
# ============================================================================

class Colors:
    """Color constants for UI"""
    # Detection buttons
    BUTTON_DEFAULT_BG = "#555555"
    BUTTON_DEFAULT_BORDER = "#333"
    
    # Human detection
    HUMAN_PRIMARY = "#4CAF50"
    HUMAN_DARK = "#2E7D32"
    HUMAN_DARKER = "#1B5E20"
    
    # Non-human detection
    NON_HUMAN_PRIMARY = "#F44336"
    NON_HUMAN_DARK = "#C62828"
    NON_HUMAN_DARKER = "#B71C1C"
    
    # Activity detection
    ACTIVITY_PRIMARY = "#FF5722"
    ACTIVITY_BORDER = "#FF5722"
    
    # Status colors
    STATUS_IDLE = "#666666"
    STATUS_ACTIVE = "#4CAF50"
    STATUS_WARNING = "#FF9800"
    STATUS_ERROR = "#F44336"
    STATUS_INFO = "#2196F3"
    
    # Background colors
    BG_LIGHT = "#f0f0f0"
    BG_DARK = "#333"
    
    # Text colors
    TEXT_WHITE = "white"
    TEXT_DARK = "#333"


# ============================================================================
# Style Sheets
# ============================================================================

class StyleSheets:
    """Pre-defined style sheets for widgets"""
    
    @staticmethod
    def detection_button_default():
        return f"""
            QPushButton {{
                font-size: 24px;
                font-weight: bold;
                background-color: {Colors.BUTTON_DEFAULT_BG};
                color: {Colors.TEXT_WHITE};
                border: 2px solid {Colors.BUTTON_DEFAULT_BORDER};
                border-radius: 5px;
            }}
        """
    
    @staticmethod
    def detection_button_human_active():
        return f"""
            QPushButton {{
                font-size: 24px;
                font-weight: bold;
                background-color: {Colors.HUMAN_PRIMARY};
                color: {Colors.TEXT_WHITE};
                border: 2px solid {Colors.HUMAN_DARK};
                border-radius: 5px;
            }}
        """
    
    @staticmethod
    def detection_button_human_dark():
        return f"""
            QPushButton {{
                font-size: 24px;
                font-weight: bold;
                background-color: {Colors.HUMAN_DARK};
                color: {Colors.TEXT_WHITE};
                border: 2px solid {Colors.HUMAN_DARKER};
                border-radius: 5px;
            }}
        """
    
    @staticmethod
    def detection_button_non_human_active():
        return f"""
            QPushButton {{
                font-size: 24px;
                font-weight: bold;
                background-color: {Colors.NON_HUMAN_PRIMARY};
                color: {Colors.TEXT_WHITE};
                border: 2px solid {Colors.NON_HUMAN_DARK};
                border-radius: 5px;
            }}
        """
    
    @staticmethod
    def detection_button_non_human_dark():
        return f"""
            QPushButton {{
                font-size: 24px;
                font-weight: bold;
                background-color: {Colors.NON_HUMAN_DARK};
                color: {Colors.TEXT_WHITE};
                border: 2px solid {Colors.NON_HUMAN_DARKER};
                border-radius: 5px;
            }}
        """
    
    @staticmethod
    def status_label(color=None):
        if color is None:
            color = Colors.STATUS_IDLE
        return f"""
            font-size: 28px; 
            font-weight: bold; 
            color: {color};
            border: 2px solid {Colors.BG_DARK};
            border-radius: 5px;
            padding: 10px;
            background-color: {Colors.BG_LIGHT};
        """
    
    @staticmethod
    def status_label_active(bg_color, border_color=None):
        if border_color is None:
            border_color = bg_color
        return f"""
            font-size: 28px; 
            font-weight: bold; 
            color: {Colors.TEXT_WHITE};
            border: 2px solid {border_color};
            border-radius: 5px;
            padding: 10px;
            background-color: {bg_color};
        """
    
    @staticmethod
    def activity_indicator_idle():
        return f"""
            font-size: 20px; 
            font-weight: bold; 
            color: {Colors.STATUS_IDLE};
            border: 2px solid {Colors.BG_DARK};
            border-radius: 5px;
            padding: 10px;
            background-color: {Colors.BG_LIGHT};
        """
    
    @staticmethod
    def activity_indicator_active():
        return f"""
            font-size: 20px; 
            font-weight: bold; 
            color: {Colors.TEXT_WHITE};
            border: 2px solid {Colors.ACTIVITY_BORDER};
            border-radius: 5px;
            padding: 10px;
            background-color: {Colors.ACTIVITY_PRIMARY};
        """
    
    @staticmethod
    def activity_indicator_flash():
        return f"""
            font-size: 20px; 
            font-weight: bold; 
            color: {Colors.ACTIVITY_PRIMARY};
            border: 2px solid {Colors.ACTIVITY_BORDER};
            border-radius: 5px;
            padding: 10px;
            background-color: {Colors.BG_LIGHT};
        """
    
    @staticmethod
    def small_label(bold=False, color=None):
        weight = "bold" if bold else "normal"
        color_str = f"color: {color};" if color else ""
        return f"font-size: 12px; font-weight: {weight}; {color_str}"
    
    @staticmethod
    def medium_label(bold=False, color=None):
        weight = "bold" if bold else "normal"
        color_str = f"color: {color};" if color else ""
        return f"font-size: 13px; font-weight: {weight}; {color_str}"
    
    @staticmethod
    def input_field():
        return "font-size: 14px; padding: 5px;"
    
    @staticmethod
    def button_default():
        return "font-size: 12px; padding: 5px;"
    
    @staticmethod
    def control_button():
        return "font-size: 13px; font-weight: bold; padding: 8px;"