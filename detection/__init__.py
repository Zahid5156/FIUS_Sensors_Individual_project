"""
Detection package for human detection logic
"""

from .detector import HumanDetector
from .worker import DetectionWorker, DetectionWorkerSignals

__all__ = ['HumanDetector', 'DetectionWorker', 'DetectionWorkerSignals']