"""
PROMETHEUS V3 - CONFIGURATION MANAGER
Gerenciador centralizado de configuração com hot-reload e validação
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, Union
from dataclasses import dataclass
import logging
from datetime import datetime
import hashlib
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIG MANAGER
# ============================================================================

class ConfigManager:
    """
    Gerenciador centralizado de configuração
    - Carrega YAML
    - Substitui variáveis de ambiente
    - Valida schema
    - Hot reload
    - Cache
    """
    
    _instance = None
    _config = None
    _config_path = None
    _last_modified = None
    _hash = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        self.config_path = self._find_config_file()
        self.env_vars = os.environ.copy()
        self.observers = []
        self.hot_reload_enabled = False
        
    def _find_config_file(self) -> Path:
        """Encontra arquivo de configuração"""
        possible_paths = [
            Path("prometheus_unified_config.yaml"),
            Path("config/prometheus_unified_config.yaml"),
            Path("prometheus_v3/config/prometheus_unified_config.yaml"),
            Path("../config/prometheus_unified_config.yaml"),
        ]
        
        for path in possible_paths:
            if path.exists():
                logger.info(f"Config file found: {path}")
                return path
        
        raise FileNotFoundError("Configuration file not found!")
    
    def load(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Carrega configuração"""
        if config_path:
            self.config_path = Path(config_path)
        
        try:
            with open(self.config_path, 'r') as f:
                raw_config = yaml.safe_load(f)
            
            # Substitui variáveis de ambiente
            self._config = self._substitute_env_vars(raw_config)
            
            # Valida configuração
            self._validate_config(self._config)
            
            # Calcula hash
            self._hash = self._calculate_hash(self._config)
            
            # Atualiza timestamp
            self._last_modified = datetime.now()
            
            logger.info(f"Configuration loaded successfully from {self.config_path}")
            return self._config
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _substitute_env_vars(self, config: Any) -> Any:
        """Substitui ${VAR_NAME} por valores do ambiente"""
        if isinstance(config, dict):
            return {k: self._substitute_env_vars(v) for k, v in config.items()}
        elif isinstance(config, list):
            return [self._substitute_env_vars(item) for item in config]
        elif isinstance(config, str):
            # Procura por ${VAR_NAME}
            if config.startswith("${") and config.endswith("}"):
                var_name = config[2:-1]
                return os.getenv(var_name, config)
            return config
        else:
            return config
    
    def _validate_config(self, config: Dict[str, Any]):
        """Valida estrutura da configuração"""
        required_sections = ['system', 'providers', 'modules', 'runtime']
        
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required section: {section}")
        
        # Valida versão
        if 'version' not in config['system']:
            raise ValueError("System version not specified")
        
        # Valida pelo menos um provider habilitado
        providers_enabled = any(
            p.get('enabled', False) 
            for p in config['providers'].values()
        )
        if not providers_enabled:
            logger.warning("No AI providers enabled!")
    
    def _calculate_hash(self, config: Dict[str, Any]) -> str:
        """Calcula hash da configuração para detectar mudanças"""
        config_str = json.dumps(config, sort_keys=True)
        return hashlib.md5(config_str.encode()).hexdigest()
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Obtém valor da configuração usando dot notation
        Exemplo: config.get('providers.claude.api_key')
        """
        if not self._config:
            self.load()
        
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        
        return value
    
    def set(self, key_path: str, value: Any):
        """
        Define valor na configuração
        Exemplo: config.set('providers.claude.enabled', False)
        """
        if not self._config:
            self.load()
        
        keys = key_path.split('.')
        config = self._config
        
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        config[keys[-1]] = value
        
        # Recalcula hash
        self._hash = self._calculate_hash(self._config)
    
    def save(self, backup: bool = True):
        """Salva configuração atual no arquivo"""
        if backup:
            backup_path = self.config_path.with_suffix('.yaml.bak')
            if self.config_path.exists():
                import shutil
                shutil.copy2(self.config_path, backup_path)
        
        with open(self.config_path, 'w') as f:
            yaml.dump(self._config, f, default_flow_style=False, sort_keys=False)
        
        logger.info(f"Configuration saved to {self.config_path}")
    
    def reload(self):
        """Recarrega configuração do arquivo"""
        logger.info("Reloading configuration...")
        self.load()
        
        # Notifica observadores
        for callback in self.observers:
            callback(self._config)
    
    def enable_hot_reload(self):
        """Habilita hot reload da configuração"""
        if self.hot_reload_enabled:
            return
        
        class ConfigFileHandler(FileSystemEventHandler):
            def __init__(self, config_manager):
                self.config_manager = config_manager
            
            def on_modified(self, event):
                if event.src_path.endswith('.yaml'):
                    logger.info("Configuration file changed, reloading...")
                    self.config_manager.reload()
        
        event_handler = ConfigFileHandler(self)
        observer = Observer()
        observer.schedule(
            event_handler,
            path=str(self.config_path.parent),
            recursive=False
        )
        observer.start()
        
        self.hot_reload_enabled = True
        logger.info("Hot reload enabled for configuration")
    
    def register_observer(self, callback):
        """Registra callback para mudanças de configuração"""
        self.observers.append(callback)
    
    def get_all(self) -> Dict[str, Any]:
        """Retorna configuração completa"""
        if not self._config:
            self.load()
        return self._config.copy()
    
    def get_hash(self) -> str:
        """Retorna hash atual da configuração"""
        return self._hash
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da configuração"""
        return {
            'path': str(self.config_path),
            'last_modified': self._last_modified.isoformat() if self._last_modified else None,
            'hash': self._hash,
            'sections': list(self._config.keys()) if self._config else [],
            'hot_reload': self.hot_reload_enabled
        }

# ============================================================================
# ENVIRONMENT MANAGER
# ============================================================================

class EnvironmentManager:
    """Gerencia variáveis de ambiente"""
    
    @staticmethod
    def load_env_file(env_path: str = ".env"):
        """Carrega arquivo .env"""
        if not Path(env_path).exists():
            logger.warning(f"Environment file {env_path} not found")
            return
        
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
        
        logger.info(f"Environment variables loaded from {env_path}")
    
    @staticmethod
    def validate_required_vars(required: list):
        """Valida se variáveis necessárias estão definidas"""
        missing = []
        for var in required:
            if not os.getenv(var):
                missing.append(var)
        
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
    
    @staticmethod
    def get_all() -> Dict[str, str]:
        """Retorna todas as variáveis de ambiente"""
        return dict(os.environ)

# ============================================================================
# CONFIG SINGLETON
# ============================================================================

# Instância global
config = ConfigManager()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_config(key: str, default: Any = None) -> Any:
    """Helper function para acessar config globalmente"""
    return config.get(key, default)

def set_config(key: str, value: Any):
    """Helper function para setar config globalmente"""
    config.set(key, value)

def reload_config():
    """Helper function para recarregar config"""
    config.reload()

# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Carrega variáveis de ambiente
    EnvironmentManager.load_env_file()
    
    # Carrega configuração
    config_manager = ConfigManager()
    config_data = config_manager.load()
    
    # Exemplos de acesso
    print("\n=== Configuration Examples ===")
    print(f"System name: {config_manager.get('system.name')}")
    print(f"Version: {config_manager.get('system.version')}")
    print(f"Claude enabled: {config_manager.get('providers.claude.enabled')}")
    print(f"Max parallel tasks: {config_manager.get('runtime.max_parallel_tasks')}")
    
    # Estatísticas
    print("\n=== Configuration Stats ===")
    stats = config_manager.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    # Habilita hot reload
    config_manager.enable_hot_reload()
    print("\n✅ Hot reload enabled - try modifying the config file!")
    
    # Mantém rodando para testar hot reload
    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
