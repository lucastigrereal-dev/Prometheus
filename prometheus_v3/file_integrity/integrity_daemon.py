"""
Integrity Daemon
Daemon de verificação periódica de integridade (opcional)
"""

import time
import threading
from typing import Optional, Callable
from datetime import datetime
import logging

from .file_integrity_service import FileIntegrityService

logger = logging.getLogger("prometheus.integrity_daemon")


class IntegrityDaemon:
    """
    Daemon para verificação periódica de integridade

    ⚠️ NOTA: Não inicializa automaticamente
    Deve ser iniciado manualmente após integração
    """

    def __init__(
        self,
        service: FileIntegrityService,
        check_interval: int = 300,  # 5 minutos
        on_anomaly: Optional[Callable] = None
    ):
        self.service = service
        self.check_interval = check_interval
        self.on_anomaly = on_anomaly
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.last_check: Optional[str] = None
        logger.info(f"IntegrityDaemon criado (intervalo: {check_interval}s)")

    def start(self) -> bool:
        """
        Inicia daemon em background thread

        Returns:
            True se iniciado com sucesso
        """
        if self.running:
            logger.warning("Daemon já está rodando")
            return False

        try:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            logger.info("IntegrityDaemon iniciado")
            return True

        except Exception as e:
            logger.error(f"Erro ao iniciar daemon: {e}")
            self.running = False
            return False

    def stop(self) -> bool:
        """
        Para daemon

        Returns:
            True se parado com sucesso
        """
        if not self.running:
            logger.warning("Daemon não está rodando")
            return False

        self.running = False
        logger.info("IntegrityDaemon parado")
        return True

    def _run_loop(self):
        """
        Loop principal do daemon
        """
        logger.info("Loop do daemon iniciado")

        while self.running:
            try:
                logger.debug("Executando verificação de integridade...")

                result = self.service.verify_all()
                self.last_check = datetime.now().isoformat()

                # Detectar anomalias
                has_anomaly = (
                    len(result.modified_files) > 0 or
                    len(result.corrupted_files) > 0 or
                    len(result.deleted_files) > 0
                )

                if has_anomaly:
                    logger.warning(
                        f"Anomalias detectadas: "
                        f"{len(result.modified_files)} modificados, "
                        f"{len(result.deleted_files)} deletados"
                    )

                    if self.on_anomaly:
                        try:
                            self.on_anomaly(result)
                        except Exception as e:
                            logger.error(f"Erro no callback de anomalia: {e}")

                else:
                    logger.debug(f"Verificação OK: {result.valid_files}/{result.total_files} válidos")

            except Exception as e:
                logger.error(f"Erro no loop do daemon: {e}")

            # Sleep por intervalo
            time.sleep(self.check_interval)

        logger.info("Loop do daemon finalizado")

    def get_status(self) -> dict:
        """
        Status do daemon

        Returns:
            Dict com status
        """
        return {
            "running": self.running,
            "check_interval": self.check_interval,
            "last_check": self.last_check,
            "thread_alive": self.thread.is_alive() if self.thread else False
        }
