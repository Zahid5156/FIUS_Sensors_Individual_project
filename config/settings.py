# config/settings.py
# Configuration settings for the Human Detection System

from pathlib import Path

# ============================================================================
# Model Configuration
# ============================================================================

# Default paths
DEFAULT_MODEL_DIR = Path("/Volumes/Works/gitupload/model")
DEFAULT_MODEL_PATH = DEFAULT_MODEL_DIR / "best_model_mps.pth"
BEST_MODEL_PATH = DEFAULT_MODEL_DIR / "best_model_mps.pth"

# ============================================================================
# Spectrogram Parameters (MUST MATCH training)
# ============================================================================

FS = 1953125              # Sampling frequency (Hz)
NPERSEG = 2048           # Segment length for FFT
NOVERLAP = 1024          # Overlap between segments (50%)
WINDOW = "hamming"       # Window type
MODE = "magnitude"       # Spectrogram mode

# Expected spectrogram shape
EXPECTED_FREQ_BINS = 1025
EXPECTED_TIME_BINS = 18

# ============================================================================
# Distance Calculation Constants
# ============================================================================

SPEED_OF_SOUND = 343.0  # m/s at 20°C
SENSOR_HEIGHT_CM = 216  # Sensor setup height in cm

# Default distance threshold
DEFAULT_DISTANCE_THRESHOLD_CM = 10  # 10 cm default

# ============================================================================
# LED Control Commands
# ============================================================================

LED7_ON_COMMAND = "/opt/redpitaya/bin/monitor 0x40000030 0x80"
LED7_OFF_COMMAND = "/opt/redpitaya/bin/monitor 0x40000030 0x0"

# ============================================================================
# Detection Timing Configuration
# ============================================================================

# Two-step detection timing
LED_TIMER_DURATION = 15  # 15 seconds

# Signal processing rate control (for VALID signals only)
SIGNALS_PER_SECOND = 2  # Process 2 VALID signals per second
SIGNAL_DELAY = 1.0 / SIGNALS_PER_SECOND  # 0.5 seconds between valid signals

# ============================================================================
# RedPitaya Connection Settings
# ============================================================================

REDPITAYA_HOST_IP = "169.254.148.148"
REDPITAYA_DATA_PORT = 61231
REDPITAYA_SSH_PORT = 22
SIZE_OF_RAW_ADC = 25000
