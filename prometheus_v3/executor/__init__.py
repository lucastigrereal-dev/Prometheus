"""
Prometheus Executor Module
Responsável por executar ações no sistema local e browser de forma segura e auditada.
"""

from .executor_local import LocalExecutor
from .browser_executor import BrowserExecutor
from .task_logger import TaskLogger
from .task_manager import TaskManager

__all__ = ['LocalExecutor', 'BrowserExecutor', 'TaskLogger', 'TaskManager']
