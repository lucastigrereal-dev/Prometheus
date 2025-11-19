"""
Structured Logger - Sistema de logging estruturado com contexto rico
PRINCÍPIOS:
- Logs sempre com contexto (timestamp, module, task_id, user_id)
- Níveis apropriados (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Formato JSON para análise
- Rotação automática de arquivos
"""

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from logging.handlers import RotatingFileHandler
import traceback

class StructuredLogger:
    """Logger estruturado com contexto rico"""

    def __init__(
        self,
        name: str,
        log_dir: str = "logs",
        level: str = "INFO",
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        """
        Inicializa o logger estruturado

        Args:
            name: Nome do logger (módulo)
            log_dir: Diretório para logs
            level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            max_bytes: Tamanho máximo do arquivo de log
            backup_count: Número de backups a manter
        """
        self.name = name
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Criar logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.upper()))

        # Evitar duplicação de handlers
        if not self.logger.handlers:
            # Handler para arquivo (JSON estruturado)
            log_file = self.log_dir / f"{name}.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(logging.Formatter('%(message)s'))
            self.logger.addHandler(file_handler)

            # Handler para console (formato legível)
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

        self.context = {}  # Contexto global

    def set_context(self, **kwargs):
        """
        Define contexto global para todos os logs

        Args:
            **kwargs: Pares chave-valor para adicionar ao contexto
        """
        self.context.update(kwargs)

    def clear_context(self):
        """Limpa o contexto global"""
        self.context = {}

    def _build_log_entry(
        self,
        level: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None
    ) -> Dict[str, Any]:
        """Constrói entrada de log estruturada"""

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'logger': self.name,
            'message': message,
            **self.context  # Adiciona contexto global
        }

        # Adiciona contexto extra
        if extra:
            log_entry.update(extra)

        # Adiciona informações de exceção
        if exc_info:
            log_entry['exception'] = {
                'type': type(exc_info).__name__,
                'message': str(exc_info),
                'traceback': traceback.format_exc()
            }

        return log_entry

    def _log(
        self,
        level: str,
        message: str,
        extra: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None
    ):
        """Log interno estruturado"""

        log_entry = self._build_log_entry(level, message, extra, exc_info)

        # Log em JSON para arquivo
        json_log = json.dumps(log_entry, ensure_ascii=False)

        # Log no nível apropriado
        log_method = getattr(self.logger, level.lower())
        log_method(json_log, extra={'structured': True})

        # Log em formato legível para console se houver exceção
        if exc_info and level in ['ERROR', 'CRITICAL']:
            self.logger.error(f"Exception details: {traceback.format_exc()}")

    def debug(self, message: str, **kwargs):
        """Log nível DEBUG"""
        self._log('DEBUG', message, extra=kwargs)

    def info(self, message: str, **kwargs):
        """Log nível INFO"""
        self._log('INFO', message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """Log nível WARNING"""
        self._log('WARNING', message, extra=kwargs)

    def error(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        """Log nível ERROR"""
        self._log('ERROR', message, extra=kwargs, exc_info=exc_info)

    def critical(self, message: str, exc_info: Optional[Exception] = None, **kwargs):
        """Log nível CRITICAL"""
        self._log('CRITICAL', message, extra=kwargs, exc_info=exc_info)

    def task_start(self, task_id: str, task_type: str, **kwargs):
        """Log início de tarefa"""
        self.info(
            "Task started",
            task_id=task_id,
            task_type=task_type,
            event="task_start",
            **kwargs
        )

    def task_complete(self, task_id: str, duration_seconds: float, **kwargs):
        """Log conclusão de tarefa"""
        self.info(
            "Task completed",
            task_id=task_id,
            duration_seconds=duration_seconds,
            event="task_complete",
            **kwargs
        )

    def task_failed(self, task_id: str, error: str, exc_info: Optional[Exception] = None, **kwargs):
        """Log falha de tarefa"""
        self.error(
            "Task failed",
            task_id=task_id,
            error=error,
            event="task_failed",
            exc_info=exc_info,
            **kwargs
        )

    def api_request(self, method: str, endpoint: str, status_code: int, duration_ms: float, **kwargs):
        """Log requisição API"""
        self.info(
            "API request",
            event="api_request",
            http_method=method,
            endpoint=endpoint,
            status_code=status_code,
            duration_ms=duration_ms,
            **kwargs
        )

    def ai_call(self, provider: str, model: str, tokens: int, duration_seconds: float, **kwargs):
        """Log chamada de IA"""
        self.info(
            "AI call",
            event="ai_call",
            provider=provider,
            model=model,
            tokens=tokens,
            duration_seconds=duration_seconds,
            **kwargs
        )

    def browser_action(self, action: str, url: str, success: bool, **kwargs):
        """Log ação do browser"""
        self.info(
            "Browser action",
            event="browser_action",
            action=action,
            url=url,
            success=success,
            **kwargs
        )

    def memory_operation(self, operation: str, collection: str, duration_ms: float, **kwargs):
        """Log operação de memória"""
        self.info(
            "Memory operation",
            event="memory_operation",
            operation=operation,
            collection=collection,
            duration_ms=duration_ms,
            **kwargs
        )


# Singleton global para facilitar uso
_loggers: Dict[str, StructuredLogger] = {}

def get_logger(name: str, **kwargs) -> StructuredLogger:
    """
    Obtém ou cria um logger estruturado

    Args:
        name: Nome do logger
        **kwargs: Argumentos adicionais para StructuredLogger

    Returns:
        StructuredLogger instance
    """
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name, **kwargs)
    return _loggers[name]
