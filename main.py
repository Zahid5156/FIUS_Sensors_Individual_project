#!/usr/bin/env python3
# main.py
# Human Detection System - Main Entry Point

import sys
from PyQt6.QtWidgets import QApplication

from src.gui.main_window import MainWindow
from config.settings import (
    SIGNALS_PER_SECOND,
    SIGNAL_DELAY,
    DEFAULT_DISTANCE_THRESHOLD_CM,
    LED_TIMER_DURATION
)


def main():
    """Main entry point for the Human Detection APP"""
    print("="*70)
    print("HUMAN DETECTION APP - COUNTER-BASED LED TIMER")
    print("="*70)
    print(f"Processing Rate: {SIGNALS_PER_SECOND} VALID signals per second")
    print(f"Signal Delay: {SIGNAL_DELAY:.3f} seconds (between valid signals)")
    print(f"Default Distance Threshold: {DEFAULT_DISTANCE_THRESHOLD_CM} cm")
    print(f"LED Timer Duration: {LED_TIMER_DURATION} seconds")
    print("="*70)
    print("KEY FEATURES:")
    print("  ✓ Rate control applies ONLY to valid signals")
    print("  ✓ Broken signals are skipped immediately (no delay)")
    print("  ✓ Activity detected -> LED ON, counter starts at 0s")
    print("  ✓ CNN continuously checks: HUMAN or NON-HUMAN")
    print("  ✓ If HUMAN -> Counter RESETS to 0s (timer restarts)")
    print("  ✓ If counter reaches 15s + HUMAN -> Counter RESETS to 0s (LED stays ON)")
    print("  ✓ If NON-HUMAN/UNCERTAIN -> Counter keeps counting to 15s")
    print("  ✓ If counter reaches 15s + NON-HUMAN -> LED OFF")
    print("  ✓ Real-time counter display in UI")
    print("="*70)
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
