"""
Detection worker thread with rate control
"""

import time
import traceback
from collections import deque

from PyQt6.QtCore import QRunnable, pyqtSlot, QObject, pyqtSignal

from config import (
    SIGNAL_DELAY,
    SIGNALS_PER_SECOND,
    LED_TIMER_DURATION
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
    """Worker thread with rate control - 2 VALID signals per second"""
    
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
        
        # LED state management
        self.led_state = False
        self.led_timer_start = None
        self.current_detection_state = None
        
        # Rate tracking for VALID signals only
        self.last_valid_signal_time = None
        self.valid_signal_times = deque(maxlen=10)
        self.valid_signal_count = 0

    @pyqtSlot()
    def run(self):
        """Main detection loop with rate control for VALID signals only"""
        self._print_startup_info()
        
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
                
                # VALID DATA - Start rate control timing
                valid_signal_start_time = time.time()
                
                # Convert to numpy array
                signal_array = data.to_numpy()
                
                self.valid_signal_count += 1
                
                # STEP 1: Activity Detection
                activity_detected, distance_change = self._check_activity(distance)
                
                # STEP 2: CNN Classification
                inference_time, prediction, confidence, class_name, probs = self._run_classification(signal_array)
                
                # STEP 3: Timer Management
                self._manage_led_timer()
                
                # Calculate actual VALID signal rate
                actual_rate = self._calculate_rate()
                
                # Prepare result
                result = self._build_result(
                    data, prediction, confidence, class_name, probs,
                    inference_time, distance, activity_detected,
                    distance_change, actual_rate
                )
                
                self.signals.result.emit(result)
                
                # RATE CONTROL - Sleep ONLY for valid signals
                self._apply_rate_control(valid_signal_start_time)
                
            except Exception as e:
                print(f"Error in detection loop: {e}")
                traceback.print_exc()
            finally:
                self.signals.finished.emit()
    
    def _print_startup_info(self):
        """Print startup information"""
        print("="*70)
        print("RATE-CONTROLLED DETECTION STARTED (VALID SIGNALS ONLY)")
        print("="*70)
        print(f"Target Rate: {SIGNALS_PER_SECOND} VALID signals/second")
        print(f"Signal Delay: {SIGNAL_DELAY:.3f} seconds (between valid signals)")
        print(f"Distance Threshold: {self.distance_threshold_cm} cm")
        print(f"LED Timer Duration: {LED_TIMER_DURATION} seconds")
        print("="*70)
        print("NOTE: Broken signals are skipped immediately without delay")
        print("="*70)
    
    def _check_activity(self, distance):
        """Check for activity based on distance change"""
        activity_detected = False
        distance_change = 0
        
        if self.previous_distance is not None and distance is not None:
            distance_change = abs(distance - self.previous_distance)
            
            if distance_change > self.distance_threshold_cm:
                activity_detected = True
                self.activity_count += 1
                print(f"\n[ACTIVITY #{self.activity_count}] Distance change: {distance_change:.1f} cm")
                
                # Turn ON LED7 for 15 seconds
                if not self.led_state:
                    self.rp_sensor.control_led7(turn_on=True)
                    self.led_state = True
                    self.led_timer_start = time.time()
                    print(f"[LED] ON - Timer started ({LED_TIMER_DURATION}s)")
                
                self.signals.activity_detected.emit(self.activity_count, distance_change)
        
        # Update previous distance
        self.previous_distance = distance
        
        return activity_detected, distance_change
    
    def _run_classification(self, signal_array):
        """Run CNN classification"""
        start_time_pred = time.time()
        prediction, confidence, class_name, probs = self.detector.predict(signal_array)
        inference_time = (time.time() - start_time_pred) * 1000
        
        # COUNT IMMEDIATELY BASED ON CNN RESULT
        if prediction == 1:
            self.human_detections += 1
            self.current_detection_state = 'human'
            print(f"[Valid #{self.valid_signal_count}] HUMAN ({confidence*100:.1f}%) - Total: {self.human_detections}")
        elif prediction == 0:
            self.non_human_detections += 1
            self.current_detection_state = 'non-human'
            print(f"[Valid #{self.valid_signal_count}] NON-HUMAN ({confidence*100:.1f}%) - Total: {self.non_human_detections}")
        else:
            self.uncertain_detections += 1
            self.current_detection_state = None
            print(f"[Valid #{self.valid_signal_count}] UNCERTAIN ({confidence*100:.1f}%) - Total: {self.uncertain_detections}")
        
        return inference_time, prediction, confidence, class_name, probs
    
    def _manage_led_timer(self):
        """Manage LED timer based on detection state"""
        if self.led_state and self.led_timer_start:
            elapsed_time = time.time() - self.led_timer_start
            
            if elapsed_time >= LED_TIMER_DURATION:
                if self.current_detection_state == 'human':
                    # HUMAN -> RESET TIMER
                    self.led_timer_start = time.time()
                    print(f"[TIMER] {LED_TIMER_DURATION}s elapsed - HUMAN detected -> RESET for {LED_TIMER_DURATION}s")
                    self.signals.led_state_changed.emit(True, "TIMER_RESET")
                
                elif self.current_detection_state == 'non-human':
                    # NON-HUMAN -> LED OFF
                    self.rp_sensor.control_led7(turn_on=False)
                    self.led_state = False
                    self.led_timer_start = None
                    print(f"[TIMER] {LED_TIMER_DURATION}s elapsed - NON-HUMAN -> LED OFF")
                    self.signals.led_state_changed.emit(False, "NON_HUMAN")
                
                else:
                    # UNCERTAIN -> LED OFF
                    self.rp_sensor.control_led7(turn_on=False)
                    self.led_state = False
                    self.led_timer_start = None
                    print(f"[TIMER] {LED_TIMER_DURATION}s elapsed - UNCERTAIN -> LED OFF")
                    self.signals.led_state_changed.emit(False, "UNCERTAIN")
    
    def _calculate_rate(self):
        """Calculate actual valid signal rate"""
        current_time = time.time()
        self.valid_signal_times.append(current_time)
        
        if len(self.valid_signal_times) >= 2:
            time_span = self.valid_signal_times[-1] - self.valid_signal_times[0]
            actual_rate = (len(self.valid_signal_times) - 1) / time_span if time_span > 0 else 0
        else:
            actual_rate = 0
        
        return actual_rate
    
    def _build_result(self, data, prediction, confidence, class_name, probs,
                     inference_time, distance, activity_detected,
                     distance_change, actual_rate):
        """Build result dictionary"""
        return {
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
            'timer_active': self.led_timer_start is not None,
            'actual_rate': actual_rate,
            'valid_count': self.valid_signal_count,
            'broken_count': self.broken_signals_count
        }
    
    def _apply_rate_control(self, valid_signal_start_time):
        """Apply rate control by sleeping if necessary"""
        elapsed = time.time() - valid_signal_start_time
        if elapsed < SIGNAL_DELAY:
            sleep_time = SIGNAL_DELAY - elapsed
            print(f"[RATE] Sleeping {sleep_time:.3f}s (Processing: {elapsed:.3f}s)")
            time.sleep(sleep_time)
        else:
            print(f"[RATE WARNING] Processing took {elapsed:.3f}s (target: {SIGNAL_DELAY:.3f}s)")
    
    def stop(self):
        """Stop the worker and turn off LED"""
        self.is_running = False
        if self.led_state:
            self.rp_sensor.control_led7(turn_on=False)
            print("Worker stopped - LED7 turned OFF")
        
        # Print final statistics
        self._print_final_statistics()
    
    def _print_final_statistics(self):
        """Print final detection statistics"""
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