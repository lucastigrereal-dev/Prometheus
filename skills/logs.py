"""
Prometheus - Logging Utility
Configuração centralizada de logging para todos os módulos
"""

import logging
import os
from datetime import datetime

def setup_logger(name: str, log_file: str = None, level: str = "INFO") -> logging.Logger:
    """
    Configura e retorna um logger padronizado

    Args:
        name: Nome do módulo/logger
        log_file: Caminho do arquivo de log (opcional)
        level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        logging.Logger configurado
    """
    logger = logging.getLogger(name)

    # Se já foi configurado, retorna
    if logger.handlers:
        return logger

    # Configurar nível
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Formato padronizado
    formatter = logging.Formatter(
        fmt='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Handler para console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Handler para arquivo (se especificado)
    if log_file:
        # Criar diretório de logs se não existir
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_function_call(logger: logging.Logger):
    """
    Decorator para logar chamadas de função

    Usage:
        @log_function_call(logger)
        def my_function():
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.debug(f"Chamando {func.__name__}(args={args}, kwargs={kwargs})")
            try:
                result = func(*args, **kwargs)
                logger.debug(f"{func.__name__} executado com sucesso")
                return result
            except Exception as e:
                logger.error(f"Erro em {func.__name__}: {e}", exc_info=True)
                raise
        return wrapper
    return decorator
