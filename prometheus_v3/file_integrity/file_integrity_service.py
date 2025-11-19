"""
File Integrity Service
Serviço principal de verificação de integridade de arquivos
"""

from pathlib import Path
from typing import Optional, Any
from datetime import datetime
import logging

from .file_hash import FileHasher
from .file_index import FileIndex, FileRecord

logger = logging.getLogger("prometheus.file_integrity")


class IntegrityCheckResult:
    """
    Resultado de verificação de integridade
    """

    def __init__(self):
        self.total_files = 0
        self.valid_files = 0
        self.modified_files: list[str] = []
        self.deleted_files: list[str] = []
        self.corrupted_files: list[str] = []
        self.new_files: list[str] = []
        self.errors: list[str] = []
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_files": self.total_files,
            "valid_files": self.valid_files,
            "modified_count": len(self.modified_files),
            "deleted_count": len(self.deleted_files),
            "corrupted_count": len(self.corrupted_files),
            "new_count": len(self.new_files),
            "error_count": len(self.errors),
            "modified_files": self.modified_files,
            "deleted_files": self.deleted_files,
            "corrupted_files": self.corrupted_files,
            "new_files": self.new_files,
            "errors": self.errors,
            "timestamp": self.timestamp,
            "status": "healthy" if len(self.modified_files + self.corrupted_files) == 0 else "compromised"
        }


class FileIntegrityService:
    """
    Serviço de integridade de arquivos do Prometheus

    Responsabilidades:
    - Verificar integridade de arquivos monitorados
    - Detectar modificações não autorizadas
    - Registrar anomalias
    - Integrar com Safe-Write Engine
    """

    def __init__(
        self,
        index_path: str | Path = "runtime/file_index.json",
        auto_save: bool = True
    ):
        self.hasher = FileHasher()
        self.index = FileIndex(index_path)
        self.auto_save = auto_save
        logger.info("FileIntegrityService inicializado")

    def register_file(
        self,
        file_path: str | Path,
        category: str = "unknown",
        protected: bool = False,
        metadata: Optional[dict] = None
    ) -> bool:
        """
        Registra novo arquivo no índice de integridade

        Args:
            file_path: Caminho do arquivo
            category: Categoria (code, config, data, log)
            protected: Se arquivo é crítico/protegido
            metadata: Metadados adicionais

        Returns:
            True se registrado com sucesso
        """
        try:
            path = Path(file_path)

            if not path.exists():
                logger.error(f"Arquivo não existe: {file_path}")
                return False

            hash_data = self.hasher.hash_with_metadata(path)

            if "error" in hash_data:
                logger.error(f"Erro ao gerar hash: {hash_data['error']}")
                return False

            record = FileRecord(
                path=str(path),
                hash=hash_data["hash"],
                size_bytes=hash_data["size_bytes"],
                modified_at=hash_data["modified_at"],
                indexed_at=datetime.now().isoformat(),
                status="valid",
                category=category,
                protected=protected,
                metadata=metadata or {}
            )

            success = self.index.add_file(record)

            if success and self.auto_save:
                self.index.save()

            logger.info(f"Arquivo registrado: {file_path} (categoria: {category})")
            return success

        except Exception as e:
            logger.error(f"Erro ao registrar arquivo: {e}")
            return False

    def verify_file(self, file_path: str | Path) -> dict[str, Any]:
        """
        Verifica integridade de um arquivo específico

        Args:
            file_path: Caminho do arquivo

        Returns:
            Dict com resultado da verificação
        """
        path_str = str(file_path)
        record = self.index.get_file(path_str)

        if not record:
            return {
                "status": "not_indexed",
                "message": "Arquivo não está no índice",
                "path": path_str
            }

        path = Path(file_path)

        # Verificar se arquivo foi deletado
        if not path.exists():
            self.index.update_file(path_str, status="deleted")
            if self.auto_save:
                self.index.save()

            return {
                "status": "deleted",
                "message": "Arquivo foi deletado",
                "path": path_str,
                "original_hash": record.hash
            }

        # Calcular hash atual
        current_hash = self.hasher.hash_file(path)

        if current_hash is None:
            return {
                "status": "error",
                "message": "Erro ao calcular hash",
                "path": path_str
            }

        # Comparar hashes
        if current_hash == record.hash:
            self.index.update_file(
                path_str,
                status="valid",
                last_verified=datetime.now().isoformat()
            )
            if self.auto_save:
                self.index.save()

            return {
                "status": "valid",
                "message": "Arquivo íntegro",
                "path": path_str,
                "hash": current_hash
            }
        else:
            self.index.mark_as_modified(path_str, current_hash)
            if self.auto_save:
                self.index.save()

            return {
                "status": "modified",
                "message": "Arquivo foi modificado",
                "path": path_str,
                "original_hash": record.hash,
                "current_hash": current_hash,
                "protected": record.protected
            }

    def verify_all(self) -> IntegrityCheckResult:
        """
        Verifica integridade de todos os arquivos indexados

        Returns:
            IntegrityCheckResult com resultados
        """
        result = IntegrityCheckResult()

        all_records = self.index.list_files()
        result.total_files = len(all_records)

        for record in all_records:
            try:
                check = self.verify_file(record.path)

                if check["status"] == "valid":
                    result.valid_files += 1
                elif check["status"] == "modified":
                    result.modified_files.append(record.path)
                elif check["status"] == "deleted":
                    result.deleted_files.append(record.path)
                elif check["status"] == "error":
                    result.errors.append(f"{record.path}: {check['message']}")

            except Exception as e:
                result.errors.append(f"{record.path}: {str(e)}")

        logger.info(f"Verificação completa: {result.valid_files}/{result.total_files} válidos")

        return result

    def get_protected_files(self) -> list[FileRecord]:
        """
        Lista arquivos protegidos/críticos

        Returns:
            Lista de FileRecord protegidos
        """
        return self.index.list_files(protected=True)

    def get_modified_files(self) -> list[FileRecord]:
        """
        Lista arquivos modificados

        Returns:
            Lista de FileRecord modificados
        """
        return self.index.list_files(status="modified")

    def approve_modification(self, file_path: str) -> bool:
        """
        Aprova modificação de arquivo (atualiza hash no índice)

        Args:
            file_path: Caminho do arquivo

        Returns:
            True se aprovado com sucesso
        """
        try:
            path = Path(file_path)

            if not path.exists():
                return False

            current_hash = self.hasher.hash_file(path)

            if current_hash is None:
                return False

            stat = path.stat()

            success = self.index.update_file(
                str(path),
                hash=current_hash,
                size_bytes=stat.st_size,
                modified_at=datetime.fromtimestamp(stat.st_mtime).isoformat(),
                status="valid",
                last_verified=datetime.now().isoformat()
            )

            if success and self.auto_save:
                self.index.save()

            logger.info(f"Modificação aprovada: {file_path}")
            return success

        except Exception as e:
            logger.error(f"Erro ao aprovar modificação: {e}")
            return False

    def get_stats(self) -> dict[str, Any]:
        """
        Estatísticas do sistema de integridade

        Returns:
            Dict com estatísticas
        """
        return self.index.get_stats()
