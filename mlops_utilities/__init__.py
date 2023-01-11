"""
Python library provides implementation for a few high level operations
most commonly occuring in any MLOps workflows built in AWS
"""

from __future__ import annotations

# Set default logging handler to avoid "No handler found" warnings.
import logging
import typing
import warnings
from logging import NullHandler

logging.getLogger(__name__).addHandler(NullHandler())
