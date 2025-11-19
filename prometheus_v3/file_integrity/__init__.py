"""
Prometheus File Integrity System
Sistema imunológico de integridade de arquivos
"""

from .file_hash import FileHasher
from .file_index import FileIndex
from .file_integrity_service import FileIntegrityService
from .file_audit import FileAudit
from .integrity_daemon import IntegrityDaemon

__version__ = "3.5.0"

__all__ = [
    "FileHasher",
    "FileIndex",
    "FileIntegrityService",
    "FileAudit",
    "IntegrityDaemon",
]
