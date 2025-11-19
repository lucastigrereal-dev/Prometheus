"""
Prometheus Supervisor Avançado
Sistema de supervisão e proteção de integridade
"""

from .change_diff_analyzer import ChangeDiffAnalyzer, DiffResult
from .file_mutation_checker import FileMutationChecker, MutationEvent
from .code_boundary_protector import CodeBoundaryProtector, BoundaryViolation
from .config_watcher import ConfigWatcher, ConfigChange

__version__ = "3.5.0"

__all__ = [
    "ChangeDiffAnalyzer",
    "DiffResult",
    "FileMutationChecker",
    "MutationEvent",
    "CodeBoundaryProtector",
    "BoundaryViolation",
    "ConfigWatcher",
    "ConfigChange",
]
