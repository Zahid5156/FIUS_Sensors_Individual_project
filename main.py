"""
Human Detection System - Main Entry Point
Version 2.0 - Rate Controlled Detection
"""

import sys
from PyQt6.QtWidgets import QApplication

from config import (
    APP_NAME, APP_VERSION, APP_DESCRIPTION,
    SIGNALS_PER_SECOND, SIGNAL_DELAY,
    DEFAULT_DISTANCE_THRESHOLD_CM, LED_TIMER_DURATION
)
from ui.main_window import MainWindow


def print_startup_banner():
    """Print startup information banner"""
    print("="*70)
    print(f"{APP_NAME.upper()} v{APP_VERSION} - RATE CONTROLLED")
    print("="*70)
    print(f"Processing Rate: {SIGNALS_PER_SECOND} VALID signals per second")
    print(f"Signal Delay: {SIGNAL_DELAY:.3f} seconds (between valid signals)")
    print(f"Default Distance Threshold: {DEFAULT_DISTANCE_THRESHOLD_CM} cm")
    print(f"LED Timer Duration: {LED_TIMER_DURATION} seconds")
    print("="*70)
    print("KEY FEATURES:")
    print("  ✓ Rate control applies ONLY to valid signals")
    print("  ✓ Broken signals are skipped immediately (no delay)")
    print("  ✓ Activity detected -> LED ON for 15 seconds")
    print("  ✓ CNN continuously checks: HUMAN or NON-HUMAN")
    print("  ✓ If HUMAN after 15s -> RESET timer for another 15s")
    print("  ✓ If NON-HUMAN after 15s -> LED OFF")
    print("  ✓ Real-time rate monitoring displayed in UI")
    print("="*70)


def main():
    """Main application entry point"""
    print_startup_banner()
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()