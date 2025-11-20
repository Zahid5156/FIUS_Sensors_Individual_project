"""
Main window UI for Human Detection System
"""

import sys
import time
import traceback
from pathlib import Path

from PyQt6.QtCore import Qt, QThreadPool
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QPushButton, QGridLayout, QHBoxLayout, QVBoxLayout,
    QLabel, QLineEdit, QGroupBox, QMessageBox, QApplication
)

import pyqtgraph as pg

from config import (
    WINDOW_TITLE, APP_VERSION, APP_DESCRIPTION,
    DEFAULT_MODEL_PATH, BEST_MODEL_PATH, DEFAULT_MODEL_DIR,
    DEFAULT_DISTANCE_THRESHOLD_CM,
    SIGNALS_PER_SECOND
)
from hardware.redpitaya import RedPitayaSensor
from detection.detector import HumanDetector
from detection.worker import DetectionWorker
from ui.widgets import DetectionButton, StatusLabel, ActivityIndicator, LEDStatusLabel
from ui.styles import StyleSheets, Colors

try:
    import torch
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False


class MainWindow(QMainWindow):
    """Main window with rate-controlled detection"""
    
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
        self.current_detection = None
        
        # Setup UI
        self.setWindowTitle(f"{WINDOW_TITLE} - {SIGNALS_PER_SECOND} valid signals/sec")
        self._init_ui()
        
        # Pre-load model
        self.preload_model()
    
    def _init_ui(self):
        """Initialize the user interface"""
        # Main layout
        main_layout = QGridLayout()
        
        # Plot widget
        self._create_plot_widget(main_layout)
        
        # Detection buttons section
        self._create_detection_section(main_layout)
        
        # Settings section
        self._create_settings_section(main_layout)
        
        # Message section
        self._create_message_section(main_layout)
        
        # Statistics section
        self._create_statistics_section(main_layout)
        
        # Control buttons
        self._create_control_section(main_layout)
        
        # Set central widget
        self.widget = QWidget()
        self.widget.setLayout(main_layout)
        self.setCentralWidget(self.widget)
    
    def _create_plot_widget(self, layout):
        """Create plot widget for signal visualization"""
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('black')
        self.plot_widget.setLabel('left', 'Amplitude (ADC)', color='white')
        self.plot_widget.setLabel('bottom', 'Sample', color='white')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self.plot_widget, 0, 0, 1, 3)
    
    def _create_detection_section(self, layout):
        """Create detection buttons and status displays"""
        buttons_layout = QHBoxLayout()
        
        # HUMAN Button
        self.human_button = DetectionButton("HUMAN")
        buttons_layout.addWidget(self.human_button)
        
        # NON-HUMAN Button
        self.non_human_button = DetectionButton("NON-HUMAN")
        buttons_layout.addWidget(self.non_human_button)
        
        # LED Status Display
        led_vbox = QVBoxLayout()
        self.led_label = QLabel("LED7 Status:")
        self.led_label.setStyleSheet(StyleSheets.small_label(bold=True))
        led_vbox.addWidget(self.led_label)
        
        self.led_status_label = LEDStatusLabel()
        led_vbox.addWidget(self.led_status_label)
        buttons_layout.addLayout(led_vbox)
        
        # Distance Display
        distance_vbox = QVBoxLayout()
        self.distance_label = QLabel("Distance:")
        self.distance_label.setStyleSheet(StyleSheets.small_label(bold=True))
        distance_vbox.addWidget(self.distance_label)
        
        self.distance_value_label = StatusLabel("-- cm")
        self.distance_value_label.set_color(Colors.STATUS_INFO)
        distance_vbox.addWidget(self.distance_value_label)
        buttons_layout.addLayout(distance_vbox)
        
        # Confidence Display
        confidence_vbox = QVBoxLayout()
        self.confidence_label_text = QLabel("Confidence:")
        self.confidence_label_text.setStyleSheet(StyleSheets.small_label(bold=True))
        confidence_vbox.addWidget(self.confidence_label_text)
        
        self.confidence_value_label = StatusLabel("--")
        self.confidence_value_label.set_color(Colors.HUMAN_PRIMARY)
        confidence_vbox.addWidget(self.confidence_value_label)
        buttons_layout.addLayout(confidence_vbox)
        
        # Activity Indicator
        activity_vbox = QVBoxLayout()
        self.activity_label = QLabel("Activity:")
        self.activity_label.setStyleSheet(StyleSheets.small_label(bold=True))
        activity_vbox.addWidget(self.activity_label)
        
        self.activity_indicator = ActivityIndicator()
        activity_vbox.addWidget(self.activity_indicator)
        
        self.activity_count_label = QLabel("Count: 0")
        self.activity_count_label.setStyleSheet(StyleSheets.small_label(bold=True))
        self.activity_count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        activity_vbox.addWidget(self.activity_count_label)
        buttons_layout.addLayout(activity_vbox)
        
        layout.addLayout(buttons_layout, 1, 0, 1, 3)
    
    def _create_settings_section(self, layout):
        """Create settings section"""
        settings_group = QGroupBox("Detection Settings")
        settings_layout = QHBoxLayout()
        
        # Distance threshold
        self.threshold_label = QLabel("Distance Threshold (cm):")
        self.threshold_label.setStyleSheet(StyleSheets.small_label(bold=True))
        settings_layout.addWidget(self.threshold_label)
        
        self.threshold_input = QLineEdit()
        self.threshold_input.setText(str(DEFAULT_DISTANCE_THRESHOLD_CM))
        self.threshold_input.setFixedWidth(80)
        self.threshold_input.setStyleSheet(StyleSheets.input_field())
        settings_layout.addWidget(self.threshold_input)
        
        self.set_threshold_btn = QPushButton("Set Threshold")
        self.set_threshold_btn.clicked.connect(self.set_threshold_handler)
        self.set_threshold_btn.setStyleSheet(StyleSheets.button_default())
        settings_layout.addWidget(self.set_threshold_btn)
        
        self.current_threshold_label = QLabel(f"Current: {DEFAULT_DISTANCE_THRESHOLD_CM} cm")
        self.current_threshold_label.setStyleSheet(StyleSheets.small_label(bold=True, color=Colors.STATUS_INFO))
        settings_layout.addWidget(self.current_threshold_label)
        
        settings_layout.addStretch()
        
        # Rate display
        self.rate_label = QLabel(f"Valid: 0 | Rate: 0.00/s (Target: {SIGNALS_PER_SECOND})")
        self.rate_label.setStyleSheet(StyleSheets.small_label(bold=True, color=Colors.STATUS_WARNING))
        settings_layout.addWidget(self.rate_label)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group, 2, 0, 1, 3)
    
    def _create_message_section(self, layout):
        """Create message section"""
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
        self.broken_signal_count_message_widget.setStyleSheet(StyleSheets.small_label(color=Colors.STATUS_ERROR))
        message_layout.addWidget(self.broken_signal_count_message_widget)
        
        layout.addLayout(message_layout, 3, 0, 1, 3)
    
    def _create_statistics_section(self, layout):
        """Create statistics section"""
        stats_layout = QHBoxLayout()
        
        self.human_count_label = QLabel("Human: 0")
        self.human_count_label.setStyleSheet(StyleSheets.medium_label(bold=True, color=Colors.HUMAN_PRIMARY))
        stats_layout.addWidget(self.human_count_label)
        
        self.non_human_count_label = QLabel("Non-Human: 0")
        self.non_human_count_label.setStyleSheet(StyleSheets.medium_label(bold=True, color=Colors.STATUS_ERROR))
        stats_layout.addWidget(self.non_human_count_label)
        
        self.uncertain_count_label = QLabel("Uncertain: 0")
        self.uncertain_count_label.setStyleSheet(StyleSheets.medium_label(bold=True, color=Colors.STATUS_WARNING))
        stats_layout.addWidget(self.uncertain_count_label)
        
        self.inference_time_label = QLabel("Inference: -- ms")
        self.inference_time_label.setStyleSheet(StyleSheets.medium_label())
        stats_layout.addWidget(self.inference_time_label)
        
        layout.addLayout(stats_layout, 4, 0, 1, 3)
    
    def _create_control_section(self, layout):
        """Create control buttons"""
        control_layout = QHBoxLayout()
        
        self.start_sensor_btn = QPushButton("Start Sensor & Detection")
        self.start_sensor_btn.clicked.connect(self.start_sensor_btn_handler)
        self.start_sensor_btn.setStyleSheet(StyleSheets.control_button())
        control_layout.addWidget(self.start_sensor_btn)
        
        self.stop_sensor_btn = QPushButton("Stop Sensor & Detection")
        self.stop_sensor_btn.clicked.connect(self.stop_sensor_btn_handler)
        self.stop_sensor_btn.setStyleSheet(StyleSheets.control_button())
        control_layout.addWidget(self.stop_sensor_btn)
        
        layout.addLayout(control_layout, 5, 0, 1, 3)
    
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
            self.detector = HumanDetector(
                model_path=model_path,
                device='auto',
                confidence_threshold=0.95
            )
            
            model_info = self.detector.get_model_info()
            self.app_status_message_set(f"Model loaded - Val Acc: {model_info['val_accuracy']:.2f}%")
            
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
            
            # Connect signals
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
            
            # Stop all animations
            self.human_button.stop_blinking()
            self.non_human_button.stop_blinking()
            self.activity_indicator.reset()
            self.reset_buttons()
            
            self.detection_active = False
            self.current_detection = None
            self.app_status_message_set("Sensor stopped")
            
            self.led_status_label.set_off()
            self.rate_label.setText(f"Valid: 0 | Rate: 0.00/s (Target: {SIGNALS_PER_SECOND})")
            
        except Exception as e:
            error_msg = f"ERROR: Failed to stop sensor!\n{str(e)}"
            self.app_status_message_set(error_msg)
            traceback.print_exc()
    
    def activity_detected_handler(self, activity_count, distance_change):
        """Handle activity detection"""
        self.activity_count_label.setText(f"Count: {activity_count}")
        self.activity_indicator.trigger_activity()
    
    def led_state_changed_handler(self, led_state, reason):
        """Handle LED state changes"""
        if led_state:
            self.led_status_label.set_on()
        else:
            self.led_status_label.set_off()
    
    def update_detection_result(self, result):
        """Update UI with detection result"""
        prediction = result['prediction']
        confidence = result['confidence']
        distance = result['distance']
        led_state = result.get('led_state', False)
        actual_rate = result.get('actual_rate', 0)
        valid_count = result.get('valid_count', 0)
        
        # Update counts
        self.human_count_label.setText(f"Human: {result['human']}")
        self.non_human_count_label.setText(f"Non-Human: {result['non_human']}")
        self.uncertain_count_label.setText(f"Uncertain: {result['uncertain']}")
        self.inference_time_label.setText(f"Inference: {result['inference_time']:.1f} ms")
        
        # Update rate display
        if actual_rate > 0:
            rate_diff = abs(actual_rate - SIGNALS_PER_SECOND)
            rate_color = Colors.HUMAN_PRIMARY if rate_diff < 0.2 else Colors.STATUS_WARNING if rate_diff < 0.5 else Colors.STATUS_ERROR
            self.rate_label.setText(
                f"Valid: {valid_count} | Rate: {actual_rate:.2f}/s (Target: {SIGNALS_PER_SECOND})"
            )
            self.rate_label.setStyleSheet(StyleSheets.small_label(bold=True, color=rate_color))
        
        # Update distance
        if distance is not None:
            self.distance_value_label.setText(f"{distance} cm")
        else:
            self.distance_value_label.setText("-- cm")
        
        # Update confidence
        self.confidence_value_label.setText(f"{confidence*100:.1f}%")
        
        # Update LED status
        if led_state:
            self.led_status_label.set_on()
        else:
            self.led_status_label.set_off()
        
        # Update detection buttons
        if prediction != self.current_detection:
            self.human_button.stop_blinking()
            self.non_human_button.stop_blinking()
            self.reset_buttons()
            
            self.current_detection = prediction
            
            if prediction == 1:
                self.human_button.start_blinking()
            elif prediction == 0:
                self.non_human_button.start_blinking()
        
        # Update plot
        self.plot_adc_data(result['signal'])
    
    def reset_buttons(self):
        """Reset both buttons to gray"""
        self.human_button.reset_style()
        self.non_human_button.reset_style()
    
    def plot_adc_data(self, data):
        """Plot ADC data"""
        self.server_message_widget.setText(self.rp_sensor.get_sensor_status_message())
        self.plot_widget.clear()
        
        x = [i for i in range(self.rp_sensor.size_of_raw_adc * self.rp_sensor.total_data_blocks)]
        y = data
        
        self.plot_widget.plot(x, y, pen='y')
    
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
        
        self.human_button.stop_blinking()
        self.non_human_button.stop_blinking()
        self.activity_indicator.reset()
        
        event.accept()