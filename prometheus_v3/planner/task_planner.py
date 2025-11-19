"""
Task Planner - Orquestra o processo de planejamento
Combina Knowledge Query + AI Plan Generation
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
from .knowledge_query import KnowledgeQuery
from .plan_generator import PlanGenerator

class TaskPlanner:
    """
    Planner principal que:
    1. Recebe requisição do usuário
    2. Busca contexto no Knowledge Brain
    3. Usa IA para gerar plano de ação
    4. Retorna plano estruturado para o Executor
    """

    def __init__(self, supabase_client=None, openai_api_key: Optional[str] = None):
        self.knowledge_query = KnowledgeQuery(supabase_client)
        self.plan_generator = PlanGenerator(openai_api_key)
        self.planning_history = []

    def create_plan(
        self,
        user_request: str,
        context: Optional[Dict[str, Any]] = None,
        max_knowledge_results: int = 5
    ) -> Dict[str, Any]:
        """
        Cria um plano de ação baseado em requisição do usuário

        Args:
            user_request: O que o usuário quer fazer (linguagem natural)
            context: Contexto adicional (opcional)
            max_knowledge_results: Quantos resultados buscar no Knowledge Brain

        Returns:
            Dict com plano estruturado
        """
        plan_id = f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Passo 1: Buscar conhecimento relevante
        knowledge_results = self.knowledge_query.search_relevant_knowledge(
            query=user_request,
            limit=max_knowledge_results
        )

        # Passo 2: Gerar plano com IA
        plan = self.plan_generator.generate_plan(
            user_request=user_request,
            knowledge_context=knowledge_results,
            additional_context=context
        )

        # Passo 3: Estruturar resultado
        structured_plan = {
            'plan_id': plan_id,
            'user_request': user_request,
            'created_at': datetime.now().isoformat(),
            'knowledge_used': {
                'count': len(knowledge_results),
                'sources': [r['source_type'] for r in knowledge_results],
                'top_similarity': knowledge_results[0]['similarity'] if knowledge_results else 0
            },
            'plan': plan,
            'status': 'ready',  # ready, executing, completed, failed
            'executor_tasks': []  # Será preenchido quando converter para tarefas
        }

        # Salvar no histórico
        self.planning_history.append(structured_plan)

        return structured_plan

    def plan_to_executor_tasks(self, plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Converte um plano em tarefas prontas para o Executor

        Args:
            plan: Plano gerado pelo create_plan()

        Returns:
            Lista de tarefas no formato do Executor
        """
        tasks = []

        # Extrair steps do plano
        steps = plan['plan'].get('steps', [])

        for step in steps:
            # Tentar mapear step para ação do Executor
            task = self._map_step_to_task(step)

            if task:
                tasks.append(task)

        return tasks

    def _map_step_to_task(self, step: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Mapeia um step do plano para uma tarefa do Executor

        Args:
            step: Step do plano gerado pela IA

        Returns:
            Task dict ou None se não mapear
        """
        # Extrair ação e parâmetros do step
        action_text = step.get('action', '').lower()

        # Mapeamento simples (será expandido)
        action_mapping = {
            'listar arquivos': ('list_files', {'path': step.get('params', {}).get('path', '.')}),
            'organizar downloads': ('organize_downloads', {'dry_run': True}),
            'info sistema': ('get_system_info', {}),
            'ler arquivo': ('read_file_info', {'path': step.get('params', {}).get('path')}),
            'criar pasta': ('create_directory', {'path': step.get('params', {}).get('path')}),
        }

        # Buscar match
        for key, (action, params) in action_mapping.items():
            if key in action_text:
                return {
                    'action': action,
                    'params': params,
                    'description': step.get('description', action),
                    'critical': step.get('critical', False)
                }

        # Se não mapear, retornar None (step precisa de ação manual)
        return None

    def get_planning_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna histórico de planejamentos"""
        return self.planning_history[-limit:]
