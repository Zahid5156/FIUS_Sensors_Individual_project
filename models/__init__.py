"""
Models package for CNN architectures
"""

from .cnn_model import SpectrogramCNN, get_device

__all__ = ['SpectrogramCNN', 'get_device']