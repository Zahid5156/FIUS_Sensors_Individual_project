"""
Signal processing utilities for spectrogram generation
"""

import numpy as np

try:
    import torch
    from scipy.signal import spectrogram
    PROCESSING_AVAILABLE = True
except ImportError:
    PROCESSING_AVAILABLE = False
    print("ERROR: Required signal processing libraries not installed!")


def signal_to_spectrogram(signal, fs, nperseg, noverlap, window, mode, device):
    """
    Convert raw signal to spectrogram tensor
    
    Args:
        signal: Raw signal data (numpy array)
        fs: Sampling frequency
        nperseg: Segment length for FFT
        noverlap: Overlap between segments
        window: Window type
        mode: Spectrogram mode
        device: PyTorch device
    
    Returns:
        tuple: (spectrogram_tensor, frequencies, times)
    """
    if not PROCESSING_AVAILABLE:
        raise ImportError("Signal processing libraries not available!")
    
    freqs, times, S = spectrogram(
        signal,
        fs=fs,
        window=window,
        nperseg=nperseg,
        noverlap=noverlap,
        mode=mode
    )
    
    # Convert to tensor
    S = S.astype(np.float32)
    S = np.expand_dims(np.expand_dims(S, 0), 0)
    S = torch.from_numpy(S).to(device)
    
    return S, freqs, times


def correct_distance_measurement(dmax_raw):
    """
    Correct distance measurement from RedPitaya
    
    If dmax < 10, it's in meters; convert to cm
    
    Args:
        dmax_raw: Raw distance value
    
    Returns:
        int: Distance in cm
    """
    if dmax_raw < 10:
        return int(dmax_raw * 100)
    else:
        return int(dmax_raw)