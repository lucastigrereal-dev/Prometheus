"""
Safe Write Logger
Sistema de logging específico para Safe-Write Engine
"""

import json
from pathlib import Path
from typing import Optional, Any
from datetime import datetime
import logging

logger = logging.getLogger("prometheus.safe_write_logger")


class SafeWriteLogger:
    """
    Logger especializado para operações de Safe-Write
    Registra todas as operações de escrita em log estruturado
    """

    def __init__(self, log_path: str | Path = "runtime/safe_write.log"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"SafeWriteLogger inicializado: {log_path}")

    def log_operation(
        self,
        operation_id: str,
        operation_type: str,
        target_path: str,
        status: str,
        details: Optional[dict[str, Any]] = None
    ) -> bool:
        """
        Registra operação de escrita

        Args:
            operation_id: ID da operação
            operation_type: Tipo (write, rollback, restore)
            target_path: Caminho do arquivo
            status: Status (success, failed, verified)
            details: Detalhes adicionais

        Returns:
            True se registrado com sucesso
        """
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "operation_id": operation_id,
                "operation_type": operation_type,
                "target_path": target_path,
                "status": status,
                "details": details or {}
            }

            with open(self.log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')

            return True

        except Exception as e:
            logger.error(f"Erro ao registrar operação: {e}")
            return False

    def log_write_success(
        self,
        operation_id: str,
        target_path: str,
        bytes_written: int,
        backup_created: bool,
        duration_ms: float
    ) -> bool:
        """
        Registra escrita bem-sucedida
        """
        return self.log_operation(
            operation_id=operation_id,
            operation_type="write",
            target_path=target_path,
            status="success",
            details={
                "bytes_written": bytes_written,
                "backup_created": backup_created,
                "duration_ms": duration_ms
            }
        )

    def log_write_failure(
        self,
        operation_id: str,
        target_path: str,
        error: str,
        rollback_executed: bool
    ) -> bool:
        """
        Registra falha de escrita
        """
        return self.log_operation(
            operation_id=operation_id,
            operation_type="write",
            target_path=target_path,
            status="failed",
            details={
                "error": error,
                "rollback_executed": rollback_executed
            }
        )

    def log_verification(
        self,
        operation_id: str,
        target_path: str,
        passed: bool,
        details: Optional[dict] = None
    ) -> bool:
        """
        Registra verificação de conteúdo
        """
        return self.log_operation(
            operation_id=operation_id,
            operation_type="verification",
            target_path=target_path,
            status="passed" if passed else "failed",
            details=details or {}
        )

    def log_rollback(
        self,
        operation_id: str,
        target_path: str,
        backup_path: str,
        success: bool
    ) -> bool:
        """
        Registra operação de rollback
        """
        return self.log_operation(
            operation_id=operation_id,
            operation_type="rollback",
            target_path=target_path,
            status="success" if success else "failed",
            details={
                "backup_path": backup_path
            }
        )

    def get_recent_operations(self, limit: int = 100) -> list[dict]:
        """
        Busca operações recentes

        Args:
            limit: Número máximo de operações

        Returns:
            Lista de operações
        """
        try:
            if not self.log_path.exists():
                return []

            operations = []

            with open(self.log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        operation = json.loads(line.strip())
                        operations.append(operation)
                    except:
                        continue

            return operations[-limit:][::-1]

        except Exception as e:
            logger.error(f"Erro ao buscar operações: {e}")
            return []

    def get_operations_for_file(self, file_path: str, limit: int = 50) -> list[dict]:
        """
        Busca operações de um arquivo específico

        Args:
            file_path: Caminho do arquivo
            limit: Número máximo de operações

        Returns:
            Lista de operações do arquivo
        """
        all_ops = self.get_recent_operations(limit=1000)
        file_ops = [op for op in all_ops if op.get("target_path") == file_path]
        return file_ops[:limit]

    def get_failed_operations(self, limit: int = 50) -> list[dict]:
        """
        Busca operações que falharam

        Args:
            limit: Número máximo de operações

        Returns:
            Lista de operações falhadas
        """
        all_ops = self.get_recent_operations(limit=1000)
        failed = [op for op in all_ops if op.get("status") == "failed"]
        return failed[:limit]

    def get_stats(self) -> dict[str, Any]:
        """
        Estatísticas de operações

        Returns:
            Dict com estatísticas
        """
        all_ops = self.get_recent_operations(limit=10000)

        return {
            "total_operations": len(all_ops),
            "successful": len([op for op in all_ops if op.get("status") == "success"]),
            "failed": len([op for op in all_ops if op.get("status") == "failed"]),
            "rollbacks": len([op for op in all_ops if op.get("operation_type") == "rollback"]),
            "last_operation": all_ops[0] if all_ops else None
        }
