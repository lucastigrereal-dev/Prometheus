"""
Config Watcher
Monitor de alterações em arquivos de configuração
"""

import json
import yaml
from pathlib import Path
from typing import Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger("prometheus.config_watcher")


@dataclass
class ConfigChange:
    """
    Mudança em configuração
    """
    config_file: str
    change_type: str  # added, modified, removed
    key_path: str
    old_value: Any = None
    new_value: Any = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ConfigWatcher:
    """
    Monitor de arquivos de configuração

    Funcionalidades:
    - Validação de formato (JSON, YAML)
    - Detecção de mudanças em chaves
    - Comparação de valores
    - Histórico de alterações
    - Validação de consistência
    """

    def __init__(self, state_path: str | Path = "runtime/supervisor_state.json"):
        self.state_path = Path(state_path)
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.config_snapshots: dict[str, dict] = {}
        self.load_state()
        logger.info("ConfigWatcher inicializado")

    def load_state(self):
        """Carrega estado de snapshots salvos"""
        try:
            if self.state_path.exists():
                with open(self.state_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.config_snapshots = data.get("config_snapshots", {})
                logger.info(f"Estado carregado: {len(self.config_snapshots)} configs")
        except Exception as e:
            logger.error(f"Erro ao carregar estado: {e}")
            self.config_snapshots = {}

    def save_state(self):
        """Salva estado de snapshots"""
        try:
            data = {
                "last_updated": datetime.now().isoformat(),
                "config_snapshots": self.config_snapshots
            }

            with open(self.state_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info("Estado salvo")
        except Exception as e:
            logger.error(f"Erro ao salvar estado: {e}")

    def register_config(self, config_path: str | Path) -> bool:
        """
        Registra arquivo de configuração para monitoramento

        Args:
            config_path: Caminho do arquivo de config

        Returns:
            True se registrado com sucesso
        """
        try:
            path = Path(config_path)

            if not path.exists():
                logger.error(f"Config não encontrado: {config_path}")
                return False

            # Ler e parsear config
            config_data = self._load_config_file(path)

            if config_data is None:
                return False

            # Salvar snapshot
            self.config_snapshots[str(path)] = {
                "data": config_data,
                "registered_at": datetime.now().isoformat()
            }

            self.save_state()
            logger.info(f"Config registrado: {config_path}")
            return True

        except Exception as e:
            logger.error(f"Erro ao registrar config: {e}")
            return False

    def check_config_changes(self, config_path: str | Path) -> list[ConfigChange]:
        """
        Verifica mudanças em arquivo de configuração

        Args:
            config_path: Caminho do arquivo

        Returns:
            Lista de ConfigChange detectadas
        """
        path_str = str(config_path)

        if path_str not in self.config_snapshots:
            logger.warning(f"Config não registrado: {config_path}")
            return []

        try:
            path = Path(config_path)

            if not path.exists():
                return [ConfigChange(
                    config_file=path_str,
                    change_type="removed",
                    key_path="<entire_file>",
                    old_value=self.config_snapshots[path_str]["data"],
                    new_value=None
                )]

            # Carregar config atual
            current_data = self._load_config_file(path)

            if current_data is None:
                return []

            # Comparar com snapshot
            old_data = self.config_snapshots[path_str]["data"]
            changes = self._compare_configs(old_data, current_data, path_str)

            if changes:
                logger.info(f"{len(changes)} mudanças detectadas em {config_path}")

            return changes

        except Exception as e:
            logger.error(f"Erro ao verificar mudanças: {e}")
            return []

    def update_snapshot(self, config_path: str | Path) -> bool:
        """
        Atualiza snapshot de configuração

        Args:
            config_path: Caminho do arquivo

        Returns:
            True se atualizado com sucesso
        """
        return self.register_config(config_path)

    def validate_config_format(self, config_path: str | Path) -> tuple[bool, Optional[str]]:
        """
        Valida formato de arquivo de configuração

        Args:
            config_path: Caminho do arquivo

        Returns:
            Tupla (is_valid, error_message)
        """
        try:
            path = Path(config_path)

            if not path.exists():
                return False, "Arquivo não encontrado"

            data = self._load_config_file(path)

            if data is None:
                return False, "Erro ao fazer parse do arquivo"

            return True, None

        except Exception as e:
            return False, str(e)

    def _load_config_file(self, path: Path) -> Optional[dict]:
        """
        Carrega arquivo de configuração (JSON ou YAML)

        Args:
            path: Caminho do arquivo

        Returns:
            Dict com configuração ou None
        """
        try:
            content = path.read_text(encoding='utf-8')

            if path.suffix in ['.json']:
                return json.loads(content)
            elif path.suffix in ['.yaml', '.yml']:
                return yaml.safe_load(content)
            else:
                logger.warning(f"Formato não suportado: {path.suffix}")
                return None

        except Exception as e:
            logger.error(f"Erro ao carregar config: {e}")
            return None

    def _compare_configs(
        self,
        old_data: dict,
        new_data: dict,
        config_file: str,
        prefix: str = ""
    ) -> list[ConfigChange]:
        """
        Compara duas versões de configuração

        Args:
            old_data: Dados antigos
            new_data: Dados novos
            config_file: Path do arquivo
            prefix: Prefixo de caminho de chave

        Returns:
            Lista de ConfigChange
        """
        changes = []

        # Verificar chaves removidas e modificadas
        for key, old_value in old_data.items():
            key_path = f"{prefix}.{key}" if prefix else key

            if key not in new_data:
                # Chave removida
                changes.append(ConfigChange(
                    config_file=config_file,
                    change_type="removed",
                    key_path=key_path,
                    old_value=old_value,
                    new_value=None
                ))
            else:
                new_value = new_data[key]

                # Se ambos são dicts, comparar recursivamente
                if isinstance(old_value, dict) and isinstance(new_value, dict):
                    sub_changes = self._compare_configs(
                        old_value,
                        new_value,
                        config_file,
                        key_path
                    )
                    changes.extend(sub_changes)

                # Caso contrário, comparar valores
                elif old_value != new_value:
                    changes.append(ConfigChange(
                        config_file=config_file,
                        change_type="modified",
                        key_path=key_path,
                        old_value=old_value,
                        new_value=new_value
                    ))

        # Verificar chaves adicionadas
        for key, new_value in new_data.items():
            if key not in old_data:
                key_path = f"{prefix}.{key}" if prefix else key
                changes.append(ConfigChange(
                    config_file=config_file,
                    change_type="added",
                    key_path=key_path,
                    old_value=None,
                    new_value=new_value
                ))

        return changes

    def get_config_snapshot(self, config_path: str | Path) -> Optional[dict]:
        """
        Obtém snapshot de configuração

        Args:
            config_path: Caminho do arquivo

        Returns:
            Dict com snapshot ou None
        """
        path_str = str(config_path)

        if path_str in self.config_snapshots:
            return self.config_snapshots[path_str]["data"]

        return None
