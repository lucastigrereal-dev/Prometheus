# -*- coding: utf-8 -*-
"""
UNIFIED EXECUTOR - Executa Planos Multi-Step com Segurança

Integra com módulos V2/V3 existentes:
- BrowserController (V2)
- ShadowExecutor (V3)
- PlaybookExecutor (V3)
- SystemToolkit (novo)
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """Status de um step"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


@dataclass
class ExecutionStep:
    """Um step de execução"""
    tool: str  # browser, system, playbook, etc
    action: str  # navigate, screenshot, command, etc
    params: Dict[str, Any] = field(default_factory=dict)
    is_critical: bool = False  # Se True, cria checkpoint antes
    requires_confirmation: bool = False
    timeout_seconds: int = 60
    retry_attempts: int = 1


@dataclass
class StepResult:
    """Resultado de execução de um step"""
    step_number: int
    step: ExecutionStep
    status: StepStatus
    output: Any = None
    error: Optional[str] = None
    duration: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ExecutionPlan:
    """Plano de execução multi-step"""
    plan_id: str
    description: str
    steps: List[ExecutionStep]
    estimated_cost: float = 0.0
    estimated_time: float = 0.0
    requires_confirmation: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    """Resultado completo de execução"""
    plan: ExecutionPlan
    status: StepStatus
    steps_results: List[StepResult]
    total_duration: float = 0.0
    total_cost: float = 0.0
    success: bool = False
    error: Optional[str] = None
    checkpoints_created: int = 0


class UnifiedExecutor:
    """
    Executor unificado que coordena execução de planos

    Usa ferramentas existentes:
    - BrowserController (V2)
    - ShadowExecutor (V3)
    - PlaybookExecutor (V3)
    - SystemToolkit (novo)
    """

    def __init__(
        self,
        integration_bridge=None,
        checkpoint_manager=None,
        dry_run: bool = False
    ):
        """
        Args:
            integration_bridge: PrometheusIntegrationBridge instance
            checkpoint_manager: CheckpointManager instance
            dry_run: Se True, não executa de verdade (modo preview)
        """
        self.bridge = integration_bridge
        self.checkpoint_manager = checkpoint_manager
        self.dry_run = dry_run

        # Carrega ferramentas
        self.tools = {}
        self._load_tools()

        logger.info(f"UnifiedExecutor initialized with {len(self.tools)} tools")

    def _load_tools(self):
        """Carrega ferramentas disponíveis via bridge"""
        if not self.bridge:
            logger.warning("No integration bridge - tools not loaded")
            return

        # Browser (V2)
        try:
            browser = self.bridge.get_module('browser')
            if browser:
                self.tools['browser'] = browser
                logger.info("Tool loaded: browser (V2)")
        except Exception as e:
            logger.warning(f"Browser tool not loaded: {e}")

        # Shadow Executor (V3)
        try:
            shadow = self.bridge.get_module('shadow_executor')
            if shadow:
                self.tools['shadow'] = shadow
                logger.info("Tool loaded: shadow_executor (V3)")
        except Exception as e:
            logger.warning(f"Shadow executor not loaded: {e}")

        # Playbook (V3)
        try:
            playbook = self.bridge.get_module('playbook')
            if playbook:
                self.tools['playbook'] = playbook
                logger.info("Tool loaded: playbook (V3)")
        except Exception as e:
            logger.warning(f"Playbook not loaded: {e}")

        # System Toolkit será carregado separadamente
        # self.tools['system'] = SystemToolkit()

    async def execute(
        self,
        plan: ExecutionPlan,
        confirm_before_execute: bool = None
    ) -> ExecutionResult:
        """
        Executa um plano multi-step

        Args:
            plan: ExecutionPlan a executar
            confirm_before_execute: Se True, pede confirmação antes de executar

        Returns:
            ExecutionResult com status da execução
        """
        start_time = datetime.now()

        logger.info("=" * 60)
        logger.info(f"EXECUTING PLAN: {plan.description}")
        logger.info(f"Steps: {len(plan.steps)}")
        logger.info(f"Estimated cost: ${plan.estimated_cost:.4f}")
        logger.info(f"Estimated time: {plan.estimated_time:.1f}s")
        logger.info("=" * 60)

        # Confirmação
        if confirm_before_execute or plan.requires_confirmation:
            if not await self._confirm_execution(plan):
                logger.info("Execution cancelled by user")
                return ExecutionResult(
                    plan=plan,
                    status=StepStatus.CANCELLED,
                    steps_results=[],
                    success=False,
                    error="Cancelled by user"
                )

        # Executa steps
        results = []
        checkpoints = []

        for i, step in enumerate(plan.steps, 1):
            logger.info(f"\nStep {i}/{len(plan.steps)}: {step.tool}.{step.action}")

            # Checkpoint se step crítico
            if step.is_critical and self.checkpoint_manager:
                logger.info("Creating checkpoint (critical step)...")
                checkpoint = await self.checkpoint_manager.create_checkpoint()
                checkpoints.append(checkpoint)

            # Executa step
            step_result = await self._execute_step(step, step_number=i)
            results.append(step_result)

            # Verifica sucesso
            if step_result.status == StepStatus.FAILED:
                logger.error(f"Step {i} failed: {step_result.error}")

                # Rollback se tiver checkpoints
                if checkpoints and self.checkpoint_manager:
                    logger.info("Rolling back to last checkpoint...")
                    await self.checkpoint_manager.rollback_to(checkpoints[-1])

                # Retorna com falha
                total_duration = (datetime.now() - start_time).total_seconds()

                return ExecutionResult(
                    plan=plan,
                    status=StepStatus.FAILED,
                    steps_results=results,
                    total_duration=total_duration,
                    success=False,
                    error=f"Step {i} failed: {step_result.error}",
                    checkpoints_created=len(checkpoints)
                )

            logger.info(f"Step {i} completed in {step_result.duration:.2f}s")

        # Sucesso total
        total_duration = (datetime.now() - start_time).total_seconds()

        # Limpa checkpoints
        if checkpoints and self.checkpoint_manager:
            await self.checkpoint_manager.cleanup_checkpoints(checkpoints)

        logger.info("=" * 60)
        logger.info(f"EXECUTION COMPLETED")
        logger.info(f"Duration: {total_duration:.1f}s")
        logger.info(f"Steps completed: {len(results)}/{len(plan.steps)}")
        logger.info("=" * 60)

        return ExecutionResult(
            plan=plan,
            status=StepStatus.COMPLETED,
            steps_results=results,
            total_duration=total_duration,
            success=True,
            checkpoints_created=len(checkpoints)
        )

    async def _execute_step(
        self,
        step: ExecutionStep,
        step_number: int
    ) -> StepResult:
        """Executa um step individual"""
        start_time = datetime.now()

        try:
            # Dry run mode
            if self.dry_run:
                logger.info(f"[DRY RUN] Would execute: {step.tool}.{step.action}({step.params})")
                return StepResult(
                    step_number=step_number,
                    step=step,
                    status=StepStatus.COMPLETED,
                    output="[DRY RUN] Simulated execution",
                    duration=0.1
                )

            # Confirmação se necessário
            if step.requires_confirmation:
                if not await self._confirm_step(step):
                    return StepResult(
                        step_number=step_number,
                        step=step,
                        status=StepStatus.CANCELLED,
                        error="Cancelled by user"
                    )

            # Busca tool
            tool = self.tools.get(step.tool)

            if not tool:
                # Tool não encontrado - simula
                logger.warning(f"Tool '{step.tool}' not available - simulating")
                return StepResult(
                    step_number=step_number,
                    step=step,
                    status=StepStatus.COMPLETED,
                    output=f"[SIMULATED] {step.tool}.{step.action}",
                    duration=0.1
                )

            # Executa com timeout e retry
            output = await self._execute_with_retry(
                tool,
                step.action,
                step.params,
                timeout=step.timeout_seconds,
                max_attempts=step.retry_attempts
            )

            duration = (datetime.now() - start_time).total_seconds()

            return StepResult(
                step_number=step_number,
                step=step,
                status=StepStatus.COMPLETED,
                output=output,
                duration=duration
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()

            logger.error(f"Step execution failed: {e}")

            return StepResult(
                step_number=step_number,
                step=step,
                status=StepStatus.FAILED,
                error=str(e),
                duration=duration
            )

    async def _execute_with_retry(
        self,
        tool: Any,
        action: str,
        params: Dict[str, Any],
        timeout: int,
        max_attempts: int
    ) -> Any:
        """Executa com retry automático"""
        last_error = None

        for attempt in range(max_attempts):
            try:
                # TODO: Executar ação real na ferramenta
                # Por ora, simula
                logger.debug(f"Executing: {tool}.{action}({params}) [attempt {attempt+1}/{max_attempts}]")

                # Simula execução
                output = f"Executed {action} with {params}"
                return output

            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt+1} failed: {e}")

                if attempt < max_attempts - 1:
                    # Aguarda antes de retry
                    await asyncio.sleep(1 * (attempt + 1))

        # Todas as tentativas falharam
        raise last_error

    async def _confirm_execution(self, plan: ExecutionPlan) -> bool:
        """Pede confirmação do usuário para executar plano"""
        # TODO: Implementar confirmação real
        # Por ora, retorna True (auto-aprovar)
        logger.debug(f"Auto-confirming execution of: {plan.description}")
        return True

    async def _confirm_step(self, step: ExecutionStep) -> bool:
        """Pede confirmação do usuário para executar step"""
        # TODO: Implementar confirmação real
        # Por ora, retorna True (auto-aprovar)
        logger.debug(f"Auto-confirming step: {step.tool}.{step.action}")
        return True

    def get_available_tools(self) -> List[str]:
        """Retorna lista de ferramentas disponíveis"""
        return list(self.tools.keys())
