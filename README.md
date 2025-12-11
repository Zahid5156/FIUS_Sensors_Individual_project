# Smart lighting system for electricity saving with Red pitaya and Ultrasonic sensor
## Keywords:
Red Pitaya, Signal Processing, Spectrogram, Short Time Fourier Transform, Convolutional Neural Network, Graphical User Interface. 

## Introduction:
This project presents a energy-efficient human detection system designed for smart office environments using a Red Pitaya STEMlab 125-14 and an SRF02 ultrasonic sensor. Operating on a client-server model via Ethernet, the system captures 25,000 ADC data samples and transmits them via UDP to a Python application for analysis. To maximize energy efficiency, the system utilizes a two-stage detection process: an initial "Activity Detection" stage that uses Distance Threshold 10 cm to identify sudden environmental changes, and a secondary "CNN Classify" stage that employs a pre-trained 2D CNN model on spectrogram data for accurate human classification. Upon confirming human presence, the system activates LED7 on the Red Pitaya board.

![redpitaya](https://github.com/user-attachments/assets/e9d0f54f-ef3a-4613-8029-1166297db405)

## Data Collection:
To build this project, ADC data was collected using a C-based Red Pitaya library (prebuilt as a UDP client and installed in the laboratory). The experimental setup utilized the sensor’s I2C interface to read from the ultrasonic proximity sensor. For data collection, the sensor was mounted on a metal stand at three different heights: 210 cm, 230 cm, and 250 cm, measured from the sensor head to the ground. The total dataset consists of 186,500 signals. The distribution between the two classes is as follows:
```
Class	    Count	  Percentage
Human	    99,500	   53.35%
Non-Human	87,000	   46.65%
Total	    186,500	   100.00%
```
![data01](https://github.com/user-attachments/assets/61e829a9-60c2-4e17-93cf-8979aa65db0e)
## Data Preprocessing:
Raw ultrasonic signals were cleaned by removing the first 5,517 columns and discarding waveforms shorter than 2,048 samples. Valid signals were transformed into magnitude spectrograms via STFT using a 1.953125 MHz sampling rate, a 2,048-sample Hamming window, and 50% overlap. This process yielded 1,025 frequency bins, resulting in a final stacked float32 tensor of shape $(186500, 1025, 18)$. Labels were binary encoded (Human=1, Non-Human=0), and the processed features were serialized as NumPy arrays for training.

![Spectrogram2](https://github.com/user-attachments/assets/125b7a0a-633b-47a8-aa6c-4c14bc90a289)

## Model training:
The preprocessed spectrogram images were fed into a 2D Convolutional Neural Network (CNN) SpectrogramCNN model to classify human and non-human subjects. This model was implemented using PyTorch, chosen for its flexibility and efficiency. The SpectrogramCNN model was evaluated using a randomized 80/20 split on the spectrogram dataset, designating 149,200 samples for training and 37,300 samples for validation. Training was conducted over 15 epochs, requiring approximately 76 minutes. The training dynamics indicated a robust learning process; the model achieved a validation accuracy of 99.53% with a minimal validation loss of 0.0104 at epoch 14, which was selected as the optimal checkpoint. The structure of the 2D CNN model used for classification is given below:

![SpectrogramCNN](https://github.com/user-attachments/assets/c5557be6-0969-4f38-aab0-b278f8cf54a2)


## Project Structure
```
gitupload/
├── main.py                          # Application entry point (run this!)
├── requirements.txt                 # Python dependencies
├── .gitignore                      # Git ignore rules
├── model                           # pth model file
├── jupyter-notebooks                # spectrogram and cnn training files
├── config/                          # Configuration module
│   ├── __init__.py
│   └── settings.py                  # All configuration constants
│
└── src/                             # Source code
    ├── __init__.py
    │
    ├── models/                      # Neural network models
    │   ├── __init__.py
    │   └── cnn_model.py            # SpectrogramCNN architecture
    │
    ├── detection/                   # Detection logic
    │   ├── __init__.py
    │   └── detector.py             # HumanDetector class
    │
    ├── hardware/                    # Hardware interfaces
    │   ├── __init__.py
    │   └── sensor.py               # RedPitayaSensor class
    │
    ├── workers/                     # Background workers
    │   ├── __init__.py
    │   └── detection_worker.py     # DetectionWorker & signals
    │
    └── gui/                         # GUI components
        ├── __init__.py
        └── main_window.py          # MainWindow class

```

### Install Dependencies

```bash
pip install PyQt6 pyqtgraph torch scipy numpy pandas paramiko
```
```bash
# Install all required packages (inside virtual environment)
pip install -r requirements.txt
```

**Alternative (without virtual environment):**
```bash
pip3 install -r requirements.txt --user
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

All configuration is centralized in `config/settings.py`. Edit this file to customize:
To change CNN confidence threshold, edit `src/gui/main_window.py`:


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

### Two-Step Detection
1. **Activity Detection**: Distance change threshold (default: 10 cm)
2. **CNN Classification**: HUMAN vs NON-HUMAN vs UNCERTAIN

### Counter-Based LED Timer
- LED turns ON when activity detected
- Counter starts at 0s, counts up to 15s
- **HUMAN detection** → Counter resets to 0s (LED stays ON)
- **NON-HUMAN/UNCERTAIN** → Counter continues to 15s → LED turns OFF
- If counter reaches 15s + HUMAN → Counter resets (timer restarts)

### Real-time UI
- Live signal plotting (fixed axis: -6000 to +6000 ADC)
- Blinking status indicators
- Counter display (0.0s to 15.0s)
- Configurable thresholds via UI

## Module Details

### 1. **config/settings.py**
Central configuration file containing all constants:
- Model paths and parameters
- Spectrogram settings (FS, NPERSEG, NOVERLAP, etc.)
- Distance calculation constants
- LED control commands
- Detection timing parameters
- RedPitaya connection settings

### 2. **src/models/cnn_model.py**
- **SpectrogramCNN**: PyTorch CNN architecture for human detection
- 4 convolutional blocks with batch normalization and dropout
- Fully connected layers for classification

### 3. **src/detection/detector.py**
- **HumanDetector**: Main detection class
- Loads trained model and performs inference
- Converts raw signals to spectrograms
- Returns predictions with confidence scores

### 4. **src/hardware/sensor.py**
- **RedPitayaSensor**: Interface to RedPitaya hardware
- UDP communication for data acquisition
- SSH commands for LED control
- Distance calculation from sensor data

### 5. **src/workers/detection_worker.py**
- **DetectionWorker**: Background thread for continuous detection
- **DetectionWorkerSignals**: Qt signals for inter-thread communication
- Rate-controlled signal processing (2 valid signals/second)
- Counter-based LED timer management
- Activity detection based on distance threshold

### 6. **src/gui/main_window.py**
- **MainWindow**: PyQt6-based GUI
- Real-time signal visualization
- Detection status indicators (HUMAN/NON-HUMAN)
- LED status and timer display
- Configurable threshold and timer settings
- Statistics display (counts, inference time, rate)

### 7. **main.py**
Clean entry point that:
- Prints startup information
- Initializes QApplication
- Creates and shows MainWindow
- Starts event loop

  ## Graphical User Interface (GUI):
This is the visual representation of the GUI when the model starts: To initiate the system, click the "Start Sensor Detetction" button. This establishes an SSH connection, executes the dma_with_udp_faster.c acquisition code on the Red Pitaya, and confirms the link via a UDP handshake. Once connected, the system immediately begins the analysis pipeline, continuously processing data at a rate of two signals per second.
The interface features large visual indicators—HUMAN (blinks green) and NON-HUMAN (blinks red)—alongside real-time metrics for object distance, model confidence, and LED7 status. Movement is tracked via an "Activity" label (IDLE/ACTIVE) based on a user-adjustable Distance Threshold (default: 10 cm) and LED timer *default 15s). Comprehensive telemetry displays connection status, detection counters, inference time, and signal loss warnings at the bottom of the window, with the entire session controlled via the main Start/Stop buttons.

![gui000](https://github.com/user-attachments/assets/3a3d12d7-4b68-46ad-985e-69425898d06a)

System Demonstration:

In this figure, the system monitors a static background (e.g., floor at 205 cm). Since distance fluctuations do not exceed the 10 cm threshold, the system remains in IDLE mode with LED7 OFF.

 .Classification: The model correctly identifies the environment as NON-HUMAN with 100% confidence.

. Performance: Processing remains stable at 1.82 signals/sec (6.6 ms inference time).

. Robustness: The filter successfully discards incomplete data (1559 broken packets) while processing 81 valid signals (79 Non-Human, 3 Uncertain) with zero false positives.

![gui001](https://github.com/user-attachments/assets/4b4f5a72-11c3-4d85-b486-c2719ef8c22d)

In this scenario, a non-human object (chair) is detected at 154 cm. The sudden distance shift exceeds the threshold, triggering the Activity state (Count: 5) and instantly switching LED7 ON.

. Responsiveness: Despite the dynamic change, the model maintains high accuracy (100% confidence).

. Stability: During extended operation (24,793 total packets), the system processed 1077 valid signals at 7.3 ms inference time.

. Accuracy: The session recorded 1064 Non-Human and 13 Uncertain classifications. Crucially, zero Human false positives were generated during the active trigger event.

![gui002](https://github.com/user-attachments/assets/f28d5533-f238-441f-b03c-9db4c79f9dab)

In this event, the system detects a HUMAN with 100% confidence. The subject's entry caused a sudden distance shift exceeding the 10 cm threshold, instantly triggering the Active status (Count: 33) and turning LED7 ON and continuous CNN Checking.

the sequence of events: the system initially tracked a static environment (non-human data). When a person suddenly entered the sensor's range, the significant distance change triggered the "Activity" state. Simultaneously, the CNN accurately classified the signal as "Human," which caused the LED7 to remain continuously ON.

![gui003](https://github.com/user-attachments/assets/94cc9195-e90e-41e3-89e7-ad4cd2617139)

LED7 (yellow light) turns on when HUMAN is detected

<img width="1315" height="869" alt="image" src="https://github.com/user-attachments/assets/0e068fd1-d075-4b6a-80b9-50541e9f07f8" />

## Model Evaluation & Performance
The SpectrogramCNN was trained on a randomized 80/20 split (149,200 Train / 37,300 Val) over 15 epochs (~76 mins). The model achieved optimal convergence at Epoch 14 with a validation accuracy of 99.53% and a minimal loss of 0.0104, utilizing a weighted loss function to effectively mitigate class imbalance.

Classification Metrics Evaluation on the validation set (N=37,300) demonstrated exceptional discrimination with a Precision of 99.79% and Recall of 99.31% for the Human class.
High-confidence predictions (>95% score) accounted for 98.47% of all samples, achieving 99.96% accuracy within this subset.

<img width="1350" height="1182" alt="confusion_matrix_simple" src="https://github.com/user-attachments/assets/f6b0af4b-c211-4463-a07b-028fd7d37776" />


True Positives: 19,647 (Human correctly identified)

True Negatives: 17,476 (Non-Human correctly rejected)

False Positives: 41 (Low error rate indicating high reliability)

False Negatives: 136

Real-Time Validation Field trials confirmed the system's robustness across 6 distinct subjects (4 unknown, 2 known). The model consistently activated the LED for human presence while correctly classifying moving inanimate objects (e.g., chairs) as Non-Human, effectively filtering out false positives in dynamic environments.

```
   NR.  	Data type Actual	  Classified as Human	   Classified as Non-Human
   1	          Floor              	No	                      Yes
   2	          Human1	            Yes	                     No
   3	          Chair	              No                      Yes
   4	          Human 2	            Yes                      No
   5	          Human 3	            Yes	                     No
   6	          Human 4	            Yes                     	No
   7	          Table	              No                     	 Yes
   8	          Human 5	            Yes	                     No
   9	          Human 6	            Yes                     	No
```
## Real-time usage of The Project
This project focuses on generating optimized weights for a Convolutional Neural Network (CNN) to enable a SONAR sensor array to detect human presence within office environments. By utilizing annotated time-frequency data, the system achieves high-accuracy classification to distinguish between humans and non-human objects. In real-time operation, the detection logic interfaces directly with the Red Pitaya’s internal C code to trigger automated lighting systems immediately upon confirming a person's presence.
