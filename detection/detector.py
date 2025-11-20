"""
Human detector using CNN for spectrogram classification
"""

from pathlib import Path

try:
    import torch
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    print("ERROR: PyTorch not installed!")

from models.cnn_model import SpectrogramCNN, get_device
from utils.signal_processing import signal_to_spectrogram
from config import (
    FS, NPERSEG, NOVERLAP, WINDOW, MODE
)


class HumanDetector:
    """Real-time human detection from spectrogram"""
    
    def __init__(self, model_path, device='auto', confidence_threshold=0.85):
        if not PYTORCH_AVAILABLE:
            raise ImportError("PyTorch is not installed!")
        
        # Device selection
        self.device = get_device(device)
        
        # Load model
        checkpoint = torch.load(model_path, map_location=self.device)
        self.model = SpectrogramCNN(num_classes=2)
        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.model.to(self.device)
        self.model.eval()
        
        self.confidence_threshold = confidence_threshold
        self.model_metadata = {
            'val_accuracy': checkpoint.get('val_acc', 'N/A'),
            'val_loss': checkpoint.get('val_loss', 'N/A'),
            'epoch': checkpoint.get('epoch', 'N/A')
        }
        
        # Spectrogram parameters
        self.fs = FS
        self.nperseg = NPERSEG
        self.noverlap = NOVERLAP
        self.window = WINDOW
        self.mode = MODE
        
        print(f"Model loaded: {Path(model_path).name}")
        print(f"Validation accuracy: {self.model_metadata['val_accuracy']}")
        print(f"Confidence threshold: {confidence_threshold*100:.0f}%")
    
    def signal_to_spectrogram(self, signal):
        """Convert raw signal to spectrogram tensor"""
        return signal_to_spectrogram(
            signal,
            self.fs,
            self.nperseg,
            self.noverlap,
            self.window,
            self.mode,
            self.device
        )
    
    def predict(self, signal):
        """Predict human presence from raw signal"""
        spec, freqs, times = self.signal_to_spectrogram(signal)
        
        with torch.no_grad():
            output = self.model(spec)
            probs = torch.softmax(output, dim=1)
            confidence, predicted = torch.max(probs, 1)
        
        pred = predicted.item()
        conf = confidence.item()
        probs_np = probs.cpu().numpy()[0]
        
        if conf >= self.confidence_threshold:
            class_name = "HUMAN" if pred == 1 else "NON-HUMAN"
            return pred, conf, class_name, probs_np
        else:
            return None, conf, "UNCERTAIN", probs_np
    
    def get_model_info(self):
        return self.model_metadata