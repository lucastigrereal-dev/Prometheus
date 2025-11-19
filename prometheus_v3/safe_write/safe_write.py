"""
Safe Write Engine
Motor de escrita segura com verificação, backup e rollback
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger("prometheus.safe_write")


class WriteMode(Enum):
    """Modos de escrita"""
    CREATE = "create"  # Criar novo arquivo
    OVERWRITE = "overwrite"  # Sobrescrever existente
    APPEND = "append"  # Adicionar ao final


@dataclass
class WriteOperation:
    """
    Operação de escrita a ser executada
    """
    target_path: str
    content: str | bytes
    mode: WriteMode = WriteMode.CREATE
    encoding: str = "utf-8"
    create_backup: bool = True
    verify_after: bool = True
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class WriteResult:
    """
    Resultado de operação de escrita
    """
    success: bool
    operation_id: str
    target_path: str
    backup_path: Optional[str] = None
    temp_path: Optional[str] = None
    bytes_written: int = 0
    verification_passed: bool = False
    error_message: Optional[str] = None
    timestamp: str = None
    duration_ms: float = 0.0

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SafeWriter:
    """
    Motor de escrita segura do Prometheus

    Pipeline:
    1. Validação de operação
    2. Criação de backup (se necessário)
    3. Escrita em arquivo temporário
    4. Verificação de conteúdo
    5. Commit (move temp → target)
    6. Registro no índice de integridade
    7. Log da operação

    Características:
    - Transacional (tudo ou nada)
    - Backup automático
    - Verificação de conteúdo
    - Rollback em caso de erro
    - Integração com FileIntegrityService
    """

    def __init__(
        self,
        backup_dir: str | Path = "runtime/backups",
        integrity_service: Optional[Any] = None,
        audit_logger: Optional[Any] = None,
        dry_run: bool = False
    ):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.integrity_service = integrity_service
        self.audit_logger = audit_logger
        self.dry_run = dry_run
        self.operation_counter = 0
        logger.info(f"SafeWriter inicializado (dry_run={dry_run})")

    def write(self, operation: WriteOperation) -> WriteResult:
        """
        Executa operação de escrita segura

        Args:
            operation: WriteOperation com detalhes da escrita

        Returns:
            WriteResult com resultado da operação
        """
        start_time = datetime.now()
        operation_id = self._generate_operation_id()

        logger.info(f"[{operation_id}] Iniciando escrita segura: {operation.target_path}")

        # Dry run mode
        if self.dry_run:
            logger.info(f"[{operation_id}] DRY RUN - operação simulada")
            return WriteResult(
                success=True,
                operation_id=operation_id,
                target_path=operation.target_path,
                bytes_written=len(operation.content) if isinstance(operation.content, bytes) else len(operation.content.encode(operation.encoding)),
                verification_passed=True,
                error_message="DRY RUN MODE - nenhuma alteração real"
            )

        try:
            # 1. Validação
            validation_error = self._validate_operation(operation)
            if validation_error:
                return self._create_error_result(operation_id, operation.target_path, validation_error)

            target_path = Path(operation.target_path)
            backup_path = None
            temp_path = None

            # 2. Criar backup se arquivo existe
            if operation.create_backup and target_path.exists():
                backup_path = self._create_backup(target_path)
                logger.info(f"[{operation_id}] Backup criado: {backup_path}")

            # 3. Escrever em arquivo temporário
            temp_path = self._write_to_temp(operation, operation_id)
            logger.debug(f"[{operation_id}] Escrito em temp: {temp_path}")

            # 4. Verificar conteúdo
            if operation.verify_after:
                verification_ok = self._verify_temp_file(temp_path, operation)
                if not verification_ok:
                    self._cleanup_temp(temp_path)
                    return self._create_error_result(
                        operation_id,
                        operation.target_path,
                        "Falha na verificação de conteúdo"
                    )

            # 5. Commit (move temp → target)
            bytes_written = self._commit_write(temp_path, target_path, operation)
            logger.info(f"[{operation_id}] Commit realizado: {bytes_written} bytes")

            # 6. Registrar no índice de integridade
            if self.integrity_service:
                self._register_in_integrity(target_path, operation)

            # 7. Log de auditoria
            if self.audit_logger:
                self._log_audit(operation_id, operation, backup_path)

            # Calcular duração
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            result = WriteResult(
                success=True,
                operation_id=operation_id,
                target_path=str(target_path),
                backup_path=str(backup_path) if backup_path else None,
                temp_path=str(temp_path),
                bytes_written=bytes_written,
                verification_passed=operation.verify_after,
                duration_ms=duration_ms
            )

            logger.info(f"[{operation_id}] Escrita segura concluída com sucesso")
            return result

        except Exception as e:
            logger.error(f"[{operation_id}] Erro na escrita segura: {e}")

            # Tentar rollback se backup existe
            if backup_path and Path(backup_path).exists():
                try:
                    self._rollback(backup_path, target_path)
                    logger.info(f"[{operation_id}] Rollback executado")
                except Exception as rollback_error:
                    logger.error(f"[{operation_id}] Erro no rollback: {rollback_error}")

            # Cleanup temp file
            if temp_path:
                self._cleanup_temp(temp_path)

            return self._create_error_result(operation_id, operation.target_path, str(e))

    def write_text(
        self,
        path: str | Path,
        content: str,
        mode: WriteMode = WriteMode.CREATE,
        encoding: str = "utf-8",
        create_backup: bool = True
    ) -> WriteResult:
        """
        Escreve arquivo de texto (helper method)

        Args:
            path: Caminho do arquivo
            content: Conteúdo texto
            mode: Modo de escrita
            encoding: Encoding
            create_backup: Criar backup

        Returns:
            WriteResult
        """
        operation = WriteOperation(
            target_path=str(path),
            content=content,
            mode=mode,
            encoding=encoding,
            create_backup=create_backup
        )
        return self.write(operation)

    def write_bytes(
        self,
        path: str | Path,
        content: bytes,
        mode: WriteMode = WriteMode.CREATE,
        create_backup: bool = True
    ) -> WriteResult:
        """
        Escreve arquivo binário (helper method)

        Args:
            path: Caminho do arquivo
            content: Conteúdo bytes
            mode: Modo de escrita
            create_backup: Criar backup

        Returns:
            WriteResult
        """
        operation = WriteOperation(
            target_path=str(path),
            content=content,
            mode=mode,
            create_backup=create_backup
        )
        return self.write(operation)

    def _validate_operation(self, operation: WriteOperation) -> Optional[str]:
        """
        Valida operação de escrita

        Returns:
            String de erro ou None se válido
        """
        target_path = Path(operation.target_path)

        # Validar modo CREATE
        if operation.mode == WriteMode.CREATE:
            if target_path.exists():
                return f"Arquivo já existe (modo CREATE): {operation.target_path}"

        # Validar modo OVERWRITE
        if operation.mode == WriteMode.OVERWRITE:
            if not target_path.exists():
                return f"Arquivo não existe (modo OVERWRITE): {operation.target_path}"

        # Validar modo APPEND
        if operation.mode == WriteMode.APPEND:
            if not target_path.exists():
                return f"Arquivo não existe (modo APPEND): {operation.target_path}"

        # Validar diretório pai existe
        if not target_path.parent.exists():
            try:
                target_path.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                return f"Não foi possível criar diretório: {e}"

        # Validar permissões de escrita
        if target_path.exists():
            if not os.access(target_path, os.W_OK):
                return f"Sem permissão de escrita: {operation.target_path}"

        return None

    def _create_backup(self, target_path: Path) -> Path:
        """
        Cria backup de arquivo existente

        Args:
            target_path: Caminho do arquivo original

        Returns:
            Caminho do backup
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{target_path.name}.{timestamp}.bak"
        backup_path = self.backup_dir / backup_name

        shutil.copy2(target_path, backup_path)

        return backup_path

    def _write_to_temp(self, operation: WriteOperation, operation_id: str) -> Path:
        """
        Escreve conteúdo em arquivo temporário

        Args:
            operation: WriteOperation
            operation_id: ID da operação

        Returns:
            Caminho do arquivo temporário
        """
        # Criar temp file no mesmo diretório do target (garante mesmo filesystem)
        target_path = Path(operation.target_path)
        temp_dir = target_path.parent

        # Criar temp file
        fd, temp_path_str = tempfile.mkstemp(
            dir=temp_dir,
            prefix=f".prometheus_temp_{operation_id}_",
            suffix=target_path.suffix
        )

        temp_path = Path(temp_path_str)

        try:
            if isinstance(operation.content, bytes):
                # Conteúdo binário
                with os.fdopen(fd, 'wb') as f:
                    f.write(operation.content)
            else:
                # Conteúdo texto
                with os.fdopen(fd, 'w', encoding=operation.encoding) as f:
                    f.write(operation.content)

            return temp_path

        except Exception as e:
            os.close(fd)
            raise e

    def _verify_temp_file(self, temp_path: Path, operation: WriteOperation) -> bool:
        """
        Verifica conteúdo do arquivo temporário

        Args:
            temp_path: Caminho do arquivo temporário
            operation: WriteOperation original

        Returns:
            True se verificação passou
        """
        try:
            if isinstance(operation.content, bytes):
                with open(temp_path, 'rb') as f:
                    written_content = f.read()
                return written_content == operation.content
            else:
                with open(temp_path, 'r', encoding=operation.encoding) as f:
                    written_content = f.read()
                return written_content == operation.content

        except Exception as e:
            logger.error(f"Erro na verificação: {e}")
            return False

    def _commit_write(self, temp_path: Path, target_path: Path, operation: WriteOperation) -> int:
        """
        Commit da escrita (move temp → target)

        Args:
            temp_path: Caminho temporário
            target_path: Caminho final
            operation: WriteOperation

        Returns:
            Número de bytes escritos
        """
        # Obter tamanho antes de mover
        bytes_written = temp_path.stat().st_size

        if operation.mode == WriteMode.APPEND:
            # Modo append: adicionar conteúdo ao final
            with open(temp_path, 'rb') as temp_f:
                with open(target_path, 'ab') as target_f:
                    target_f.write(temp_f.read())
            # Remover temp
            temp_path.unlink()
        else:
            # Modo CREATE ou OVERWRITE: substituir arquivo
            shutil.move(str(temp_path), str(target_path))

        return bytes_written

    def _register_in_integrity(self, target_path: Path, operation: WriteOperation):
        """
        Registra arquivo no índice de integridade

        Args:
            target_path: Caminho do arquivo
            operation: WriteOperation
        """
        try:
            # Determinar categoria baseado na extensão
            category = self._determine_category(target_path)

            # Verificar se já está registrado
            existing = self.integrity_service.index.get_file(str(target_path))

            if existing:
                # Aprovar modificação (atualizar hash)
                self.integrity_service.approve_modification(str(target_path))
            else:
                # Registrar novo arquivo
                self.integrity_service.register_file(
                    file_path=target_path,
                    category=category,
                    protected=operation.metadata.get("protected", False),
                    metadata=operation.metadata
                )

        except Exception as e:
            logger.error(f"Erro ao registrar no índice de integridade: {e}")

    def _determine_category(self, path: Path) -> str:
        """
        Determina categoria do arquivo baseado na extensão

        Args:
            path: Caminho do arquivo

        Returns:
            Categoria (code, config, data, log)
        """
        suffix = path.suffix.lower()

        code_extensions = {'.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.cpp', '.c', '.h'}
        config_extensions = {'.yaml', '.yml', '.json', '.toml', '.ini', '.env', '.conf'}
        log_extensions = {'.log', '.txt'}

        if suffix in code_extensions:
            return "code"
        elif suffix in config_extensions:
            return "config"
        elif suffix in log_extensions:
            return "log"
        else:
            return "data"

    def _log_audit(self, operation_id: str, operation: WriteOperation, backup_path: Optional[Path]):
        """
        Registra operação no log de auditoria

        Args:
            operation_id: ID da operação
            operation: WriteOperation
            backup_path: Caminho do backup (se criado)
        """
        try:
            self.audit_logger.log_event(
                event_type="safe_write",
                file_path=operation.target_path,
                actor="safe_write_engine",
                details={
                    "operation_id": operation_id,
                    "mode": operation.mode.value,
                    "backup_created": backup_path is not None,
                    "backup_path": str(backup_path) if backup_path else None,
                    "verified": operation.verify_after
                }
            )
        except Exception as e:
            logger.error(f"Erro ao registrar auditoria: {e}")

    def _rollback(self, backup_path: Path, target_path: Path):
        """
        Executa rollback (restaura backup)

        Args:
            backup_path: Caminho do backup
            target_path: Caminho do arquivo original
        """
        shutil.copy2(backup_path, target_path)
        logger.info(f"Rollback executado: {target_path} restaurado")

    def _cleanup_temp(self, temp_path: Path | str):
        """
        Remove arquivo temporário

        Args:
            temp_path: Caminho do arquivo temporário
        """
        try:
            Path(temp_path).unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Erro ao remover temp file: {e}")

    def _generate_operation_id(self) -> str:
        """
        Gera ID único para operação

        Returns:
            ID da operação
        """
        self.operation_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"SW_{timestamp}_{self.operation_counter:04d}"

    def _create_error_result(self, operation_id: str, target_path: str, error: str) -> WriteResult:
        """
        Cria WriteResult de erro

        Args:
            operation_id: ID da operação
            target_path: Caminho do arquivo
            error: Mensagem de erro

        Returns:
            WriteResult com erro
        """
        return WriteResult(
            success=False,
            operation_id=operation_id,
            target_path=target_path,
            error_message=error
        )

    def get_backup_files(self, original_path: str | Path) -> list[Path]:
        """
        Lista backups de um arquivo

        Args:
            original_path: Caminho do arquivo original

        Returns:
            Lista de caminhos de backup
        """
        original_name = Path(original_path).name
        pattern = f"{original_name}.*.bak"

        backups = list(self.backup_dir.glob(pattern))
        backups.sort(reverse=True)  # Mais recentes primeiro

        return backups

    def restore_from_backup(self, backup_path: str | Path, target_path: str | Path) -> bool:
        """
        Restaura arquivo de backup

        Args:
            backup_path: Caminho do backup
            target_path: Caminho de destino

        Returns:
            True se restaurado com sucesso
        """
        try:
            shutil.copy2(backup_path, target_path)
            logger.info(f"Arquivo restaurado de backup: {target_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao restaurar backup: {e}")
            return False
