"""
File Index Manager
Gerencia índice JSON de arquivos monitorados pelo Prometheus
"""

import json
from pathlib import Path
from typing import Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger("prometheus.file_index")


@dataclass
class FileRecord:
    """
    Registro de arquivo no índice de integridade
    """
    path: str
    hash: str
    size_bytes: int
    modified_at: str
    indexed_at: str
    status: str = "valid"  # valid, modified, deleted, corrupted
    category: str = "unknown"  # code, config, data, log
    protected: bool = False
    last_verified: Optional[str] = None
    backup_path: Optional[str] = None
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class FileIndex:
    """
    Gerenciador do índice de integridade de arquivos
    Armazena estado de todos os arquivos monitorados
    """

    def __init__(self, index_path: str | Path = "runtime/file_index.json"):
        self.index_path = Path(index_path)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        self.records: dict[str, FileRecord] = {}
        self.load()

    def load(self) -> bool:
        """
        Carrega índice do disco

        Returns:
            True se carregado com sucesso
        """
        try:
            if not self.index_path.exists():
                logger.info(f"Criando novo índice em {self.index_path}")
                self.records = {}
                self.save()
                return True

            with open(self.index_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            self.records = {}
            for path, record_data in data.get("files", {}).items():
                self.records[path] = FileRecord(**record_data)

            logger.info(f"Índice carregado: {len(self.records)} arquivos")
            return True

        except Exception as e:
            logger.error(f"Erro ao carregar índice: {e}")
            self.records = {}
            return False

    def save(self) -> bool:
        """
        Salva índice no disco

        Returns:
            True se salvo com sucesso
        """
        try:
            data = {
                "version": "3.5.0",
                "last_updated": datetime.now().isoformat(),
                "total_files": len(self.records),
                "files": {
                    path: asdict(record)
                    for path, record in self.records.items()
                }
            }

            # Backup do índice anterior
            if self.index_path.exists():
                backup_path = self.index_path.with_suffix('.json.bak')
                self.index_path.rename(backup_path)

            with open(self.index_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.info(f"Índice salvo: {len(self.records)} arquivos")
            return True

        except Exception as e:
            logger.error(f"Erro ao salvar índice: {e}")
            return False

    def add_file(self, record: FileRecord) -> bool:
        """
        Adiciona arquivo ao índice

        Args:
            record: FileRecord com dados do arquivo

        Returns:
            True se adicionado com sucesso
        """
        try:
            self.records[record.path] = record
            logger.info(f"Arquivo indexado: {record.path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao adicionar arquivo: {e}")
            return False

    def update_file(self, path: str, **kwargs) -> bool:
        """
        Atualiza registro de arquivo

        Args:
            path: Caminho do arquivo
            **kwargs: Campos a atualizar

        Returns:
            True se atualizado com sucesso
        """
        if path not in self.records:
            logger.warning(f"Arquivo não encontrado no índice: {path}")
            return False

        try:
            record = self.records[path]
            for key, value in kwargs.items():
                if hasattr(record, key):
                    setattr(record, key, value)

            logger.info(f"Arquivo atualizado: {path}")
            return True

        except Exception as e:
            logger.error(f"Erro ao atualizar arquivo: {e}")
            return False

    def get_file(self, path: str) -> Optional[FileRecord]:
        """
        Busca registro de arquivo

        Args:
            path: Caminho do arquivo

        Returns:
            FileRecord ou None
        """
        return self.records.get(path)

    def remove_file(self, path: str) -> bool:
        """
        Remove arquivo do índice

        Args:
            path: Caminho do arquivo

        Returns:
            True se removido com sucesso
        """
        if path in self.records:
            del self.records[path]
            logger.info(f"Arquivo removido do índice: {path}")
            return True
        return False

    def list_files(
        self,
        status: Optional[str] = None,
        category: Optional[str] = None,
        protected: Optional[bool] = None
    ) -> list[FileRecord]:
        """
        Lista arquivos com filtros opcionais

        Args:
            status: Filtrar por status
            category: Filtrar por categoria
            protected: Filtrar por proteção

        Returns:
            Lista de FileRecord
        """
        results = list(self.records.values())

        if status:
            results = [r for r in results if r.status == status]

        if category:
            results = [r for r in results if r.category == category]

        if protected is not None:
            results = [r for r in results if r.protected == protected]

        return results

    def get_stats(self) -> dict[str, Any]:
        """
        Estatísticas do índice

        Returns:
            Dict com estatísticas
        """
        records = list(self.records.values())

        return {
            "total_files": len(records),
            "by_status": {
                "valid": len([r for r in records if r.status == "valid"]),
                "modified": len([r for r in records if r.status == "modified"]),
                "deleted": len([r for r in records if r.status == "deleted"]),
                "corrupted": len([r for r in records if r.status == "corrupted"])
            },
            "by_category": {
                "code": len([r for r in records if r.category == "code"]),
                "config": len([r for r in records if r.category == "config"]),
                "data": len([r for r in records if r.category == "data"]),
                "log": len([r for r in records if r.category == "log"]),
                "unknown": len([r for r in records if r.category == "unknown"])
            },
            "protected_files": len([r for r in records if r.protected]),
            "total_size_bytes": sum(r.size_bytes for r in records)
        }

    def mark_as_modified(self, path: str, new_hash: str) -> bool:
        """
        Marca arquivo como modificado

        Args:
            path: Caminho do arquivo
            new_hash: Novo hash detectado

        Returns:
            True se marcado com sucesso
        """
        return self.update_file(
            path,
            status="modified",
            hash=new_hash,
            last_verified=datetime.now().isoformat()
        )

    def mark_as_valid(self, path: str) -> bool:
        """
        Marca arquivo como válido

        Args:
            path: Caminho do arquivo

        Returns:
            True se marcado com sucesso
        """
        return self.update_file(
            path,
            status="valid",
            last_verified=datetime.now().isoformat()
        )
