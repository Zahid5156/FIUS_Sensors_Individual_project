# Smart lighting system for electricity saving with Red pitaya and Ultrasonic sensor

## Introduction:
This project presents a energy-efficient human detection system designed for smart office environments using a Red Pitaya STEMlab 125-14 and an SRF02 ultrasonic sensor. Operating on a client-server model via Ethernet, the system captures 25,000 ADC data samples and transmits them via UDP to a Python application for analysis. To maximize energy efficiency, the system utilizes a two-stage detection process: an initial "Activity Detection" stage that uses Distance Threshold 10 cm to identify sudden environmental changes, and a secondary "CNN Classify" stage that employs a pre-trained 2D CNN model on spectrogram data for accurate human classification. Upon confirming human presence, the system activates LED7 on the Red Pitaya board.

![redpitaya](https://github.com/user-attachments/assets/e9d0f54f-ef3a-4613-8029-1166297db405)




## Project Structure
```
project/
├── main.py                      # Application entry point
├── config.py                    # Configuration constants
├── models/
│   ├── __init__.py
│   └── cnn_model.py            # CNN architecture (SpectrogramCNN)
├── detection/
│   ├── __init__.py
│   ├── detector.py             # HumanDetector class
│   └── worker.py               # Detection worker thread
├── hardware/
│   ├── __init__.py
│   └── redpitaya.py            # RedPitaya sensor interface
├── utils/
│   ├── __init__.py
│   └── signal_processing.py    # Signal processing utilities
└── ui/
    ├── __init__.py
    ├── main_window.py          # Main window UI
    ├── widgets.py              # Custom Qt widgets
    └── styles.py               # UI styling constants

```

### Requirements

```bash
pip install PyQt6 pyqtgraph torch scipy numpy pandas paramiko
```
### Dependencies

- Python 3.8+
- PyTorch (with MPS/CUDA support if available)
- PyQt6
- pyqtgraph
- scipy
- numpy
- pandas
- paramiko

## Configuration

Edit `config.py` to customize:

- **Model paths**: Update `DEFAULT_MODEL_DIR`, `DEFAULT_MODEL_PATH`
- **Sensor settings**: Modify RedPitaya IP, ports
- **Detection parameters**: Change `SIGNALS_PER_SECOND`, `DEFAULT_DISTANCE_THRESHOLD_CM`
- **LED timer**: Adjust `LED_TIMER_DURATION`

## Usage

### Running the Application

```bash
python main.py
```

### Basic Workflow

1. **Load Model**: Model is automatically loaded on startup
2. **Set Distance Threshold**: Adjust in the "Detection Settings" section
3. **Start Sensor**: Click "Start Sensor & Detection"
4. **Monitor Detection**: Watch real-time classification (HUMAN/NON-HUMAN)
5. **Stop Sensor**: Click "Stop Sensor & Detection"

## Key Features

- **Rate-Controlled Processing**: 2 valid signals per second
- **Activity Detection**: Based on distance threshold
- **LED Control**: Automatic LED7 control on RedPitaya
- **Two-Step Detection**: 
  - Step 1: Activity detected → LED ON for 15 seconds
  - Step 2: CNN classification every 0.5 seconds
  - If HUMAN after 15s → Reset timer for another 15s
  - If NON-HUMAN after 15s → LED OFF

## Module Details

### `config.py`
Contains all configuration constants including model paths, sensor settings, detection parameters, and UI constants.

### `models/cnn_model.py`
Defines the `SpectrogramCNN` architecture with 4 convolutional blocks and fully connected layers.

### `detection/detector.py`
`HumanDetector` class that loads the CNN model and performs inference on spectrograms.

### `detection/worker.py`
`DetectionWorker` thread that handles:
- Rate-controlled signal acquisition
- Activity detection
- CNN classification
- LED timer management

### `hardware/redpitaya.py`
`RedPitayaSensor` class for:
- UDP communication with RedPitaya
- SSH command execution
- LED7 control
- Distance measurement correction

### `utils/signal_processing.py`
Utility functions for:
- Converting signals to spectrograms
- Distance measurement correction

### `ui/main_window.py`
Main application window with:
- Signal plotting
- Detection display
- Settings controls
- Statistics monitoring

### `ui/widgets.py`
Custom Qt widgets:
- `DetectionButton`: Blinking detection buttons
- `StatusLabel`: Styled status displays
- `ActivityIndicator`: Activity animation
- `LEDStatusLabel`: LED status display

### `ui/styles.py`
Centralized styling:
- Color palette (`Colors` class)
- Pre-defined stylesheets (`StyleSheets` class)

## Customization

### Adding New Detection Algorithms

1. Create a new class in `detection/` directory
2. Implement `predict(signal)` method
3. Update `MainWindow` to use new detector

### Modifying UI

1. Edit `ui/main_window.py` for layout changes
2. Add custom widgets in `ui/widgets.py`
3. Update styles in `ui/styles.py`

### Changing Sensor Hardware

1. Create new sensor class in `hardware/` directory
2. Implement required interface methods
3. Update `MainWindow` to use new sensor

## Troubleshooting

### Model Not Loading
- Check `DEFAULT_MODEL_DIR` path in `config.py`
- Ensure PyTorch is installed
- Verify model file exists

### Sensor Connection Issues
- Verify RedPitaya IP address in `config.py`
- Check network connectivity
- Ensure RedPitaya server is running

### Rate Control Issues
- Adjust `SIGNALS_PER_SECOND` in `config.py`
- Monitor actual rate in UI
- Check for broken signals

## License

[Your License Here]

## Authors

[Your Name/Team]

## Version History

- **v2.0**: Modular refactoring, rate-controlled detection
- **v1.0**: Initial monolithic implementation
