# src/gui/main_window.py
# Main Window GUI for Human Detection System

import sys
import time
import traceback
from pathlib import Path

from PyQt6.QtCore import Qt, QThreadPool, QTimer, QSize
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QGridLayout, QHBoxLayout, QVBoxLayout,
    QLabel, QLineEdit, QGroupBox, QMessageBox
)
import pyqtgraph as pg

try:
    import torch
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False

from src.detection.detector import HumanDetector
from src.hardware.sensor import RedPitayaSensor
from src.workers.detection_worker import DetectionWorker
from config.settings import (
    DEFAULT_MODEL_DIR,
    DEFAULT_MODEL_PATH,
    BEST_MODEL_PATH,
    DEFAULT_DISTANCE_THRESHOLD_CM,
    LED_TIMER_DURATION,
    SIGNALS_PER_SECOND
)


class MainWindow(QMainWindow):
    """Main window with rate-controlled detection and counter-based LED timer"""
    
    def __init__(self):
        super().__init__()
        
        # Initialize components
        self.rp_sensor = RedPitayaSensor()
        self.detector = None
        self.start_time = None
        self.header_info = None
        self.threadpool = QThreadPool()
        
        # Status messages
        self.sensor_status_message = self.rp_sensor.get_sensor_status_message()
        self.app_status_message = "App Started"
        
        # State variables
        self.worker = None
        self.detection_active = False
        self.distance_threshold_cm = DEFAULT_DISTANCE_THRESHOLD_CM
        self.led_timer_duration = LED_TIMER_DURATION  # LED timer duration in seconds
        
        # Blink timers
        self.human_blink_timer = QTimer()
        self.human_blink_timer.timeout.connect(self.blink_human_button)
        self.human_blink_state = False
        
        self.non_human_blink_timer = QTimer()
        self.non_human_blink_timer.timeout.connect(self.blink_non_human_button)
        self.non_human_blink_state = False
        
        # Activity blink timer
        self.activity_blink_timer = QTimer()
        self.activity_blink_timer.timeout.connect(self.blink_activity_indicator)
        self.activity_blink_state = False
        self.activity_blink_count = 0
        
        # Current detection state
        self.current_detection = None
        
        # Setup UI
        self.setWindowTitle(f"Human Detection APP - {SIGNALS_PER_SECOND} valid signals/sec")
        
        # Main layout
        main_layout = QGridLayout()
        
        # Plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('black')
        self.plot_widget.setLabel('left', 'Amplitude (ADC)', color='white')
        self.plot_widget.setLabel('bottom', 'Sample', color='white')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # Set fixed axis ranges
        # Y-axis: -6000 to +6000 (amplitude)
        # X-axis: 0 to 25000 (samples)
        self.plot_widget.setYRange(-6000, 6000, padding=0)
        self.plot_widget.setXRange(0, 25000, padding=0)
        self.plot_widget.enableAutoRange(axis='y', enable=False)  # Disable auto-range for Y-axis
        self.plot_widget.enableAutoRange(axis='x', enable=False)  # Disable auto-range for X-axis
        
        main_layout.addWidget(self.plot_widget, 0, 0, 1, 3)
        
        # ====================================================================
        # Detection Buttons Section
        # ====================================================================
        buttons_layout = QHBoxLayout()
        
        # HUMAN Button
        self.human_button = QPushButton("HUMAN")
        self.human_button.setFixedSize(QSize(180, 100))
        self.human_button.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                font-weight: bold;
                background-color: #555555;
                color: white;
                border: 2px solid #333;
                border-radius: 5px;
            }
        """)
        buttons_layout.addWidget(self.human_button)
        
        # NON-HUMAN Button
        self.non_human_button = QPushButton("NON-HUMAN")
        self.non_human_button.setFixedSize(QSize(180, 100))
        self.non_human_button.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                font-weight: bold;
                background-color: #555555;
                color: white;
                border: 2px solid #333;
                border-radius: 5px;
            }
        """)
        buttons_layout.addWidget(self.non_human_button)
        
        # LED Status Display
        led_vbox = QVBoxLayout()
        led_vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.led_label = QLabel("LED7 Status:")
        self.led_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.led_label.setFixedHeight(20)
        self.led_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        led_vbox.addWidget(self.led_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.led_status_label = QLabel("OFF")
        self.led_status_label.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #666666;
            border: 2px solid #333;
            border-radius: 5px;
            padding: 5px;
            background-color: #f0f0f0;
        """)
        self.led_status_label.setFixedSize(QSize(120, 50))
        self.led_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        led_vbox.addWidget(self.led_status_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Timer counter display
        self.timer_counter_label = QLabel("Timer: 0.0s")
        self.timer_counter_label.setStyleSheet("font-size: 10px; font-weight: bold;")
        self.timer_counter_label.setFixedHeight(20)
        self.timer_counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        led_vbox.addWidget(self.timer_counter_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        buttons_layout.addLayout(led_vbox)
        
        # Distance Display
        distance_vbox = QVBoxLayout()
        distance_vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.distance_label = QLabel("Distance:")
        self.distance_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.distance_label.setFixedHeight(20)
        self.distance_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        distance_vbox.addWidget(self.distance_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.distance_value_label = QLabel("-- cm")
        self.distance_value_label.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #2196F3;
            border: 2px solid #333;
            border-radius: 5px;
            padding: 5px;
            background-color: #f0f0f0;
        """)
        self.distance_value_label.setFixedSize(QSize(120, 50))
        self.distance_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        distance_vbox.addWidget(self.distance_value_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Empty space to match timer counter
        distance_spacer = QLabel("")
        distance_spacer.setFixedHeight(20)
        distance_vbox.addWidget(distance_spacer, alignment=Qt.AlignmentFlag.AlignCenter)
        
        buttons_layout.addLayout(distance_vbox)
        
        # Confidence Display
        confidence_vbox = QVBoxLayout()
        confidence_vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.confidence_label_text = QLabel("Confidence:")
        self.confidence_label_text.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.confidence_label_text.setFixedHeight(20)
        self.confidence_label_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        confidence_vbox.addWidget(self.confidence_label_text, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.confidence_value_label = QLabel("--")
        self.confidence_value_label.setStyleSheet("""
            font-size: 24px; 
            font-weight: bold; 
            color: #4CAF50;
            border: 2px solid #333;
            border-radius: 5px;
            padding: 5px;
            background-color: #f0f0f0;
        """)
        self.confidence_value_label.setFixedSize(QSize(120, 50))
        self.confidence_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        confidence_vbox.addWidget(self.confidence_value_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Empty space to match timer counter
        confidence_spacer = QLabel("")
        confidence_spacer.setFixedHeight(20)
        confidence_vbox.addWidget(confidence_spacer, alignment=Qt.AlignmentFlag.AlignCenter)
        
        buttons_layout.addLayout(confidence_vbox)
        
        # Activity Indicator
        activity_vbox = QVBoxLayout()
        activity_vbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.activity_label = QLabel("Activity:")
        self.activity_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        self.activity_label.setFixedHeight(20)
        self.activity_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        activity_vbox.addWidget(self.activity_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.activity_indicator = QLabel("IDLE")
        self.activity_indicator.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            color: #666666;
            border: 2px solid #333;
            border-radius: 5px;
            padding: 5px;
            background-color: #f0f0f0;
        """)
        self.activity_indicator.setFixedSize(QSize(120, 50))
        self.activity_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        activity_vbox.addWidget(self.activity_indicator, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.activity_count_label = QLabel("Count: 0")
        self.activity_count_label.setStyleSheet("font-size: 10px; font-weight: bold;")
        self.activity_count_label.setFixedHeight(20)
        self.activity_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        activity_vbox.addWidget(self.activity_count_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        buttons_layout.addLayout(activity_vbox)
        
        main_layout.addLayout(buttons_layout, 1, 0, 1, 3)
        
        # ====================================================================
        # Settings Section
        # ====================================================================
        settings_group = QGroupBox("Detection Settings")
        settings_layout = QHBoxLayout()
        
        # Distance threshold
        self.threshold_label = QLabel("Distance Threshold (cm):")
        self.threshold_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        settings_layout.addWidget(self.threshold_label)
        
        self.threshold_input = QLineEdit()
        self.threshold_input.setText(str(DEFAULT_DISTANCE_THRESHOLD_CM))
        self.threshold_input.setFixedWidth(80)
        self.threshold_input.setStyleSheet("font-size: 14px; padding: 5px;")
        settings_layout.addWidget(self.threshold_input)
        
        self.set_threshold_btn = QPushButton("Set Threshold")
        self.set_threshold_btn.clicked.connect(self.set_threshold_handler)
        self.set_threshold_btn.setStyleSheet("font-size: 12px; padding: 5px;")
        settings_layout.addWidget(self.set_threshold_btn)
        
        self.current_threshold_label = QLabel(f"Current: {DEFAULT_DISTANCE_THRESHOLD_CM} cm")
        self.current_threshold_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #2196F3;")
        settings_layout.addWidget(self.current_threshold_label)
        
        settings_layout.addStretch()
        
        # LED Timer Duration
        self.timer_duration_label = QLabel("LED Timer (seconds):")
        self.timer_duration_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        settings_layout.addWidget(self.timer_duration_label)
        
        self.timer_duration_input = QLineEdit()
        self.timer_duration_input.setText(str(LED_TIMER_DURATION))
        self.timer_duration_input.setFixedWidth(80)
        self.timer_duration_input.setStyleSheet("font-size: 14px; padding: 5px;")
        settings_layout.addWidget(self.timer_duration_input)
        
        self.set_timer_btn = QPushButton("Set Timer")
        self.set_timer_btn.clicked.connect(self.set_timer_handler)
        self.set_timer_btn.setStyleSheet("font-size: 12px; padding: 5px;")
        settings_layout.addWidget(self.set_timer_btn)
        
        self.current_timer_label = QLabel(f"Current: {LED_TIMER_DURATION}s")
        self.current_timer_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #4CAF50;")
        settings_layout.addWidget(self.current_timer_label)
        
        settings_layout.addStretch()
        
        # Rate display
        self.rate_label = QLabel(f"Valid: 0 | Rate: 0.00/s (Target: {SIGNALS_PER_SECOND})")
        self.rate_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #FF9800;")
        settings_layout.addWidget(self.rate_label)
        
        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group, 2, 0, 1, 3)
        
        # ====================================================================
        # Message Section
        # ====================================================================
        message_layout = QHBoxLayout()
        
        self.server_message_widget = QLabel(self.sensor_status_message)
        self.server_message_widget.setStyleSheet("font-size: 10px;")
        message_layout.addWidget(self.server_message_widget)
        
        self.app_message_widget = QLabel(self.app_status_message)
        self.app_message_widget.setStyleSheet("font-size: 10px;")
        message_layout.addWidget(self.app_message_widget)
        
        self.total_signal_count_message_widget = QLabel("Total: 0")
        self.total_signal_count_message_widget.setStyleSheet("font-size: 10px;")
        message_layout.addWidget(self.total_signal_count_message_widget)
        
        self.broken_signal_count_message_widget = QLabel("Broken: 0")
        self.broken_signal_count_message_widget.setStyleSheet("font-size: 10px; color: #F44336;")
        message_layout.addWidget(self.broken_signal_count_message_widget)
        
        main_layout.addLayout(message_layout, 3, 0, 1, 3)
        
        # ====================================================================
        # Statistics Section
        # ====================================================================
        stats_layout = QHBoxLayout()
        
        self.human_count_label = QLabel("Human: 0")
        self.human_count_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #4CAF50;")
        stats_layout.addWidget(self.human_count_label)
        
        self.non_human_count_label = QLabel("Non-Human: 0")
        self.non_human_count_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #F44336;")
        stats_layout.addWidget(self.non_human_count_label)
        
        self.uncertain_count_label = QLabel("Uncertain: 0")
        self.uncertain_count_label.setStyleSheet("font-size: 13px; font-weight: bold; color: #FF9800;")
        stats_layout.addWidget(self.uncertain_count_label)
        
        self.inference_time_label = QLabel("Inference: -- ms")
        self.inference_time_label.setStyleSheet("font-size: 13px;")
        stats_layout.addWidget(self.inference_time_label)
        
        main_layout.addLayout(stats_layout, 4, 0, 1, 3)
        
        # ====================================================================
        # Control Buttons
        # ====================================================================
        control_layout = QHBoxLayout()
        
        self.start_sensor_btn = QPushButton("Start Sensor & Detection")
        self.start_sensor_btn.clicked.connect(self.start_sensor_btn_handler)
        self.start_sensor_btn.setStyleSheet("font-size: 13px; font-weight: bold; padding: 8px;")
        control_layout.addWidget(self.start_sensor_btn)
        
        self.stop_sensor_btn = QPushButton("Stop Sensor & Detection")
        self.stop_sensor_btn.clicked.connect(self.stop_sensor_btn_handler)
        self.stop_sensor_btn.setStyleSheet("font-size: 13px; font-weight: bold; padding: 8px;")
        control_layout.addWidget(self.stop_sensor_btn)
        
        main_layout.addLayout(control_layout, 5, 0, 1, 3)
        
        # Set central widget
        self.widget = QWidget()
        self.widget.setLayout(main_layout)
        self.setCentralWidget(self.widget)
        
        # Pre-load model
        self.preload_model()
    
    # ========================================================================
    # Handler Methods
    # ========================================================================
    
    def set_threshold_handler(self):
        """Set distance threshold for activity detection"""
        try:
            threshold_value = float(self.threshold_input.text())
            
            if threshold_value <= 0:
                QMessageBox.warning(self, "Invalid Value", "Distance threshold must be greater than 0!")
                return
            
            if threshold_value > 100:
                QMessageBox.warning(self, "Invalid Value", "Distance threshold seems too large! Recommended: 5-50 cm")
                return
            
            self.distance_threshold_cm = threshold_value
            self.current_threshold_label.setText(f"Current: {threshold_value} cm")
            
            if self.worker:
                self.worker.distance_threshold_cm = threshold_value
            
            self.app_status_message_set(f"Distance threshold set to {threshold_value} cm")
            print(f"Distance threshold updated: {threshold_value} cm")
            
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number for distance threshold!")
    
    def set_timer_handler(self):
        """Set LED timer duration"""
        try:
            timer_value = float(self.timer_duration_input.text())
            
            if timer_value <= 0:
                QMessageBox.warning(self, "Invalid Value", "LED timer duration must be greater than 0!")
                return
            
            if timer_value > 300:
                QMessageBox.warning(self, "Invalid Value", "LED timer duration seems too large! Recommended: 5-60 seconds")
                return
            
            self.led_timer_duration = timer_value
            self.current_timer_label.setText(f"Current: {timer_value}s")
            
            # Update global LED_TIMER_DURATION (used by worker)
            import config.settings as settings
            settings.LED_TIMER_DURATION = timer_value
            
            self.app_status_message_set(f"LED timer duration set to {timer_value} seconds")
            print(f"LED timer duration updated: {timer_value} seconds")
            
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter a valid number for LED timer duration!")
    
    def preload_model(self):
        """Pre-load model on startup"""
        print("="*70)
        print("MODEL LOADING")
        print("="*70)
        
        self.app_status_message_set("Loading model...")
        
        if not PYTORCH_AVAILABLE:
            error_msg = "ERROR: PyTorch not installed!"
            self.app_status_message_set(error_msg)
            QMessageBox.critical(self, "PyTorch Not Found", error_msg)
            return
        
        if not DEFAULT_MODEL_DIR.exists():
            error_msg = f"ERROR: Model directory not found!\n{DEFAULT_MODEL_DIR}"
            self.app_status_message_set(error_msg)
            QMessageBox.critical(self, "Directory Not Found", error_msg)
            return
        
        model_path = None
        if DEFAULT_MODEL_PATH.exists():
            model_path = DEFAULT_MODEL_PATH
        elif BEST_MODEL_PATH.exists():
            model_path = BEST_MODEL_PATH
        
        if model_path is None:
            error_msg = "ERROR: Model file not found!"
            self.app_status_message_set(error_msg)
            QMessageBox.critical(self, "Model Not Found", error_msg)
            return
        
        try:
            if torch.backends.mps.is_available():
                device = 'mps'
            elif torch.cuda.is_available():
                device = 'cuda'
            else:
                device = 'cpu'
            
            self.detector = HumanDetector(
                model_path=model_path,
                device=device,
                confidence_threshold=0.95
            )
            
            model_info = self.detector.get_model_info()
            self.app_status_message_set(f"Model loaded ({device.upper()}) - Val Acc: {model_info['val_accuracy']:.2f}%")
            
        except Exception as e:
            error_msg = f"ERROR: Failed to load model!\n{str(e)}"
            self.app_status_message_set(error_msg)
            QMessageBox.critical(self, "Model Load Error", error_msg)
            traceback.print_exc()
    
    def start_sensor_btn_handler(self):
        """Start sensor and begin detection"""
        if self.detector is None:
            error_msg = "ERROR: Model not loaded!"
            self.app_status_message_set(error_msg)
            QMessageBox.warning(self, "Model Not Loaded", error_msg)
            return
        
        try:
            self.app_status_message_set("Starting RedPitaya sensor...")
            commands = ["cd /usr/RedPitaya/Examples/C", "./dma_with_udp_faster"]
            full_command = " && ".join(commands)
            self.rp_sensor.give_ssh_command(full_command)
            time.sleep(3)
            
            self.start_time, self.header_info = self.rp_sensor.get_data_info_from_server()
            time.sleep(1)
            
            self.app_status_message_set(f"Sensor started - Processing {SIGNALS_PER_SECOND} valid signals/sec")
            
            self.worker = DetectionWorker(
                self.rp_sensor,
                self.detector,
                self.start_time,
                self.distance_threshold_cm
            )
            
            self.worker.signals.result.connect(self.update_detection_result)
            self.worker.signals.total_signals_count_updated.connect(self.total_signal_status_message_set)
            self.worker.signals.broken_signals_count_updated.connect(self.broken_signal_status_message_set)
            self.worker.signals.activity_detected.connect(self.activity_detected_handler)
            self.worker.signals.led_state_changed.connect(self.led_state_changed_handler)
            
            self.threadpool.start(self.worker)
            
            self.detection_active = True
            
        except Exception as e:
            error_msg = f"ERROR: Failed to start sensor!\n{str(e)}"
            self.app_status_message_set(error_msg)
            QMessageBox.critical(self, "Sensor Error", error_msg)
            traceback.print_exc()
    
    def stop_sensor_btn_handler(self):
        """Stop sensor and detection"""
        try:
            if self.worker:
                self.worker.stop()
            
            command = "pidof dma_with_udp_faster"
            pid = self.rp_sensor.give_ssh_command(command)
            if pid:
                command1 = f"kill {pid}"
                self.rp_sensor.give_ssh_command(command1)
            
            self.human_blink_timer.stop()
            self.non_human_blink_timer.stop()
            self.activity_blink_timer.stop()
            self.reset_buttons()
            
            self.detection_active = False
            self.current_detection = None
            self.app_status_message_set("Sensor stopped")
            
            self.activity_indicator.setText("IDLE")
            self.activity_indicator.setStyleSheet("""
                font-size: 20px; 
                font-weight: bold; 
                color: #666666;
                border: 2px solid #333;
                border-radius: 5px;
                padding: 10px;
                background-color: #f0f0f0;
            """)
            
            self.led_status_label.setText("OFF")
            self.led_status_label.setStyleSheet("""
                font-size: 28px; 
                font-weight: bold; 
                color: #666666;
                border: 2px solid #333;
                border-radius: 5px;
                padding: 10px;
                background-color: #f0f0f0;
            """)
            
            self.timer_counter_label.setText("Timer: 0.0s")
            self.rate_label.setText(f"Valid: 0 | Rate: 0.00/s (Target: {SIGNALS_PER_SECOND})")
            
        except Exception as e:
            error_msg = f"ERROR: Failed to stop sensor!\n{str(e)}"
            self.app_status_message_set(error_msg)
            traceback.print_exc()
    
    def activity_detected_handler(self, activity_count, distance_change):
        """Handle activity detection"""
        self.activity_count_label.setText(f"Count: {activity_count}")
        
        self.activity_blink_count = 0
        self.activity_blink_timer.start(200)
    
    def led_state_changed_handler(self, led_state, reason):
        """Handle LED state changes"""
        if led_state:
            self.led_status_label.setText("ON")
            self.led_status_label.setStyleSheet("""
                font-size: 28px; 
                font-weight: bold; 
                color: white;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                padding: 10px;
                background-color: #4CAF50;
            """)
        else:
            self.led_status_label.setText("OFF")
            self.led_status_label.setStyleSheet("""
                font-size: 28px; 
                font-weight: bold; 
                color: #666666;
                border: 2px solid #333;
                border-radius: 5px;
                padding: 10px;
                background-color: #f0f0f0;
            """)
            self.timer_counter_label.setText("Timer: 0.0s")
    
    def blink_activity_indicator(self):
        """Blink activity indicator"""
        if self.activity_blink_count < 10:
            if self.activity_blink_state:
                self.activity_indicator.setText("ACTIVE!")
                self.activity_indicator.setStyleSheet("""
                    font-size: 20px; 
                    font-weight: bold; 
                    color: white;
                    border: 2px solid #FF5722;
                    border-radius: 5px;
                    padding: 10px;
                    background-color: #FF5722;
                """)
            else:
                self.activity_indicator.setText("ACTIVE!")
                self.activity_indicator.setStyleSheet("""
                    font-size: 20px; 
                    font-weight: bold; 
                    color: #FF5722;
                    border: 2px solid #FF5722;
                    border-radius: 5px;
                    padding: 10px;
                    background-color: #f0f0f0;
                """)
            
            self.activity_blink_state = not self.activity_blink_state
            self.activity_blink_count += 1
        else:
            self.activity_blink_timer.stop()
            self.activity_indicator.setText("IDLE")
            self.activity_indicator.setStyleSheet("""
                font-size: 20px; 
                font-weight: bold; 
                color: #666666;
                border: 2px solid #333;
                border-radius: 5px;
                padding: 10px;
                background-color: #f0f0f0;
            """)
    
    def update_detection_result(self, result):
        """Update UI with detection result"""
        prediction = result['prediction']
        confidence = result['confidence']
        distance = result['distance']
        led_state = result.get('led_state', False)
        timer_counter = result.get('timer_counter', 0.0)
        actual_rate = result.get('actual_rate', 0)
        valid_count = result.get('valid_count', 0)
        broken_count = result.get('broken_count', 0)
        activity_detected = result.get('activity_detected', False)
        
        self.human_count_label.setText(f"Human: {result['human']}")
        self.non_human_count_label.setText(f"Non-Human: {result['non_human']}")
        self.uncertain_count_label.setText(f"Uncertain: {result['uncertain']}")
        self.inference_time_label.setText(f"Inference: {result['inference_time']:.1f} ms")
        
        # Update rate display
        if actual_rate > 0:
            rate_diff = abs(actual_rate - SIGNALS_PER_SECOND)
            rate_color = "#4CAF50" if rate_diff < 0.2 else "#FF9800" if rate_diff < 0.5 else "#F44336"
            self.rate_label.setText(
                f"Valid: {valid_count} | Rate: {actual_rate:.2f}/s (Target: {SIGNALS_PER_SECOND})"
            )
            self.rate_label.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {rate_color};")
        
        if distance is not None:
            self.distance_value_label.setText(f"{distance} cm")
        else:
            self.distance_value_label.setText("-- cm")
        
        # Show "NA" when LED is OFF (before activity detected), show confidence when LED is ON (CNN active)
        if not led_state:
            # LED is OFF - no activity detected yet, show NA
            self.confidence_value_label.setText("NA")
        else:
            # LED is ON - activity detected, CNN is classifying, show confidence
            self.confidence_value_label.setText(f"{confidence*100:.1f}%")
        
        # Update timer counter display
        if led_state:
            self.timer_counter_label.setText(f"Timer: {timer_counter:.1f}s")
            self.led_status_label.setText("ON")
            self.led_status_label.setStyleSheet("""
                font-size: 28px; 
                font-weight: bold; 
                color: white;
                border: 2px solid #4CAF50;
                border-radius: 5px;
                padding: 10px;
                background-color: #4CAF50;
            """)
        else:
            self.timer_counter_label.setText("Timer: 0.0s")
            self.led_status_label.setText("OFF")
            self.led_status_label.setStyleSheet("""
                font-size: 28px; 
                font-weight: bold; 
                color: #666666;
                border: 2px solid #333;
                border-radius: 5px;
                padding: 10px;
                background-color: #f0f0f0;
            """)
        
        if prediction != self.current_detection:
            self.human_blink_timer.stop()
            self.non_human_blink_timer.stop()
            self.reset_buttons()
            
            self.current_detection = prediction
            
            if prediction == 1:
                self.human_blink_state = False
                self.human_blink_timer.start(500)
            elif prediction == 0:
                self.non_human_blink_state = False
                self.non_human_blink_timer.start(500)
        
        self.plot_adc_data(result['signal'])
    
    def blink_human_button(self):
        """Blink HUMAN button green"""
        if self.human_blink_state:
            self.human_button.setStyleSheet("""
                QPushButton {
                    font-size: 24px;
                    font-weight: bold;
                    background-color: #4CAF50;
                    color: white;
                    border: 2px solid #2E7D32;
                    border-radius: 5px;
                }
            """)
        else:
            self.human_button.setStyleSheet("""
                QPushButton {
                    font-size: 24px;
                    font-weight: bold;
                    background-color: #2E7D32;
                    color: white;
                    border: 2px solid #1B5E20;
                    border-radius: 5px;
                }
            """)
        self.human_blink_state = not self.human_blink_state
    
    def blink_non_human_button(self):
        """Blink NON-HUMAN button red"""
        if self.non_human_blink_state:
            self.non_human_button.setStyleSheet("""
                QPushButton {
                    font-size: 24px;
                    font-weight: bold;
                    background-color: #F44336;
                    color: white;
                    border: 2px solid #C62828;
                    border-radius: 5px;
                }
            """)
        else:
            self.non_human_button.setStyleSheet("""
                QPushButton {
                    font-size: 24px;
                    font-weight: bold;
                    background-color: #C62828;
                    color: white;
                    border: 2px solid #B71C1C;
                    border-radius: 5px;
                }
            """)
        self.non_human_blink_state = not self.non_human_blink_state
    
    def reset_buttons(self):
        """Reset both buttons to gray"""
        self.human_button.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                font-weight: bold;
                background-color: #555555;
                color: white;
                border: 2px solid #333;
                border-radius: 5px;
            }
        """)
        self.non_human_button.setStyleSheet("""
            QPushButton {
                font-size: 24px;
                font-weight: bold;
                background-color: #555555;
                color: white;
                border: 2px solid #333;
                border-radius: 5px;
            }
        """)
        self.human_blink_state = False
        self.non_human_blink_state = False
    
    def plot_adc_data(self, data):
        """Plot ADC data with fixed axis ranges"""
        self.server_message_widget.setText(self.rp_sensor.get_sensor_status_message())
        self.plot_widget.clear()
        
        # Create x-axis based on actual data length
        x = [i for i in range(len(data))]
        y = data
        
        self.plot_widget.plot(x, y, pen='y')
        
        # Ensure axis ranges stay fixed regardless of data length
        # This ensures signals at different distances (400cm, 600cm, etc.) 
        # always display within the same fixed window
        # Y-axis: -6000 to +6000 (amplitude)
        # X-axis: 0 to 25000 (samples)
        self.plot_widget.setYRange(-6000, 6000, padding=0)
        self.plot_widget.setXRange(0, 25000, padding=0)
    
    def app_status_message_set(self, text):
        """Set app status message"""
        self.app_status_message = text
        self.app_message_widget.setText(text)
    
    def total_signal_status_message_set(self, count):
        """Update total signal count"""
        self.total_signal_count_message_widget.setText(f"Total: {count}")
    
    def broken_signal_status_message_set(self, count):
        """Update broken signal count"""
        self.broken_signal_count_message_widget.setText(f"Broken: {count}")
    
    def closeEvent(self, event):
        """Handle window close"""
        if self.worker:
            self.worker.stop()
            self.threadpool.waitForDone()
        
        self.human_blink_timer.stop()
        self.non_human_blink_timer.stop()
        self.activity_blink_timer.stop()
        
        event.accept()
