# -*- coding: utf-8 -*-
"""
BACKGROUND INGESTION - Scheduler para Ingestão Periódica de Conhecimento

Roda ingestores em background a cada X horas
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)


class BackgroundIngestionScheduler:
    """
    Scheduler para rodar ingestão de conhecimento em background

    Roda a cada N horas automaticamente
    """

    def __init__(
        self,
        knowledge_bank,
        interval_hours: int = 6,
        run_on_startup: bool = True
    ):
        """
        Args:
            knowledge_bank: KnowledgeBank instance
            interval_hours: Intervalo entre execuções (horas)
            run_on_startup: Se True, roda ao iniciar
        """
        self.knowledge_bank = knowledge_bank
        self.interval = timedelta(hours=interval_hours)
        self.run_on_startup = run_on_startup

        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None

        logger.info(f"BackgroundIngestionScheduler created: interval={interval_hours}h")

    async def start(self):
        """Inicia scheduler em background"""
        if self.is_running:
            logger.warning("Scheduler already running")
            return

        self.is_running = True

        # Cria task em background
        self.task = asyncio.create_task(self._run_loop())

        logger.info("Background ingestion scheduler started")

    async def stop(self):
        """Para scheduler"""
        if not self.is_running:
            return

        self.is_running = False

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.info("Background ingestion scheduler stopped")

    async def _run_loop(self):
        """Loop principal do scheduler"""
        try:
            # Roda na inicialização se configurado
            if self.run_on_startup:
                logger.info("Running initial ingestion...")
                await self._run_ingestion()

            # Loop infinito
            while self.is_running:
                # Calcula próxima execução
                self.next_run = datetime.now() + self.interval

                logger.info(f"Next ingestion at: {self.next_run.strftime('%Y-%m-%d %H:%M')}")

                # Aguarda até próxima execução
                await asyncio.sleep(self.interval.total_seconds())

                # Roda ingestão
                if self.is_running:
                    await self._run_ingestion()

        except asyncio.CancelledError:
            logger.info("Scheduler loop cancelled")
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}")
            self.is_running = False

    async def _run_ingestion(self):
        """Executa ingestão de todos os ingestores"""
        start_time = datetime.now()
        logger.info("=" * 60)
        logger.info("BACKGROUND INGESTION STARTED")
        logger.info("=" * 60)

        try:
            results = await self.knowledge_bank.ingest_all(background=False)

            self.last_run = datetime.now()
            duration = (self.last_run - start_time).total_seconds()

            total_chunks = sum(results.values())

            logger.info("=" * 60)
            logger.info(f"BACKGROUND INGESTION COMPLETED")
            logger.info(f"Duration: {duration:.1f}s")
            logger.info(f"Total chunks: {total_chunks}")
            logger.info(f"Results by source:")
            for source, count in results.items():
                logger.info(f"  - {source}: {count} chunks")
            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"Error during background ingestion: {e}")

    async def run_now(self):
        """Força execução imediata (fora do schedule)"""
        logger.info("Manual ingestion triggered")
        await self._run_ingestion()

    def get_status(self) -> dict:
        """Retorna status do scheduler"""
        return {
            'is_running': self.is_running,
            'interval_hours': self.interval.total_seconds() / 3600,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'next_run': self.next_run.isoformat() if self.next_run else None,
            'knowledge_bank_stats': self.knowledge_bank.get_stats()
        }
