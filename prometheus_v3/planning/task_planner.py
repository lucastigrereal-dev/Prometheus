# -*- coding: utf-8 -*-
"""
TASK PLANNER - Planejamento Inteligente de Tarefas

Integra:
- TaskAnalyzer (V2) para classificação
- KnowledgeBank para contexto
- TemplateManager para reuso
- ConsensusEngine (V2) para geração
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

from ..execution.unified_executor import ExecutionPlan, ExecutionStep

logger = logging.getLogger(__name__)


class TaskPlanner:
    """
    Planejador inteligente que gera planos de execução

    Pipeline:
    1. Classifica intent
    2. Busca conhecimento relevante
    3. Tenta encontrar template
    4. Se não encontrar, gera com IA
    5. Retorna ExecutionPlan
    """

    def __init__(
        self,
        integration_bridge=None,
        knowledge_bank=None,
        template_manager=None
    ):
        self.bridge = integration_bridge
        self.knowledge_bank = knowledge_bank
        self.template_manager = template_manager

        # Carrega componentes V2
        self.task_analyzer = None
        self.consensus_engine = None

        if self.bridge:
            try:
                self.task_analyzer = self.bridge.get_module('task_analyzer')
            except:
                logger.warning("TaskAnalyzer (V2) not available")

            try:
                self.consensus_engine = self.bridge.get_module('consensus')
            except:
                logger.warning("ConsensusEngine (V2) not available")

        logger.info("TaskPlanner initialized")

    async def plan_execution(
        self,
        task_description: str,
        use_templates: bool = True,
        use_ai: bool = True
    ) -> ExecutionPlan:
        """
        Gera plano de execução

        Args:
            task_description: Descrição da tarefa
            use_templates: Se True, tenta usar templates
            use_ai: Se True, usa IA se não encontrar template

        Returns:
            ExecutionPlan
        """
        logger.info(f"Planning task: {task_description}")

        # 1. Classificar intent e entidades
        intent, entities = await self._classify_task(task_description)
        logger.info(f"Intent: {intent}, Entities: {entities}")

        # 2. Buscar conhecimento relevante
        context = await self._get_context(task_description)
        logger.info(f"Found {len(context)} relevant knowledge chunks")

        # 3. Tentar usar template
        if use_templates and self.template_manager:
            template = await self.template_manager.find_matching_template(
                task_description,
                intent,
                min_similarity=0.90
            )

            if template:
                logger.info(f"Using template: {template.pattern}")
                return self._instantiate_template(template, task_description, intent, entities)

        # 4. Gerar com IA
        if use_ai:
            logger.info("Generating plan with AI...")
            return await self._generate_with_ai(task_description, intent, entities, context)

        # 5. Fallback: Plano genérico
        logger.warning("No template or AI available - returning generic plan")
        return self._create_generic_plan(task_description, intent, entities)

    async def _classify_task(self, task_description: str) -> tuple[str, Dict[str, Any]]:
        """Classifica intent e extrai entidades"""
        if self.task_analyzer:
            try:
                # TODO: Chamar TaskAnalyzer real quando integrado
                pass
            except Exception as e:
                logger.error(f"TaskAnalyzer error: {e}")

        # Fallback: Classificação simples
        return self._simple_classification(task_description)

    def _simple_classification(self, text: str) -> tuple[str, Dict[str, Any]]:
        """Classificação simples por keywords"""
        text_lower = text.lower()

        # Intent
        if any(kw in text_lower for kw in ['criar', 'gerar', 'fazer']):
            intent = 'criar_codigo'
        elif any(kw in text_lower for kw in ['navegar', 'abrir', 'acessar']):
            intent = 'navegar_web'
        elif any(kw in text_lower for kw in ['testar', 'teste']):
            intent = 'executar_testes'
        else:
            intent = 'generico'

        # Entities
        entities = {}

        if 'fastapi' in text_lower:
            entities['framework'] = 'fastapi'
        if 'endpoint' in text_lower:
            entities['component'] = 'endpoint'
        if 'teste' in text_lower or 'test' in text_lower:
            entities['action'] = 'test'

        return intent, entities

    async def _get_context(self, task: str) -> List[Any]:
        """Busca conhecimento relevante"""
        if self.knowledge_bank:
            try:
                return await self.knowledge_bank.search(task, limit=3)
            except Exception as e:
                logger.error(f"KnowledgeBank search error: {e}")

        return []

    def _instantiate_template(
        self,
        template,
        task_description: str,
        intent: str,
        entities: Dict[str, Any]
    ) -> ExecutionPlan:
        """Instancia template com parâmetros específicos"""

        # Converte steps do template para ExecutionStep
        steps = []
        for step_data in template.steps:
            step = ExecutionStep(
                tool=step_data['tool'],
                action=step_data['action'],
                params=step_data.get('params', {}),
                is_critical=step_data.get('is_critical', False)
            )
            steps.append(step)

        return ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            description=task_description,
            steps=steps,
            estimated_cost=0.0,  # Template = custo zero!
            estimated_time=len(steps) * 2.0,
            metadata={
                'template_id': template.id,
                'from_template': True,
                'intent': intent
            }
        )

    async def _generate_with_ai(
        self,
        task: str,
        intent: str,
        entities: Dict[str, Any],
        context: List[Any]
    ) -> ExecutionPlan:
        """Gera plano usando IA"""

        if self.consensus_engine:
            try:
                # TODO: Chamar ConsensusEngine real
                pass
            except Exception as e:
                logger.error(f"ConsensusEngine error: {e}")

        # Fallback: Plano baseado em heurísticas
        return self._create_heuristic_plan(task, intent, entities)

    def _create_heuristic_plan(
        self,
        task: str,
        intent: str,
        entities: Dict[str, Any]
    ) -> ExecutionPlan:
        """Cria plano usando heurísticas"""

        steps = []

        if intent == 'criar_codigo':
            if entities.get('framework') == 'fastapi':
                steps = [
                    ExecutionStep('system', 'open_vscode', {'file': 'main.py'}),
                    ExecutionStep('ai', 'generate_code', {'template': 'fastapi_endpoint'}),
                    ExecutionStep('system', 'run_tests', {}, is_critical=True)
                ]

        elif intent == 'navegar_web':
            url = entities.get('url', 'https://google.com')
            steps = [
                ExecutionStep('browser', 'start', {'headless': False}),
                ExecutionStep('browser', 'navigate', {'url': url}),
                ExecutionStep('browser', 'screenshot', {'path': 'screenshot.png'}),
                ExecutionStep('browser', 'stop', {})
            ]

        elif intent == 'executar_testes':
            steps = [
                ExecutionStep('system', 'run_tests', {'path': 'tests/'}, is_critical=True)
            ]

        else:
            # Genérico
            steps = [
                ExecutionStep('system', 'echo', {'message': task})
            ]

        return ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            description=task,
            steps=steps,
            estimated_cost=0.02,  # Custo de IA
            estimated_time=len(steps) * 3.0,
            metadata={'intent': intent, 'from_heuristic': True}
        )

    def _create_generic_plan(
        self,
        task: str,
        intent: str,
        entities: Dict[str, Any]
    ) -> ExecutionPlan:
        """Cria plano genérico básico"""
        return ExecutionPlan(
            plan_id=str(uuid.uuid4()),
            description=task,
            steps=[
                ExecutionStep('generic', 'execute', {'task': task})
            ],
            estimated_cost=0.0,
            estimated_time=5.0,
            metadata={'intent': intent, 'generic': True}
        )

    async def save_successful_plan(
        self,
        task_description: str,
        intent: str,
        entities: Dict[str, Any],
        plan: ExecutionPlan
    ):
        """Salva plano bem-sucedido como template"""
        if self.template_manager:
            # Converte steps para formato serializável
            steps_data = [
                {
                    'tool': step.tool,
                    'action': step.action,
                    'params': step.params,
                    'is_critical': step.is_critical
                }
                for step in plan.steps
            ]

            await self.template_manager.save_successful_execution(
                task_description,
                intent,
                steps_data,
                entities
            )

            logger.info(f"Saved successful plan as template")
