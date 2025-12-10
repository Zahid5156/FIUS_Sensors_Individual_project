# src/workers/detection_worker.py
# Worker Thread with Rate Control for Detection

import time
import traceback
from collections import deque
import numpy as np

from PyQt6.QtCore import QRunnable, pyqtSlot, QObject, pyqtSignal

from config.settings import (
    LED_TIMER_DURATION,
    SIGNALS_PER_SECOND,
    SIGNAL_DELAY
)


class DetectionWorkerSignals(QObject):
    """Signals for detection worker"""
    result = pyqtSignal(object)
    error = pyqtSignal(tuple)
    finished = pyqtSignal()
    total_signals_count_updated = pyqtSignal(int)
    broken_signals_count_updated = pyqtSignal(int)
    activity_detected = pyqtSignal(int, float)
    led_state_changed = pyqtSignal(bool, str)


class DetectionWorker(QRunnable):
    """Worker thread with rate control - 2 VALID signals per second - COUNTER-BASED LED timer"""
    
    def __init__(self, rp_sensor, detector, start_time, distance_threshold_cm):
        super().__init__()
        self.rp_sensor = rp_sensor
        self.detector = detector
        self.start_time = start_time
        self.distance_threshold_cm = distance_threshold_cm
        self.signals = DetectionWorkerSignals()
        self.is_running = True
        
        # Statistics
        self.total_signals_count = 0
        self.broken_signals_count = 0
        self.human_detections = 0
        self.non_human_detections = 0
        self.uncertain_detections = 0
        self.activity_count = 0
        
        # Distance tracking for activity detection
        self.previous_distance = None
        
        # LED state management with COUNTER-BASED timer
        self.led_state = False
        self.led_timer_counter = 0.0  # Counter from 0 to 15 seconds
        self.last_counter_update_time = None  # Timestamp for counter updates
        self.current_detection_state = None
        
        # Rate tracking for VALID signals only
        self.last_valid_signal_time = None
        self.valid_signal_times = deque(maxlen=10)
        self.valid_signal_count = 0

    @pyqtSlot()
    def run(self):
        """Main detection loop with rate control for VALID signals only"""
        print("="*70)
        print("RATE-CONTROLLED DETECTION STARTED (VALID SIGNALS ONLY)")
        print("="*70)
        print(f"Target Rate: {SIGNALS_PER_SECOND} VALID signals/second")
        print(f"Signal Delay: {SIGNAL_DELAY:.3f} seconds (between valid signals)")
        print(f"Distance Threshold: {self.distance_threshold_cm} cm")
        print(f"LED Timer Duration: {LED_TIMER_DURATION} seconds (COUNTER-BASED)")
        print("="*70)
        print("NOTE: Broken signals are skipped immediately without delay")
        print("TIMER LOGIC:")
        print("  - HUMAN detected -> Counter RESETS to 0s (LED stays ON)")
        print("  - If counter reaches 15s + HUMAN -> Counter RESETS to 0s (restarts)")
        print("  - NON-HUMAN detected -> Counter keeps counting to 15s")
        print("  - If counter reaches 15s + NON-HUMAN -> LED turns OFF")
        print("="*70)
        
        while self.is_running:
            try:
                # Get data from sensor (no delay before acquisition)
                header, data, distance = self.rp_sensor.get_data_from_server(self.start_time)
                
                self.total_signals_count += 1
                self.signals.total_signals_count_updated.emit(self.total_signals_count)
                
                # CHECK IF DATA IS VALID
                if data is None or header is None:
                    self.broken_signals_count += 1
                    self.signals.broken_signals_count_updated.emit(self.broken_signals_count)
                    # NO SLEEP for broken signals - immediately try next
                    continue
                
                # ============================================================
                # VALID DATA - Start rate control timing
                # ============================================================
                valid_signal_start_time = time.time()
                
                # OPTIMIZED: data is already numpy array from sensor
                signal_array = data if isinstance(data, np.ndarray) else data.to_numpy()
                
                self.valid_signal_count += 1
                
                # ============================================================
                # STEP 1: Activity Detection (Distance Threshold)
                # ============================================================
                activity_detected = False
                distance_change = 0
                
                if self.previous_distance is not None and distance is not None:
                    distance_change = abs(distance - self.previous_distance)
                    
                    if distance_change > self.distance_threshold_cm:
                        activity_detected = True
                        self.activity_count += 1
                        print(f"\n[ACTIVITY #{self.activity_count}] Distance change: {distance_change:.1f} cm")
                        
                        # Turn ON LED7 and initialize counter
                        if not self.led_state:
                            self.rp_sensor.control_led7(turn_on=True)
                            self.led_state = True
                            self.led_timer_counter = 0.0  # START counter at 0
                            self.last_counter_update_time = time.time()  # Initialize timestamp
                            print(f"[LED] ON - Counter started at 0s (Target: {LED_TIMER_DURATION}s)")
                        
                        self.signals.activity_detected.emit(self.activity_count, distance_change)
                
                # Update previous distance
                self.previous_distance = distance
                
                # ============================================================
                # STEP 2: CNN Classification
                # ============================================================
                start_time_pred = time.time()
                prediction, confidence, class_name, probs = self.detector.predict(signal_array)
                inference_time = (time.time() - start_time_pred) * 1000
                
                # COUNT IMMEDIATELY BASED ON CNN RESULT
                if prediction == 1:
                    self.human_detections += 1
                    self.current_detection_state = 'human'
                    # Reduced logging for performance
                    if self.valid_signal_count % 10 == 0:  # Log every 10th signal
                        print(f"[Valid #{self.valid_signal_count}] HUMAN ({confidence*100:.1f}%) - Total: {self.human_detections}")
                elif prediction == 0:
                    self.non_human_detections += 1
                    self.current_detection_state = 'non-human'
                    if self.valid_signal_count % 10 == 0:
                        print(f"[Valid #{self.valid_signal_count}] NON-HUMAN ({confidence*100:.1f}%) - Total: {self.non_human_detections}")
                else:
                    self.uncertain_detections += 1
                    self.current_detection_state = 'uncertain'
                    if self.valid_signal_count % 10 == 0:
                        print(f"[Valid #{self.valid_signal_count}] UNCERTAIN ({confidence*100:.1f}%) - Total: {self.uncertain_detections}")
                
                # ============================================================
                # STEP 3: Timer Management (COUNTER-BASED)
                # ============================================================
                if self.led_state:
                    # Update counter based on elapsed time since last update
                    current_time = time.time()
                    
                    if self.last_counter_update_time is not None:
                        time_elapsed = current_time - self.last_counter_update_time
                        self.led_timer_counter += time_elapsed
                    
                    self.last_counter_update_time = current_time
                    
                    # Handle detection-based counter logic
                    if self.current_detection_state == 'human':
                        # HUMAN detected -> Check if counter reached 15s or just reset
                        if self.led_timer_counter >= LED_TIMER_DURATION:
                            # Counter reached 15s with HUMAN -> RESET to 0 and continue
                            print(f"[TIMER] Counter: {self.led_timer_counter:.1f}s -> 15s REACHED with HUMAN -> RESET to 0s (LED stays ON)")
                            self.led_timer_counter = 0.0
                            self.signals.led_state_changed.emit(True, "TIMER_RESET_15S")
                        else:
                            # Normal HUMAN detection -> RESET counter to 0 (reduced logging)
                            self.led_timer_counter = 0.0
                            self.signals.led_state_changed.emit(True, "TIMER_RESET")
                    
                    elif self.current_detection_state == 'non-human':
                        # NON-HUMAN detected -> Keep counter counting (reduced logging)
                        
                        # Check if counter reached 15 seconds
                        if self.led_timer_counter >= LED_TIMER_DURATION:
                            # Turn LED OFF
                            self.rp_sensor.control_led7(turn_on=False)
                            self.led_state = False
                            self.led_timer_counter = 0.0
                            self.last_counter_update_time = None
                            print(f"[TIMER] 15s limit reached -> LED OFF (NON-HUMAN)")
                            self.signals.led_state_changed.emit(False, "NON_HUMAN")
                    
                    else:  # UNCERTAIN
                        # UNCERTAIN -> Keep counter counting (reduced logging)
                        
                        # Check if counter reached 15 seconds
                        if self.led_timer_counter >= LED_TIMER_DURATION:
                            # Turn LED OFF
                            self.rp_sensor.control_led7(turn_on=False)
                            self.led_state = False
                            self.led_timer_counter = 0.0
                            self.last_counter_update_time = None
                            print(f"[TIMER] 15s limit reached -> LED OFF (UNCERTAIN)")
                            self.signals.led_state_changed.emit(False, "UNCERTAIN")
                
                # ============================================================
                # Calculate actual VALID signal rate
                # ============================================================
                current_time = time.time()
                self.valid_signal_times.append(current_time)
                
                if len(self.valid_signal_times) >= 2:
                    time_span = self.valid_signal_times[-1] - self.valid_signal_times[0]
                    actual_rate = (len(self.valid_signal_times) - 1) / time_span if time_span > 0 else 0
                else:
                    actual_rate = 0
                
                # Prepare result
                result = {
                    'signal': data,
                    'prediction': prediction,
                    'confidence': confidence,
                    'class_name': class_name,
                    'probs': probs,
                    'inference_time': inference_time,
                    'total': self.total_signals_count,
                    'human': self.human_detections,
                    'non_human': self.non_human_detections,
                    'uncertain': self.uncertain_detections,
                    'distance': distance,
                    'activity_detected': activity_detected,
                    'distance_change': distance_change,
                    'activity_count': self.activity_count,
                    'timestamp': time.strftime('%H:%M:%S'),
                    'led_state': self.led_state,
                    'timer_active': self.led_state,
                    'timer_counter': self.led_timer_counter,
                    'actual_rate': actual_rate,
                    'valid_count': self.valid_signal_count,
                    'broken_count': self.broken_signals_count
                }
                
                self.signals.result.emit(result)
                
                # ============================================================
                # RATE CONTROL - Sleep ONLY for valid signals
                # ============================================================
                elapsed = time.time() - valid_signal_start_time
                if elapsed < SIGNAL_DELAY:
                    sleep_time = SIGNAL_DELAY - elapsed
                    # Reduced logging for performance
                    if self.valid_signal_count % 10 == 0:
                        print(f"[RATE] Sleeping {sleep_time:.3f}s (Processing: {elapsed:.3f}s)")
                    time.sleep(sleep_time)
                else:
                    if self.valid_signal_count % 10 == 0:
                        print(f"[RATE WARNING] Processing took {elapsed:.3f}s (target: {SIGNAL_DELAY:.3f}s)")
                
            except Exception as e:
                print(f"Error in detection loop: {e}")
                traceback.print_exc()
            finally:
                self.signals.finished.emit()
    
    def stop(self):
        """Stop the worker and turn off LED"""
        self.is_running = False
        if self.led_state:
            self.rp_sensor.control_led7(turn_on=False)
            print(f"Worker stopped - LED7 turned OFF (Counter was at {self.led_timer_counter:.1f}s)")
        
        # Print final statistics
        if self.valid_signal_count > 0:
            print("\n" + "="*70)
            print("FINAL STATISTICS")
            print("="*70)
            print(f"Total Signal Attempts: {self.total_signals_count}")
            print(f"Valid Signals Processed: {self.valid_signal_count}")
            print(f"Broken Signals Skipped: {self.broken_signals_count}")
            valid_rate = (self.valid_signal_count / self.total_signals_count * 100) if self.total_signals_count > 0 else 0
            print(f"Valid Signal Rate: {valid_rate:.1f}%")
            print(f"Human Detections: {self.human_detections}")
            print(f"Non-Human Detections: {self.non_human_detections}")
            print(f"Uncertain: {self.uncertain_detections}")
            print("="*70)
