"""
File Audit Logger
Sistema de auditoria de alterações em arquivos
"""

import json
from pathlib import Path
from typing import Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger("prometheus.audit")


@dataclass
class AuditEvent:
    """
    Evento de auditoria
    """
    timestamp: str
    event_type: str  # registered, modified, deleted, verified, approved
    file_path: str
    actor: str  # prometheus, user, safe_write, supervisor
    details: dict[str, Any]
    severity: str = "info"  # info, warning, critical
    session_id: Optional[str] = None


class FileAudit:
    """
    Sistema de auditoria de arquivos
    Registra todas as operações no sistema de integridade
    """

    def __init__(self, audit_log_path: str | Path = "runtime/integrity_audit.log"):
        self.audit_log_path = Path(audit_log_path)
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"FileAudit inicializado: {audit_log_path}")

    def log_event(
        self,
        event_type: str,
        file_path: str,
        actor: str = "prometheus",
        details: Optional[dict] = None,
        severity: str = "info",
        session_id: Optional[str] = None
    ) -> bool:
        """
        Registra evento de auditoria

        Args:
            event_type: Tipo do evento
            file_path: Caminho do arquivo
            actor: Quem realizou a ação
            details: Detalhes adicionais
            severity: Severidade (info, warning, critical)
            session_id: ID da sessão

        Returns:
            True se registrado com sucesso
        """
        try:
            event = AuditEvent(
                timestamp=datetime.now().isoformat(),
                event_type=event_type,
                file_path=file_path,
                actor=actor,
                details=details or {},
                severity=severity,
                session_id=session_id
            )

            # Append ao log file
            with open(self.audit_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(asdict(event)) + '\n')

            # Log também no logger padrão
            log_msg = f"[{event_type}] {file_path} by {actor}"
            if severity == "critical":
                logger.critical(log_msg)
            elif severity == "warning":
                logger.warning(log_msg)
            else:
                logger.info(log_msg)

            return True

        except Exception as e:
            logger.error(f"Erro ao registrar evento de auditoria: {e}")
            return False

    def log_registration(self, file_path: str, category: str, protected: bool) -> bool:
        """
        Registra evento de registro de arquivo
        """
        return self.log_event(
            event_type="registered",
            file_path=file_path,
            details={
                "category": category,
                "protected": protected
            }
        )

    def log_modification(
        self,
        file_path: str,
        original_hash: str,
        new_hash: str,
        authorized: bool = False
    ) -> bool:
        """
        Registra evento de modificação
        """
        return self.log_event(
            event_type="modified",
            file_path=file_path,
            severity="warning" if not authorized else "info",
            details={
                "original_hash": original_hash,
                "new_hash": new_hash,
                "authorized": authorized
            }
        )

    def log_deletion(self, file_path: str, protected: bool = False) -> bool:
        """
        Registra evento de deleção
        """
        return self.log_event(
            event_type="deleted",
            file_path=file_path,
            severity="critical" if protected else "warning",
            details={
                "protected": protected
            }
        )

    def log_verification(self, file_path: str, status: str) -> bool:
        """
        Registra evento de verificação
        """
        return self.log_event(
            event_type="verified",
            file_path=file_path,
            details={
                "status": status
            }
        )

    def log_approval(self, file_path: str, approved_by: str) -> bool:
        """
        Registra evento de aprovação de modificação
        """
        return self.log_event(
            event_type="approved",
            file_path=file_path,
            actor=approved_by,
            details={
                "action": "modification_approved"
            }
        )

    def get_recent_events(self, limit: int = 100) -> list[dict]:
        """
        Busca eventos recentes

        Args:
            limit: Número máximo de eventos

        Returns:
            Lista de eventos (mais recentes primeiro)
        """
        try:
            if not self.audit_log_path.exists():
                return []

            events = []

            with open(self.audit_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event = json.loads(line.strip())
                        events.append(event)
                    except:
                        continue

            # Retornar mais recentes primeiro
            return events[-limit:][::-1]

        except Exception as e:
            logger.error(f"Erro ao buscar eventos: {e}")
            return []

    def get_events_for_file(self, file_path: str, limit: int = 50) -> list[dict]:
        """
        Busca eventos de um arquivo específico

        Args:
            file_path: Caminho do arquivo
            limit: Número máximo de eventos

        Returns:
            Lista de eventos do arquivo
        """
        all_events = self.get_recent_events(limit=1000)
        file_events = [e for e in all_events if e.get("file_path") == file_path]
        return file_events[:limit]

    def get_critical_events(self, limit: int = 50) -> list[dict]:
        """
        Busca eventos críticos

        Args:
            limit: Número máximo de eventos

        Returns:
            Lista de eventos críticos
        """
        all_events = self.get_recent_events(limit=1000)
        critical = [e for e in all_events if e.get("severity") == "critical"]
        return critical[:limit]
