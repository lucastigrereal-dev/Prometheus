"""
Health Checker - Sistema de verificação de saúde dos componentes
PRINCÍPIOS:
- Health checks independentes por componente
- Status: healthy, degraded, unhealthy
- Detalhes de erro quando unhealthy
- Agregação de status global
"""

from datetime import datetime
from typing import Dict, Any, Callable, Optional, List
from enum import Enum
import asyncio
import traceback

class HealthStatus(str, Enum):
    """Status de saúde possíveis"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

class HealthChecker:
    """Gerenciador de health checks"""

    def __init__(self):
        """Inicializa o health checker"""
        self.checks: Dict[str, Callable] = {}
        self.last_results: Dict[str, Dict[str, Any]] = {}
        self.start_time = datetime.now()

    def register_check(
        self,
        name: str,
        check_function: Callable,
        critical: bool = False
    ):
        """
        Registra um health check

        Args:
            name: Nome do componente
            check_function: Função que retorna dict com status e details
            critical: Se True, este check é crítico para o sistema
        """
        self.checks[name] = {
            'function': check_function,
            'critical': critical
        }

    async def run_check(self, name: str) -> Dict[str, Any]:
        """
        Executa um health check específico

        Args:
            name: Nome do check

        Returns:
            Dict com status e details
        """
        if name not in self.checks:
            return {
                'status': HealthStatus.UNKNOWN,
                'message': f'Check {name} não encontrado'
            }

        check = self.checks[name]
        start_time = datetime.now()

        try:
            # Executar check com timeout de 5 segundos
            if asyncio.iscoroutinefunction(check['function']):
                result = await asyncio.wait_for(
                    check['function'](),
                    timeout=5.0
                )
            else:
                result = check['function']()

            duration_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Validar resultado
            if not isinstance(result, dict) or 'status' not in result:
                raise ValueError("Check deve retornar dict com 'status'")

            # Adicionar metadados
            result['timestamp'] = datetime.now().isoformat()
            result['duration_ms'] = duration_ms
            result['critical'] = check['critical']

            # Salvar resultado
            self.last_results[name] = result

            return result

        except asyncio.TimeoutError:
            result = {
                'status': HealthStatus.UNHEALTHY,
                'message': f'Health check timeout após 5 segundos',
                'timestamp': datetime.now().isoformat(),
                'critical': check['critical']
            }
            self.last_results[name] = result
            return result

        except Exception as e:
            result = {
                'status': HealthStatus.UNHEALTHY,
                'message': f'Erro ao executar check: {str(e)}',
                'error': traceback.format_exc(),
                'timestamp': datetime.now().isoformat(),
                'critical': check['critical']
            }
            self.last_results[name] = result
            return result

    async def run_all_checks(self) -> Dict[str, Any]:
        """
        Executa todos os health checks

        Returns:
            Dict com status agregado e detalhes
        """
        results = {}

        # Executar todos os checks
        for name in self.checks.keys():
            results[name] = await self.run_check(name)

        # Calcular status global
        global_status = self._calculate_global_status(results)

        # Calcular uptime
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()

        return {
            'status': global_status,
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': uptime_seconds,
            'checks': results
        }

    def get_last_results(self) -> Dict[str, Dict[str, Any]]:
        """
        Retorna últimos resultados de checks (sem re-executar)

        Returns:
            Dict com últimos resultados
        """
        if not self.last_results:
            return {
                'status': HealthStatus.UNKNOWN,
                'message': 'Nenhum check executado ainda'
            }

        global_status = self._calculate_global_status(self.last_results)
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()

        return {
            'status': global_status,
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': uptime_seconds,
            'checks': self.last_results
        }

    def _calculate_global_status(self, results: Dict[str, Dict[str, Any]]) -> HealthStatus:
        """
        Calcula status global baseado em todos os checks

        Args:
            results: Resultados dos checks

        Returns:
            Status global
        """
        if not results:
            return HealthStatus.UNKNOWN

        statuses = []
        critical_unhealthy = False

        for name, result in results.items():
            status = result.get('status', HealthStatus.UNKNOWN)
            is_critical = result.get('critical', False)

            statuses.append(status)

            # Se um check crítico está unhealthy, sistema está unhealthy
            if is_critical and status == HealthStatus.UNHEALTHY:
                critical_unhealthy = True

        # Lógica de agregação
        if critical_unhealthy:
            return HealthStatus.UNHEALTHY

        if any(s == HealthStatus.UNHEALTHY for s in statuses):
            return HealthStatus.DEGRADED

        if any(s == HealthStatus.DEGRADED for s in statuses):
            return HealthStatus.DEGRADED

        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY

        return HealthStatus.UNKNOWN

    def get_unhealthy_checks(self) -> List[str]:
        """Retorna lista de checks unhealthy"""
        return [
            name for name, result in self.last_results.items()
            if result.get('status') == HealthStatus.UNHEALTHY
        ]

    def get_critical_checks(self) -> List[str]:
        """Retorna lista de checks críticos"""
        return [
            name for name, check in self.checks.items()
            if check.get('critical', False)
        ]


# Health check functions para componentes do Prometheus

def check_brain_memory() -> Dict[str, Any]:
    """Verifica saúde do módulo de memória"""
    try:
        from prometheus_v3.brain import memory_manager

        # Verificar se collections existem
        collections = memory_manager.list_collections()

        if not collections:
            return {
                'status': HealthStatus.DEGRADED,
                'message': 'Nenhuma collection encontrada',
                'collections_count': 0
            }

        return {
            'status': HealthStatus.HEALTHY,
            'message': 'Brain memory operacional',
            'collections_count': len(collections),
            'collections': collections[:5]  # Primeiras 5
        }

    except Exception as e:
        return {
            'status': HealthStatus.UNHEALTHY,
            'message': f'Erro ao verificar brain memory: {str(e)}'
        }


def check_task_manager() -> Dict[str, Any]:
    """Verifica saúde do task manager"""
    try:
        from prometheus_v3.tasks import task_manager

        # Verificar se task manager está inicializado
        stats = task_manager.get_task_stats()

        active_tasks = stats.get('active', 0)

        # Se há muitas tarefas ativas (> 50), pode estar sobrecarregado
        if active_tasks > 50:
            return {
                'status': HealthStatus.DEGRADED,
                'message': f'Sistema sobrecarregado com {active_tasks} tarefas ativas',
                **stats
            }

        return {
            'status': HealthStatus.HEALTHY,
            'message': 'Task manager operacional',
            **stats
        }

    except Exception as e:
        return {
            'status': HealthStatus.UNHEALTHY,
            'message': f'Erro ao verificar task manager: {str(e)}'
        }


def check_browser_executor() -> Dict[str, Any]:
    """Verifica saúde do browser executor"""
    try:
        from prometheus_v3.execution import browser_executor

        # Verificar se browser executor está disponível
        # (não vamos abrir o browser, apenas verificar se está importável)

        return {
            'status': HealthStatus.HEALTHY,
            'message': 'Browser executor disponível'
        }

    except Exception as e:
        return {
            'status': HealthStatus.DEGRADED,
            'message': f'Browser executor não disponível: {str(e)}'
        }


def check_supervisor() -> Dict[str, Any]:
    """Verifica saúde do supervisor"""
    try:
        from prometheus_v3.supervisor import code_reviewer, approval_manager

        # Verificar estatísticas
        review_stats = code_reviewer.get_review_stats()
        approval_stats = approval_manager.get_approval_stats()

        return {
            'status': HealthStatus.HEALTHY,
            'message': 'Supervisor operacional',
            'reviews_total': review_stats.get('total_reviews', 0),
            'approvals_pending': approval_stats.get('pending', 0)
        }

    except Exception as e:
        return {
            'status': HealthStatus.UNHEALTHY,
            'message': f'Erro ao verificar supervisor: {str(e)}'
        }


# Singleton global
health_checker = HealthChecker()

# Registrar checks padrão
health_checker.register_check('brain_memory', check_brain_memory, critical=True)
health_checker.register_check('task_manager', check_task_manager, critical=True)
health_checker.register_check('browser_executor', check_browser_executor, critical=False)
health_checker.register_check('supervisor', check_supervisor, critical=False)
