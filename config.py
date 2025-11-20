"""
Configuration constants for Human Detection System
"""

from pathlib import Path

# ============================================================================
# Model Configuration
# ============================================================================

# Default paths
DEFAULT_MODEL_DIR = Path("/Volumes/Works/Individual_Project/models")
DEFAULT_MODEL_PATH = DEFAULT_MODEL_DIR / "human_detector_m4_mps.pth"
BEST_MODEL_PATH = DEFAULT_MODEL_DIR / "best_model_mps.pth"

# Model parameters
MODEL_CONFIDENCE_THRESHOLD = 0.95
MODEL_NUM_CLASSES = 2
MODEL_DROPOUT_RATE = 0.5

# ============================================================================
# Spectrogram Configuration
# ============================================================================

# Spectrogram parameters - MUST MATCH training
FS = 1953125              # Sampling frequency (Hz)
NPERSEG = 2048           # Segment length for FFT
NOVERLAP = 1024          # Overlap between segments (50%)
WINDOW = "hamming"       # Window type
MODE = "magnitude"       # Spectrogram mode

# Expected spectrogram shape
EXPECTED_FREQ_BINS = 1025
EXPECTED_TIME_BINS = 18

# ============================================================================
# Detection Configuration
# ============================================================================

# Distance calculation constants
SPEED_OF_SOUND = 343.0  # m/s at 20°C
SENSOR_HEIGHT_CM = 216  # Sensor setup height in cm

# Default distance threshold
DEFAULT_DISTANCE_THRESHOLD_CM = 10  # 10 cm default

# Signal processing rate control (for VALID signals only)
SIGNALS_PER_SECOND = 2  # Process 2 VALID signals per second
SIGNAL_DELAY = 1.0 / SIGNALS_PER_SECOND  # 0.5 seconds between valid signals

# Two-step detection timing
LED_TIMER_DURATION = 15  # 15 seconds

# ============================================================================
# RedPitaya Configuration
# ============================================================================

# Connection settings
REDPITAYA_HOST_IP = "169.254.148.148"
REDPITAYA_DATA_PORT = 61231
REDPITAYA_SSH_PORT = 22
REDPITAYA_SSH_USER = "root"
REDPITAYA_SSH_PASSWORD = "root"

# Data settings
SIZE_OF_RAW_ADC = 25000

# LED control commands
LED7_ON_COMMAND = "/opt/redpitaya/bin/monitor 0x40000030 0x80"
LED7_OFF_COMMAND = "/opt/redpitaya/bin/monitor 0x40000030 0x0"

# ============================================================================
# UI Configuration
# ============================================================================

# Window settings
WINDOW_TITLE = "Human Detection System v2.0"

# Button sizes
DETECTION_BUTTON_WIDTH = 180
DETECTION_BUTTON_HEIGHT = 100

# Timer settings
BLINK_TIMER_INTERVAL = 500  # ms
ACTIVITY_BLINK_INTERVAL = 200  # ms
ACTIVITY_BLINK_COUNT = 10

# ============================================================================
# Application Metadata
# ============================================================================

APP_VERSION = "2.0"
APP_NAME = "Human Detection System"
APP_DESCRIPTION = f"{APP_NAME} - Rate Controlled: {SIGNALS_PER_SECOND} VALID signals per second"