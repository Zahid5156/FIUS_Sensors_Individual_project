"""
CNN Model Architecture for Spectrogram Classification
"""

try:
    import torch
    import torch.nn as nn
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    print("ERROR: PyTorch not installed!")


class SpectrogramCNN(nn.Module):
    """CNN for spectrogram classification"""
    
    def __init__(self, num_classes=2, dropout_rate=0.5):
        super(SpectrogramCNN, self).__init__()
        
        self.conv_block1 = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Dropout2d(0.25)
        )
        
        self.conv_block2 = nn.Sequential(
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Dropout2d(0.25)
        )
        
        self.conv_block3 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),
            nn.Dropout2d(0.25)
        )
        
        self.conv_block4 = nn.Sequential(
            nn.Conv2d(128, 256, kernel_size=3, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d((4, 1)),
            nn.Dropout2d(0.25)
        )
        
        self.fc_layers = nn.Sequential(
            nn.Flatten(),
            nn.Linear(256 * 4 * 1, 512),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(512, 128),
            nn.ReLU(),
            nn.Dropout(dropout_rate),
            nn.Linear(128, num_classes)
        )
        
    def forward(self, x):
        x = self.conv_block1(x)
        x = self.conv_block2(x)
        x = self.conv_block3(x)
        x = self.conv_block4(x)
        x = self.fc_layers(x)
        return x


def get_device(preferred_device='auto'):
    """
    Get the best available device for PyTorch
    
    Args:
        preferred_device: 'auto', 'mps', 'cuda', or 'cpu'
    
    Returns:
        torch.device
    """
    if not PYTORCH_AVAILABLE:
        raise ImportError("PyTorch is not installed!")
    
    if preferred_device == 'auto':
        if torch.backends.mps.is_available():
            device = torch.device('mps')
            print("Using MPS (Apple Silicon GPU)")
        elif torch.cuda.is_available():
            device = torch.device('cuda')
            print("Using CUDA GPU")
        else:
            device = torch.device('cpu')
            print("Using CPU")
    else:
        if preferred_device == 'mps' and torch.backends.mps.is_available():
            device = torch.device('mps')
            print("Using MPS (Apple Silicon GPU)")
        elif preferred_device == 'cuda' and torch.cuda.is_available():
            device = torch.device('cuda')
            print("Using CUDA GPU")
        else:
            device = torch.device('cpu')
            print("Using CPU")
    
    return device