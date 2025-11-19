"""
Task Logger - Sistema de logs estruturado para tarefas
"""

from typing import Optional
from datetime import datetime
from pathlib import Path
import json

class TaskLogger:
    """Logger estruturado para tarefas do Executor"""

    def __init__(self, task_id: str, storage_path: Optional[str] = None):
        self.task_id = task_id

        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = Path(__file__).parent.parent.parent / 'data' / 'executor' / 'logs'

        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.log_file = self.storage_path / f'{task_id}.log'
        self.logs = []

    def log(self, message: str, level: str = 'info', **kwargs):
        """
        Adiciona um log

        Args:
            message: Mensagem do log
            level: Nível (info, warning, error, success)
            **kwargs: Dados adicionais
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            **kwargs
        }

        self.logs.append(log_entry)

        # Escrever no arquivo
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    def info(self, message: str, **kwargs):
        """Log de informação"""
        self.log(message, 'info', **kwargs)

    def warning(self, message: str, **kwargs):
        """Log de aviso"""
        self.log(message, 'warning', **kwargs)

    def error(self, message: str, **kwargs):
        """Log de erro"""
        self.log(message, 'error', **kwargs)

    def success(self, message: str, **kwargs):
        """Log de sucesso"""
        self.log(message, 'success', **kwargs)

    def get_logs(self) -> list:
        """Retorna todos os logs"""
        return self.logs

    def get_logs_by_level(self, level: str) -> list:
        """Retorna logs de um nível específico"""
        return [log for log in self.logs if log['level'] == level]
