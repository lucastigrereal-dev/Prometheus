"""
PROMETHEUS V3 - UNIFIED LOGGING SYSTEM
Sistema de logging profissional com correlation IDs e formatação consistente
"""

import logging
import logging.handlers
import json
import sys
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from contextvars import ContextVar
import traceback

# Context variable para correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)

# ============================================================================
# CUSTOM FORMATTERS
# ============================================================================

class ColoredFormatter(logging.Formatter):
    """Formatter com cores para console"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    
    RESET = '\033[0m'
    
    def format(self, record):
        # Adiciona correlation ID se disponível
        correlation_id = correlation_id_var.get()
        if correlation_id:
            record.correlation_id = f"[{correlation_id}]"
        else:
            record.correlation_id = ""
        
        # Adiciona cor
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"
        
        # Formata mensagem
        formatted = super().format(record)
        
        # Adiciona emoji baseado no nível
        emojis = {
            'DEBUG': '🔍',
            'INFO': '✅',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'CRITICAL': '🔥'
        }
        
        for level, emoji in emojis.items():
            if level in formatted:
                formatted = f"{emoji} {formatted}"
                break
        
        return formatted

class JSONFormatter(logging.Formatter):
    """Formatter JSON para logs estruturados"""
    
    def format(self, record):
        log_obj = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'correlation_id': correlation_id_var.get(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Adiciona exception info se existir
        if record.exc_info:
            log_obj['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
        
        # Adiciona campos extras
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 
                          'funcName', 'levelname', 'levelno', 'lineno', 
                          'module', 'msecs', 'message', 'pathname', 'process',
                          'processName', 'relativeCreated', 'thread', 'threadName',
                          'exc_info', 'exc_text', 'stack_info']:
                log_obj[key] = value
        
        return json.dumps(log_obj)

# ============================================================================
# LOG MANAGER
# ============================================================================

class LogManager:
    """Gerenciador central de logging"""
    
    _instance = None
    _loggers = {}
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LogManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.setup_logging()
            self._initialized = True
    
    def setup_logging(self, config: Optional[Dict[str, Any]] = None):
        """Configura sistema de logging"""
        
        # Config padrão
        if not config:
            config = {
                'level': 'INFO',
                'console': True,
                'file': True,
                'json': False,
                'log_dir': 'logs',
                'max_size': 100 * 1024 * 1024,  # 100MB
                'backup_count': 5
            }
        
        # Cria diretório de logs
        log_dir = Path(config['log_dir'])
        log_dir.mkdir(exist_ok=True, parents=True)
        
        # Root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(config['level'])
        
        # Remove handlers existentes
        root_logger.handlers = []
        
        # Console handler
        if config.get('console', True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_formatter = ColoredFormatter(
                '[%(asctime)s] [%(levelname)s] [%(name)s] %(correlation_id)s → %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            console_handler.setLevel(config['level'])
            root_logger.addHandler(console_handler)
        
        # File handler com rotação
        if config.get('file', True):
            file_handler = logging.handlers.RotatingFileHandler(
                log_dir / 'prometheus.log',
                maxBytes=config.get('max_size', 100 * 1024 * 1024),
                backupCount=config.get('backup_count', 5)
            )
            file_formatter = logging.Formatter(
                '[%(asctime)s] [%(levelname)s] [%(name)s] [%(correlation_id)s] → %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(logging.DEBUG)  # File sempre em DEBUG
            root_logger.addHandler(file_handler)
        
        # JSON file handler para logs estruturados
        if config.get('json', False):
            json_handler = logging.handlers.RotatingFileHandler(
                log_dir / 'prometheus.json',
                maxBytes=config.get('max_size', 100 * 1024 * 1024),
                backupCount=config.get('backup_count', 5)
            )
            json_formatter = JSONFormatter()
            json_handler.setFormatter(json_formatter)
            json_handler.setLevel(logging.DEBUG)
            root_logger.addHandler(json_handler)
        
        # Error file handler (apenas erros)
        error_handler = logging.handlers.RotatingFileHandler(
            log_dir / 'errors.log',
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=3
        )
        error_formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] [%(name)s] → %(message)s\n%(exc_info)s'
        )
        error_handler.setFormatter(error_formatter)
        error_handler.setLevel(logging.ERROR)
        root_logger.addHandler(error_handler)
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Obtém logger para módulo específico"""
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            cls._loggers[name] = logger
        return cls._loggers[name]
    
    @staticmethod
    def set_correlation_id(correlation_id: Optional[str] = None):
        """Define correlation ID para rastreamento"""
        if correlation_id is None:
            correlation_id = str(uuid.uuid4())[:8]
        correlation_id_var.set(correlation_id)
        return correlation_id
    
    @staticmethod
    def get_correlation_id() -> Optional[str]:
        """Obtém correlation ID atual"""
        return correlation_id_var.get()
    
    @staticmethod
    def clear_correlation_id():
        """Limpa correlation ID"""
        correlation_id_var.set(None)

# ============================================================================
# DECORATORS
# ============================================================================

def log_execution(level=logging.INFO):
    """Decorator para logar execução de funções"""
    def decorator(func):
        logger = LogManager.get_logger(func.__module__)
        
        def wrapper(*args, **kwargs):
            start_time = time.time()
            correlation_id = LogManager.set_correlation_id()
            
            logger.log(level, f"Starting {func.__name__}")
            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.log(level, f"Completed {func.__name__} in {elapsed:.2f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"Failed {func.__name__} after {elapsed:.2f}s: {e}", exc_info=True)
                raise
            finally:
                LogManager.clear_correlation_id()
        
        return wrapper
    return decorator

def log_async_execution(level=logging.INFO):
    """Decorator para logar execução de funções assíncronas"""
    def decorator(func):
        logger = LogManager.get_logger(func.__module__)
        
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            correlation_id = LogManager.set_correlation_id()
            
            logger.log(level, f"Starting {func.__name__}")
            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.log(level, f"Completed {func.__name__} in {elapsed:.2f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"Failed {func.__name__} after {elapsed:.2f}s: {e}", exc_info=True)
                raise
            finally:
                LogManager.clear_correlation_id()
        
        return wrapper
    return decorator

# ============================================================================
# LOG VIEWER
# ============================================================================

class LogViewer:
    """Visualizador de logs em tempo real"""
    
    @staticmethod
    def tail(log_file: str = "logs/prometheus.log", lines: int = 50):
        """Mostra últimas linhas do log"""
        log_path = Path(log_file)
        if not log_path.exists():
            print(f"Log file {log_file} not found")
            return
        
        with open(log_path, 'r') as f:
            # Lê últimas N linhas
            all_lines = f.readlines()
            last_lines = all_lines[-lines:]
            
            for line in last_lines:
                print(line.rstrip())
    
    @staticmethod
    def follow(log_file: str = "logs/prometheus.log"):
        """Segue log em tempo real (como tail -f)"""
        import time
        
        log_path = Path(log_file)
        if not log_path.exists():
            print(f"Log file {log_file} not found")
            return
        
        with open(log_path, 'r') as f:
            # Vai para o final do arquivo
            f.seek(0, 2)
            
            try:
                while True:
                    line = f.readline()
                    if line:
                        print(line.rstrip())
                    else:
                        time.sleep(0.1)
            except KeyboardInterrupt:
                print("\n👋 Stopped following log")
    
    @staticmethod
    def grep(pattern: str, log_file: str = "logs/prometheus.log"):
        """Busca padrão no log"""
        import re
        
        log_path = Path(log_file)
        if not log_path.exists():
            print(f"Log file {log_file} not found")
            return
        
        regex = re.compile(pattern, re.IGNORECASE)
        
        with open(log_path, 'r') as f:
            for line in f:
                if regex.search(line):
                    print(line.rstrip())
    
    @staticmethod
    def stats(log_file: str = "logs/prometheus.log"):
        """Mostra estatísticas do log"""
        log_path = Path(log_file)
        if not log_path.exists():
            print(f"Log file {log_file} not found")
            return
        
        stats = {
            'DEBUG': 0,
            'INFO': 0,
            'WARNING': 0,
            'ERROR': 0,
            'CRITICAL': 0,
            'total': 0
        }
        
        with open(log_path, 'r') as f:
            for line in f:
                stats['total'] += 1
                for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
                    if f'[{level}]' in line:
                        stats[level] += 1
                        break
        
        print("=== Log Statistics ===")
        for level, count in stats.items():
            if level != 'total':
                percentage = (count / stats['total'] * 100) if stats['total'] > 0 else 0
                print(f"{level:8}: {count:6} ({percentage:.1f}%)")
        print(f"{'TOTAL':8}: {stats['total']:6}")

# ============================================================================
# INICIALIZAÇÃO GLOBAL
# ============================================================================

# Cria instância global
log_manager = LogManager()

# Helper function global
def get_logger(name: str) -> logging.Logger:
    """Helper para obter logger"""
    return LogManager.get_logger(name)

# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Configura logging
    log_manager.setup_logging({
        'level': 'DEBUG',
        'console': True,
        'file': True,
        'json': True
    })
    
    # Obtém logger
    logger = get_logger(__name__)
    
    # Exemplos de log
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
    
    # Com correlation ID
    LogManager.set_correlation_id("req-123")
    logger.info("Processing request")
    logger.info("Request completed")
    LogManager.clear_correlation_id()
    
    # Teste de exception
    try:
        1 / 0
    except Exception as e:
        logger.error("Division error occurred", exc_info=True)
    
    # Mostra estatísticas
    print("\n")
    LogViewer.stats()
