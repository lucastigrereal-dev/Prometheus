"""
PROMETHEUS CORE - O Núcleo do Sistema Autônomo
Arquiteto: Cláudio Opus
Versão: 1.0.0 Supreme
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import uuid
from abc import ABC, abstractmethod

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='🔥 %(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('PROMETHEUS')

# ============================================================================
# ESTRUTURAS DE DADOS FUNDAMENTAIS
# ============================================================================

class TaskStatus(Enum):
    """Status possíveis de uma tarefa"""
    PENDING = "pending"
    ANALYZING = "analyzing"
    PLANNING = "planning"
    EXECUTING = "executing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

class Priority(Enum):
    """Níveis de prioridade"""
    CRITICAL = 1  # Execução imediata
    HIGH = 2      # Próximo da fila
    NORMAL = 3    # Fila normal
    LOW = 4       # Quando possível
    BACKGROUND = 5 # Em idle

class AIProvider(Enum):
    """Provedores de IA disponíveis"""
    CLAUDE = "claude"
    GPT4 = "gpt-4"
    PERPLEXITY = "perplexity"
    GROK = "grok"
    GEMINI = "gemini"
    LOCAL = "local"

@dataclass
class Task:
    """Representa uma tarefa no sistema"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""
    raw_command: str = ""
    priority: Priority = Priority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    subtasks: List['Task'] = field(default_factory=list)
    parent_id: Optional[str] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        """Serializa a tarefa para dict"""
        return {
            'id': self.id,
            'description': self.description,
            'priority': self.priority.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'context': self.context,
            'subtasks': [st.id for st in self.subtasks],
            'parent_id': self.parent_id,
            'result': self.result,
            'retry_count': self.retry_count
        }

@dataclass
class ExecutionPlan:
    """Plano de execução para uma tarefa"""
    task_id: str
    steps: List[Dict[str, Any]]
    dependencies: Dict[str, List[str]]  # task_id -> [dependency_ids]
    estimated_time: float  # segundos
    required_resources: List[str]
    ai_assignments: Dict[str, AIProvider]  # step_id -> AI provider
    fallback_strategies: List[Dict[str, Any]]
    
    def get_execution_order(self) -> List[str]:
        """Retorna ordem topológica de execução"""
        # Implementação simplificada - seria Kahn's algorithm completo
        return list(self.dependencies.keys())

@dataclass
class AIResponse:
    """Resposta de um provedor de IA"""
    provider: AIProvider
    content: str
    confidence: float  # 0.0 a 1.0
    tokens_used: int
    latency: float  # segundos
    metadata: Dict[str, Any] = field(default_factory=dict)

# ============================================================================
# INTERFACES BASE (Contratos)
# ============================================================================

class Component(ABC):
    """Interface base para todos os componentes"""
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Inicializa o componente"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Desliga o componente gracefully"""
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do componente"""
        pass

# ============================================================================
# EVENT BUS - Sistema de Eventos
# ============================================================================

class EventBus:
    """Sistema de eventos para comunicação entre componentes"""
    
    def __init__(self):
        self._subscribers: Dict[str, List[callable]] = {}
        self._event_history: List[Dict] = []
        self._max_history = 1000
    
    def subscribe(self, event_type: str, callback: callable) -> None:
        """Inscreve um callback para um tipo de evento"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed {callback.__name__} to {event_type}")
    
    async def emit(self, event_type: str, data: Any = None) -> None:
        """Emite um evento para todos os subscribers"""
        event = {
            'type': event_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        # Adiciona ao histórico
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history.pop(0)
        
        # Notifica subscribers
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    logger.error(f"Error in event handler {callback.__name__}: {e}")
    
    def get_history(self, event_type: Optional[str] = None) -> List[Dict]:
        """Retorna histórico de eventos"""
        if event_type:
            return [e for e in self._event_history if e['type'] == event_type]
        return self._event_history

# ============================================================================
# TASK ANALYZER - Analisador de Tarefas
# ============================================================================

class TaskAnalyzer(Component):
    """Analisa comandos em linguagem natural e extrai intenção"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.patterns = self._load_patterns()
        
    async def initialize(self) -> bool:
        """Inicializa o analisador"""
        logger.info("TaskAnalyzer initialized")
        return True
    
    async def shutdown(self) -> None:
        """Desliga o analisador"""
        logger.info("TaskAnalyzer shutdown")
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do analisador"""
        return {
            'status': 'healthy',
            'patterns_loaded': len(self.patterns),
            'timestamp': datetime.now().isoformat()
        }
    
    def _load_patterns(self) -> Dict[str, List[str]]:
        """Carrega padrões de reconhecimento"""
        return {
            'create_website': [
                'cria um site', 'criar site', 'fazer site', 
                'desenvolver site', 'montar site'
            ],
            'send_message': [
                'enviar mensagem', 'mandar mensagem', 'enviar email',
                'mandar whatsapp', 'enviar whatsapp'
            ],
            'analyze_data': [
                'analisar dados', 'análise de', 'verificar métricas',
                'relatório de', 'dashboard de'
            ],
            'automate_process': [
                'automatizar', 'criar automação', 'fazer bot',
                'rotina automática', 'processo automático'
            ],
            'research': [
                'pesquisar', 'buscar sobre', 'encontrar informação',
                'procurar sobre', 'descobrir'
            ]
        }
    
    async def analyze(self, command: str) -> Task:
        """Analisa um comando e retorna uma Task estruturada"""
        await self.event_bus.emit('task_analysis_started', {'command': command})
        
        task = Task(
            raw_command=command,
            description=self._extract_description(command),
            priority=self._determine_priority(command),
            context=await self._extract_context(command)
        )
        
        # Decomposição em subtarefas
        task.subtasks = await self._decompose(command, task)
        
        await self.event_bus.emit('task_analysis_completed', task.to_dict())
        
        return task
    
    def _extract_description(self, command: str) -> str:
        """Extrai descrição limpa do comando"""
        # Simplificado - seria NLP avançado
        return command.strip().capitalize()
    
    def _determine_priority(self, command: str) -> Priority:
        """Determina prioridade baseado no comando"""
        urgent_keywords = ['urgente', 'agora', 'imediato', 'crítico']
        high_keywords = ['importante', 'prioridade', 'hoje']
        
        command_lower = command.lower()
        
        if any(keyword in command_lower for keyword in urgent_keywords):
            return Priority.CRITICAL
        elif any(keyword in command_lower for keyword in high_keywords):
            return Priority.HIGH
        else:
            return Priority.NORMAL
    
    async def _extract_context(self, command: str) -> Dict[str, Any]:
        """Extrai contexto relevante do comando"""
        context = {
            'original_command': command,
            'timestamp': datetime.now().isoformat(),
            'detected_intents': [],
            'entities': [],
            'confidence': 0.0
        }
        
        # Detecção de intenções
        for intent, patterns in self.patterns.items():
            if any(pattern in command.lower() for pattern in patterns):
                context['detected_intents'].append(intent)
        
        # Extração de entidades (simplificada)
        # Seria com NER (Named Entity Recognition)
        if '@' in command:
            emails = [word for word in command.split() if '@' in word]
            context['entities'].extend([{'type': 'email', 'value': e} for e in emails])
        
        context['confidence'] = 0.85 if context['detected_intents'] else 0.3
        
        return context
    
    async def _decompose(self, command: str, parent_task: Task) -> List[Task]:
        """Decompõe tarefa em subtarefas menores"""
        subtasks = []
        
        # Exemplo de decomposição para "criar site"
        if 'create_website' in parent_task.context.get('detected_intents', []):
            subtasks = [
                Task(
                    description="Analisar requisitos do site",
                    parent_id=parent_task.id,
                    priority=parent_task.priority
                ),
                Task(
                    description="Criar estrutura de páginas",
                    parent_id=parent_task.id,
                    priority=parent_task.priority
                ),
                Task(
                    description="Desenvolver design responsivo",
                    parent_id=parent_task.id,
                    priority=parent_task.priority
                ),
                Task(
                    description="Configurar SEO básico",
                    parent_id=parent_task.id,
                    priority=parent_task.priority
                ),
                Task(
                    description="Deploy e testes",
                    parent_id=parent_task.id,
                    priority=parent_task.priority
                )
            ]
        
        return subtasks

# ============================================================================
# EXECUTION PLANNER - Planejador de Execução
# ============================================================================

class ExecutionPlanner(Component):
    """Cria planos de execução detalhados para tarefas"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.strategies = {}
        
    async def initialize(self) -> bool:
        """Inicializa o planejador"""
        logger.info("ExecutionPlanner initialized")
        return True
    
    async def shutdown(self) -> None:
        """Desliga o planejador"""
        logger.info("ExecutionPlanner shutdown")
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do planejador"""
        return {
            'status': 'healthy',
            'strategies_loaded': len(self.strategies),
            'timestamp': datetime.now().isoformat()
        }
    
    async def create_plan(self, task: Task) -> ExecutionPlan:
        """Cria plano de execução para uma tarefa"""
        await self.event_bus.emit('planning_started', task.to_dict())
        
        plan = ExecutionPlan(
            task_id=task.id,
            steps=await self._generate_steps(task),
            dependencies=self._analyze_dependencies(task),
            estimated_time=self._estimate_time(task),
            required_resources=self._identify_resources(task),
            ai_assignments=await self._assign_ais(task),
            fallback_strategies=self._create_fallbacks(task)
        )
        
        await self.event_bus.emit('planning_completed', {
            'task_id': task.id,
            'steps_count': len(plan.steps),
            'estimated_time': plan.estimated_time
        })
        
        return plan
    
    async def _generate_steps(self, task: Task) -> List[Dict[str, Any]]:
        """Gera passos de execução"""
        steps = []
        
        # Para cada subtarefa, cria um step
        for i, subtask in enumerate(task.subtasks):
            step = {
                'id': f"step_{i+1}",
                'task_id': subtask.id,
                'description': subtask.description,
                'type': self._determine_step_type(subtask),
                'parameters': {},
                'timeout': 300,  # 5 minutos padrão
                'retry_on_failure': True
            }
            steps.append(step)
        
        # Se não tem subtarefas, cria step único
        if not steps:
            steps.append({
                'id': 'step_1',
                'task_id': task.id,
                'description': task.description,
                'type': 'execute',
                'parameters': task.context,
                'timeout': 600,
                'retry_on_failure': True
            })
        
        return steps
    
    def _determine_step_type(self, task: Task) -> str:
        """Determina tipo de step baseado na tarefa"""
        description = task.description.lower()
        
        if 'analisar' in description or 'análise' in description:
            return 'analyze'
        elif 'criar' in description or 'desenvolver' in description:
            return 'create'
        elif 'enviar' in description or 'mandar' in description:
            return 'send'
        elif 'buscar' in description or 'pesquisar' in description:
            return 'search'
        else:
            return 'execute'
    
    def _analyze_dependencies(self, task: Task) -> Dict[str, List[str]]:
        """Analisa dependências entre passos"""
        dependencies = {}
        
        # Simplificado - assume execução sequencial
        for i, subtask in enumerate(task.subtasks):
            if i == 0:
                dependencies[subtask.id] = []
            else:
                dependencies[subtask.id] = [task.subtasks[i-1].id]
        
        return dependencies
    
    def _estimate_time(self, task: Task) -> float:
        """Estima tempo de execução em segundos"""
        base_time = 60  # 1 minuto base
        
        # Adiciona tempo por subtarefa
        subtask_time = len(task.subtasks) * 30
        
        # Adiciona tempo por complexidade
        if task.priority == Priority.CRITICAL:
            complexity_time = 120  # Tarefas críticas são geralmente mais complexas
        else:
            complexity_time = 60
        
        return base_time + subtask_time + complexity_time
    
    def _identify_resources(self, task: Task) -> List[str]:
        """Identifica recursos necessários"""
        resources = []
        
        intents = task.context.get('detected_intents', [])
        
        if 'create_website' in intents:
            resources.extend(['browser', 'file_system', 'api'])
        elif 'send_message' in intents:
            resources.extend(['whatsapp_api', 'email_api'])
        elif 'analyze_data' in intents:
            resources.extend(['database', 'analytics_api'])
        
        return list(set(resources))  # Remove duplicatas
    
    async def _assign_ais(self, task: Task) -> Dict[str, AIProvider]:
        """Atribui IAs para cada passo"""
        assignments = {}
        
        for subtask in task.subtasks:
            # Lógica de atribuição baseada no tipo de tarefa
            if 'analis' in subtask.description.lower():
                assignments[subtask.id] = AIProvider.CLAUDE
            elif 'criar' in subtask.description.lower():
                assignments[subtask.id] = AIProvider.GPT4
            elif 'pesquis' in subtask.description.lower():
                assignments[subtask.id] = AIProvider.PERPLEXITY
            else:
                assignments[subtask.id] = AIProvider.GEMINI
        
        return assignments
    
    def _create_fallbacks(self, task: Task) -> List[Dict[str, Any]]:
        """Cria estratégias de fallback"""
        fallbacks = [
            {
                'condition': 'timeout',
                'action': 'retry_with_simpler_approach',
                'max_attempts': 3
            },
            {
                'condition': 'api_error',
                'action': 'switch_provider',
                'max_attempts': 2
            },
            {
                'condition': 'validation_failed',
                'action': 'request_human_intervention',
                'max_attempts': 1
            }
        ]
        
        return fallbacks

# ============================================================================
# AI ORCHESTRATOR - Orquestrador de IAs
# ============================================================================

class AIOrchestrator(Component):
    """Orquestra múltiplos provedores de IA"""
    
    def __init__(self, event_bus: EventBus):
        self.event_bus = event_bus
        self.providers = {}
        self.load_balancer = LoadBalancer()
        self.consensus_engine = ConsensusEngine()
        
    async def initialize(self) -> bool:
        """Inicializa o orquestrador"""
        # Aqui carregaria os providers reais
        logger.info("AIOrchestrator initialized")
        return True
    
    async def shutdown(self) -> None:
        """Desliga o orquestrador"""
        for provider in self.providers.values():
            await provider.shutdown()
        logger.info("AIOrchestrator shutdown")
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do orquestrador"""
        provider_status = {}
        for name, provider in self.providers.items():
            provider_status[name] = provider.health_check()
        
        return {
            'status': 'healthy',
            'providers': provider_status,
            'timestamp': datetime.now().isoformat()
        }
    
    async def execute_with_ai(
        self,
        task: Task,
        provider: AIProvider,
        require_consensus: bool = False
    ) -> AIResponse:
        """Executa tarefa com IA específica ou múltiplas"""
        
        await self.event_bus.emit('ai_execution_started', {
            'task_id': task.id,
            'provider': provider.value,
            'consensus': require_consensus
        })
        
        if require_consensus:
            response = await self._execute_with_consensus(task)
        else:
            response = await self._execute_single(task, provider)
        
        await self.event_bus.emit('ai_execution_completed', {
            'task_id': task.id,
            'response_length': len(response.content),
            'confidence': response.confidence
        })
        
        return response
    
    async def _execute_single(self, task: Task, provider: AIProvider) -> AIResponse:
        """Executa com um único provider"""
        # Simulação - seria chamada real para API
        import random
        
        response = AIResponse(
            provider=provider,
            content=f"Executando '{task.description}' com {provider.value}",
            confidence=random.uniform(0.7, 0.95),
            tokens_used=random.randint(100, 1000),
            latency=random.uniform(0.5, 2.0)
        )
        
        return response
    
    async def _execute_with_consensus(self, task: Task) -> AIResponse:
        """Executa com múltiplos providers e busca consenso"""
        providers_to_use = [AIProvider.CLAUDE, AIProvider.GPT4, AIProvider.GEMINI]
        
        responses = []
        for provider in providers_to_use:
            response = await self._execute_single(task, provider)
            responses.append(response)
        
        # Motor de consenso decide a melhor resposta
        final_response = self.consensus_engine.decide(responses)
        
        return final_response

class LoadBalancer:
    """Balanceador de carga entre providers"""
    
    def select_provider(self, task: Task) -> AIProvider:
        """Seleciona melhor provider para a tarefa"""
        # Lógica simplificada
        return AIProvider.CLAUDE

class ConsensusEngine:
    """Motor de consenso entre respostas de IAs"""
    
    def decide(self, responses: List[AIResponse]) -> AIResponse:
        """Decide melhor resposta ou cria síntese"""
        # Simplificado - pega a de maior confiança
        return max(responses, key=lambda r: r.confidence)

# ============================================================================
# PROMETHEUS CORE - O Núcleo Central
# ============================================================================

class PrometheusCore:
    """
    Núcleo central do Prometheus - O Jarvis Real
    Orquestra todos os componentes e gerencia o ciclo de vida
    """
    
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.name = "PROMETHEUS"
        self.version = "1.0.0-supreme"
        self.status = "initializing"
        
        # Event Bus central
        self.event_bus = EventBus()
        
        # Componentes principais
        self.task_analyzer = TaskAnalyzer(self.event_bus)
        self.execution_planner = ExecutionPlanner(self.event_bus)
        self.ai_orchestrator = AIOrchestrator(self.event_bus)
        
        # Filas de execução
        self.task_queue: List[Task] = []
        self.active_tasks: Dict[str, Task] = {}
        self.completed_tasks: List[Task] = []
        
        # Configurações
        self.max_concurrent_tasks = 5
        self.shutdown_flag = False
        
        logger.info(f"🚀 {self.name} v{self.version} initialized")
    
    async def initialize(self) -> bool:
        """Inicializa todos os componentes"""
        try:
            logger.info("Initializing Prometheus Core...")
            
            # Inicializa componentes
            await self.task_analyzer.initialize()
            await self.execution_planner.initialize()
            await self.ai_orchestrator.initialize()
            
            # Registra event handlers
            self._register_event_handlers()
            
            self.status = "ready"
            await self.event_bus.emit('core_initialized', {
                'id': self.id,
                'version': self.version
            })
            
            logger.info("✅ Prometheus Core ready for operation")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize: {e}")
            self.status = "error"
            return False
    
    def _register_event_handlers(self):
        """Registra handlers para eventos do sistema"""
        self.event_bus.subscribe('task_completed', self._on_task_completed)
        self.event_bus.subscribe('task_failed', self._on_task_failed)
        self.event_bus.subscribe('system_shutdown', self._on_shutdown_request)
    
    async def execute_command(self, command: str) -> Dict[str, Any]:
        """
        Ponto de entrada principal - Recebe comando em linguagem natural
        e executa completamente
        """
        logger.info(f"📥 Received command: {command}")
        
        try:
            # 1. Analisa o comando
            task = await self.task_analyzer.analyze(command)
            logger.info(f"✅ Task analyzed: {task.id} - {task.description}")
            
            # 2. Cria plano de execução
            plan = await self.execution_planner.create_plan(task)
            logger.info(f"📋 Execution plan created with {len(plan.steps)} steps")
            
            # 3. Adiciona à fila
            self.task_queue.append(task)
            
            # 4. Processa a fila
            result = await self._process_task(task, plan)
            
            return {
                'success': result['success'],
                'task_id': task.id,
                'result': result.get('data'),
                'error': result.get('error'),
                'execution_time': result.get('execution_time')
            }
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _process_task(self, task: Task, plan: ExecutionPlan) -> Dict[str, Any]:
        """Processa uma tarefa seguindo o plano"""
        start_time = datetime.now()
        task.status = TaskStatus.EXECUTING
        self.active_tasks[task.id] = task
        
        try:
            result_data = {}
            
            # Executa cada passo do plano
            for step in plan.steps:
                logger.info(f"🔧 Executing step: {step['description']}")
                
                # Determina qual IA usar
                ai_provider = plan.ai_assignments.get(
                    step['task_id'],
                    AIProvider.CLAUDE
                )
                
                # Obtém subtarefa correspondente
                subtask = next(
                    (st for st in task.subtasks if st.id == step['task_id']),
                    task
                )
                
                # Executa com IA
                ai_response = await self.ai_orchestrator.execute_with_ai(
                    subtask,
                    ai_provider,
                    require_consensus=task.priority == Priority.CRITICAL
                )
                
                result_data[step['id']] = {
                    'description': step['description'],
                    'response': ai_response.content,
                    'confidence': ai_response.confidence
                }
                
                # Simula delay entre passos
                await asyncio.sleep(0.5)
            
            # Marca como completa
            task.status = TaskStatus.COMPLETED
            task.result = result_data
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            await self.event_bus.emit('task_completed', task.to_dict())
            
            return {
                'success': True,
                'data': result_data,
                'execution_time': execution_time
            }
            
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            
            await self.event_bus.emit('task_failed', task.to_dict())
            
            return {
                'success': False,
                'error': str(e),
                'execution_time': (datetime.now() - start_time).total_seconds()
            }
        
        finally:
            # Remove das tarefas ativas
            self.active_tasks.pop(task.id, None)
            self.completed_tasks.append(task)
    
    async def _on_task_completed(self, event: Dict):
        """Handler para tarefa completada"""
        logger.info(f"✅ Task {event['data']['id']} completed successfully")
    
    async def _on_task_failed(self, event: Dict):
        """Handler para tarefa falhada"""
        task_data = event['data']
        logger.error(f"❌ Task {task_data['id']} failed: {task_data.get('error')}")
        
        # Tenta retry se possível
        if task_data['retry_count'] < 3:
            logger.info(f"🔄 Retrying task {task_data['id']}...")
            # Implementar lógica de retry
    
    async def _on_shutdown_request(self, event: Dict):
        """Handler para requisição de shutdown"""
        logger.info("🛑 Shutdown requested")
        self.shutdown_flag = True
    
    async def shutdown(self):
        """Desliga o sistema gracefully"""
        logger.info("Shutting down Prometheus Core...")
        
        # Aguarda tarefas ativas
        while self.active_tasks:
            logger.info(f"Waiting for {len(self.active_tasks)} active tasks...")
            await asyncio.sleep(1)
        
        # Desliga componentes
        await self.task_analyzer.shutdown()
        await self.execution_planner.shutdown()
        await self.ai_orchestrator.shutdown()
        
        self.status = "shutdown"
        logger.info("✅ Prometheus Core shutdown complete")
    
    def get_status(self) -> Dict[str, Any]:
        """Retorna status completo do sistema"""
        return {
            'id': self.id,
            'name': self.name,
            'version': self.version,
            'status': self.status,
            'active_tasks': len(self.active_tasks),
            'queued_tasks': len(self.task_queue),
            'completed_tasks': len(self.completed_tasks),
            'components': {
                'analyzer': self.task_analyzer.health_check(),
                'planner': self.execution_planner.health_check(),
                'orchestrator': self.ai_orchestrator.health_check()
            },
            'timestamp': datetime.now().isoformat()
        }

# ============================================================================
# MAIN - Ponto de Entrada
# ============================================================================

async def main():
    """Função principal para testes"""
    
    # Cria e inicializa o core
    prometheus = PrometheusCore()
    await prometheus.initialize()
    
    # Exemplos de comandos
    test_commands = [
        "Cria um site para o cliente ABC com landing page e formulário de contato",
        "Enviar mensagem urgente para todos os clientes sobre nova promoção",
        "Analisar dados de vendas do último mês e criar relatório"
    ]
    
    # Executa comandos de teste
    for command in test_commands:
        print(f"\n{'='*60}")
        print(f"Executing: {command}")
        print('='*60)
        
        result = await prometheus.execute_command(command)
        
        if result['success']:
            print(f"✅ Success! Task ID: {result['task_id']}")
            print(f"Execution time: {result.get('execution_time', 0):.2f} seconds")
        else:
            print(f"❌ Failed: {result.get('error')}")
    
    # Status final
    print(f"\n{'='*60}")
    print("SYSTEM STATUS")
    print('='*60)
    status = prometheus.get_status()
    print(json.dumps(status, indent=2))
    
    # Shutdown
    await prometheus.shutdown()

if __name__ == "__main__":
    # Roda o sistema
    asyncio.run(main())
