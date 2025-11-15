# -*- coding: utf-8 -*-
"""
JARVIS INTERFACE - Interface Conversacional Unificada

Integra TODOS os componentes:
- Knowledge Bank (Semana 1)
- Unified Executor (Semana 2)
- Task Planner (Semana 3)

Pipeline completo: Entender → Planejar → Executar → Aprender
"""

import logging
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

from ..knowledge.knowledge_bank import KnowledgeBank
from ..knowledge.smart_cache import SmartCache
from ..knowledge.ingestors import PerplexityIngestor, ClaudeHistoryIngestor, GPTHistoryIngestor
from ..execution.unified_executor import UnifiedExecutor, ExecutionResult
from ..execution.checkpoint_manager import CheckpointManager
from ..planning.task_planner import TaskPlanner
from ..planning.template_manager import TemplateManager

logger = logging.getLogger(__name__)


@dataclass
class TaskResult:
    """Resultado completo de uma tarefa"""
    task_description: str
    success: bool
    execution_result: Optional[ExecutionResult] = None
    error: Optional[str] = None
    used_template: bool = False
    cost: float = 0.0
    duration: float = 0.0
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class JarvisInterface:
    """
    Interface Jarvis - Experiência Conversacional Completa

    Exemplo de uso:
    ```python
    jarvis = JarvisInterface()

    result = await jarvis.process_command(
        "Crie um endpoint FastAPI de health check"
    )

    if result.success:
        print(f"OK Pronto! Custo: ${result.cost:.4f}")
    ```
    """

    def __init__(
        self,
        integration_bridge=None,
        auto_confirm: bool = False,
        dry_run: bool = False
    ):
        """
        Args:
            integration_bridge: PrometheusIntegrationBridge instance
            auto_confirm: Se True, não pede confirmação
            dry_run: Se True, não executa de verdade
        """
        self.bridge = integration_bridge
        self.auto_confirm = auto_confirm
        self.dry_run = dry_run

        # Inicializa componentes
        logger.info("Initializing Jarvis Interface...")

        # Knowledge Bank
        self.knowledge_bank = KnowledgeBank(
            cache=SmartCache(l1_max_size=100, l2_enabled=True),
            ingestors=[
                PerplexityIngestor(),
                ClaudeHistoryIngestor(),
                GPTHistoryIngestor()
            ]
        )

        # Template Manager
        self.template_manager = TemplateManager()

        # Task Planner
        self.task_planner = TaskPlanner(
            integration_bridge=self.bridge,
            knowledge_bank=self.knowledge_bank,
            template_manager=self.template_manager
        )

        # Unified Executor
        self.checkpoint_manager = CheckpointManager()
        self.unified_executor = UnifiedExecutor(
            integration_bridge=self.bridge,
            checkpoint_manager=self.checkpoint_manager,
            dry_run=self.dry_run
        )

        # Stats
        self.stats = {
            'total_tasks': 0,
            'successful_tasks': 0,
            'failed_tasks': 0,
            'template_uses': 0,
            'total_cost': 0.0
        }

        logger.info("Jarvis Interface ready!")

    async def process_command(
        self,
        user_input: str,
        confirm_before_execute: bool = None
    ) -> TaskResult:
        """
        Processa comando do usuário (pipeline completo)

        Args:
            user_input: Comando em linguagem natural
            confirm_before_execute: Se None, usa self.auto_confirm

        Returns:
            TaskResult
        """
        start_time = datetime.now()

        logger.info("=" * 60)
        logger.info(f"JARVIS: Processing command")
        logger.info(f"Input: {user_input}")
        logger.info("=" * 60)

        self.stats['total_tasks'] += 1

        try:
            # STEP 1: Buscar conhecimento relevante
            logger.info("\n[1/5] Searching knowledge...")
            context = await self.knowledge_bank.search(user_input, limit=3)
            logger.info(f"Found {len(context)} relevant chunks")

            # STEP 2: Gerar plano (template ou IA)
            logger.info("\n[2/5] Generating execution plan...")
            plan = await self.task_planner.plan_execution(user_input)

            used_template = plan.metadata.get('from_template', False)
            if used_template:
                self.stats['template_uses'] += 1
                logger.info(f"Using template (cost: $0)")
            else:
                logger.info(f"Generated with AI (cost: ${plan.estimated_cost:.4f})")

            logger.info(f"\nPlan: {len(plan.steps)} steps")
            for i, step in enumerate(plan.steps, 1):
                logger.info(f"  {i}. {step.tool}.{step.action}")

            # STEP 3: Confirmação (opcional)
            if confirm_before_execute is None:
                confirm_before_execute = not self.auto_confirm

            if confirm_before_execute:
                logger.info("\n[3/5] Requesting confirmation...")
                confirmed = await self._confirm_execution(plan)

                if not confirmed:
                    logger.info("Execution cancelled by user")
                    return TaskResult(
                        task_description=user_input,
                        success=False,
                        error="Cancelled by user",
                        used_template=used_template
                    )
            else:
                logger.info("\n[3/5] Auto-confirming execution...")

            # STEP 4: Executar
            logger.info("\n[4/5] Executing plan...")
            execution_result = await self.unified_executor.execute(
                plan,
                confirm_before_execute=False  # Já confirmamos acima
            )

            # STEP 5: Aprender (se bem-sucedido)
            if execution_result.success:
                logger.info("\n[5/5] Learning from success...")
                await self._learn_from_success(user_input, plan, execution_result)
                self.stats['successful_tasks'] += 1
            else:
                self.stats['failed_tasks'] += 1

            # Calcula duração e custo total
            duration = (datetime.now() - start_time).total_seconds()
            total_cost = plan.estimated_cost

            self.stats['total_cost'] += total_cost

            logger.info("=" * 60)
            logger.info(f"RESULT: {'SUCCESS' if execution_result.success else 'FAILED'}")
            logger.info(f"Duration: {duration:.1f}s")
            logger.info(f"Cost: ${total_cost:.4f}")
            logger.info(f"Template: {used_template}")
            logger.info("=" * 60)

            return TaskResult(
                task_description=user_input,
                success=execution_result.success,
                execution_result=execution_result,
                used_template=used_template,
                cost=total_cost,
                duration=duration
            )

        except Exception as e:
            logger.error(f"Error processing command: {e}")
            import traceback
            traceback.print_exc()

            self.stats['failed_tasks'] += 1

            return TaskResult(
                task_description=user_input,
                success=False,
                error=str(e)
            )

    async def _confirm_execution(self, plan) -> bool:
        """Pede confirmação do usuário"""
        # TODO: Implementar UI de confirmação real
        # Por ora, auto-aprova
        logger.info(f"Auto-approving plan execution")
        return True

    async def _learn_from_success(self, task: str, plan, execution_result):
        """Aprende com execução bem-sucedida"""
        try:
            # Salva em KnowledgeBank
            await self.knowledge_bank.store_task_result(task, plan, execution_result)

            # Salva como template (se não veio de template)
            if not plan.metadata.get('from_template'):
                # Extrai intent/entities (simplificado)
                intent = plan.metadata.get('intent', 'generico')
                entities = {}

                await self.task_planner.save_successful_plan(
                    task,
                    intent,
                    entities,
                    plan
                )

                logger.info("Saved as new template")

        except Exception as e:
            logger.error(f"Error learning from success: {e}")

    def get_stats(self) -> dict:
        """Retorna estatísticas do Jarvis"""
        kb_stats = self.knowledge_bank.get_stats()
        template_stats = self.template_manager.get_stats()

        return {
            **self.stats,
            'success_rate': (
                self.stats['successful_tasks'] / self.stats['total_tasks']
                if self.stats['total_tasks'] > 0 else 0.0
            ),
            'template_usage_rate': (
                self.stats['template_uses'] / self.stats['total_tasks']
                if self.stats['total_tasks'] > 0 else 0.0
            ),
            'knowledge_bank': kb_stats,
            'templates': template_stats
        }

    async def ingest_knowledge(self):
        """Roda ingestão de conhecimento"""
        logger.info("Running knowledge ingestion...")
        results = await self.knowledge_bank.ingest_all()
        logger.info(f"Ingestion complete: {sum(results.values())} chunks")
        return results
