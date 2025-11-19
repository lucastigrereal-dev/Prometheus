"""
Prometheus Safe-Write Engine
Sistema de escrita segura com verificação e rollback
"""

from .safe_write import SafeWriter, WriteOperation, WriteResult, WriteMode
from .safe_write_logger import SafeWriteLogger

__version__ = "3.5.0"

__all__ = [
    "SafeWriter",
    "WriteOperation",
    "WriteResult",
    "WriteMode",
    "SafeWriteLogger",
]
