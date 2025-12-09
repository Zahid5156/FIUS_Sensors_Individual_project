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

  ## Graphical User Interface (GUI):
This is the visual representation of the GUI when the model starts: To initiate the system, click the "Start Sensor Detetction" button. This establishes an SSH connection, executes the dma_with_udp_faster.c acquisition code on the Red Pitaya, and confirms the link via a UDP handshake. Once connected, the system immediately begins the analysis pipeline, continuously processing data at a rate of two signals per second.
The interface features large visual indicators—HUMAN (blinks green) and NON-HUMAN (blinks red)—alongside real-time metrics for object distance, model confidence, and LED7 status. Movement is tracked via an "Activity" label (IDLE/ACTIVE) based on a user-adjustable Distance Threshold (default: 10 cm). Comprehensive telemetry displays connection status, detection counters, inference time, and signal loss warnings at the bottom of the window, with the entire session controlled via the main Start/Stop buttons.

![gui00](https://github.com/user-attachments/assets/0063d42d-e822-42f3-87f6-82c524af1537)



System Demonstration:

In this figure, the system monitors a static background (e.g., floor at 205 cm). Since distance fluctuations do not exceed the 10 cm threshold, the system remains in IDLE mode with LED7 OFF.

 .Classification: The model correctly identifies the environment as NON-HUMAN with 99.8% confidence.

. Performance: Processing remains stable at 1.82 signals/sec (6.8 ms inference time).

. Robustness: The filter successfully discards incomplete data (3,979 broken packets) while processing 189 valid signals (186 Non-Human, 3 Uncertain) with zero false positives.

![gui01](https://github.com/user-attachments/assets/dbc59766-226a-49ee-92ea-279396fb48fd)

In this scenario, a non-human object (chair) is detected at 156 cm. The sudden distance shift exceeds the threshold, triggering the Activity state (Count: 3) and instantly switching LED7 ON.

. Responsiveness: Despite the dynamic change, the model maintains high accuracy (99.0% confidence).

. Stability: During extended operation (23,337 total packets), the system processed 993 valid signals at 6.6 ms inference time.

. Accuracy: The session recorded 979 Non-Human and 14 Uncertain classifications. Crucially, zero Human false positives were generated during the active trigger event.


![gui1](https://github.com/user-attachments/assets/1a8b42bb-6521-4461-a9c6-16b4b3089f1a)

In this event, the system detects a HUMAN at 102 cm with 100% confidence. The subject's entry caused a sudden distance shift exceeding the 10 cm threshold, instantly triggering the Active status (Count: 24) and turning LED7 ON and continuous CNN Checking.

Dynamic Response: The metrics capture the real-time transition from a static background (38 Non-Human detections) to human presence (47 Human detections).

Performance: Despite receiving 2,257 broken packets, the pipeline successfully filtered and processed 112 valid signals at 1.23/sec with a 7.9 ms inference time.

Classification: The model demonstrated valid tracking with 27 "Uncertain" states buffering the transition between definitive Human and Non-Human classes.

![human01](https://github.com/user-attachments/assets/c877561d-e542-483c-8974-7ef6949b3859)

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
