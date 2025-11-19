"""
Task Manager - Gerencia tarefas do Executor
Mantém estado, histórico e permite consultas
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import uuid
import json
from pathlib import Path

class TaskManager:
    """Gerenciador de tarefas do Executor"""

    def __init__(self, storage_path: Optional[str] = None):
        if storage_path:
            self.storage_path = Path(storage_path)
        else:
            self.storage_path = Path(__file__).parent.parent.parent / 'data' / 'executor'

        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.tasks: Dict[str, Dict] = {}
        self._load_tasks()

    def create_task(
        self,
        action: str,
        params: Dict[str, Any],
        description: Optional[str] = None,
        critical: bool = False
    ) -> str:
        """
        Cria uma nova tarefa

        Args:
            action: Ação a executar
            params: Parâmetros da ação
            description: Descrição legível da tarefa
            critical: Se True, requer aprovação antes de executar

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())[:8]

        task = {
            'id': task_id,
            'action': action,
            'params': params,
            'description': description or f'Executar {action}',
            'critical': critical,
            'status': 'pending',  # pending, running, completed, failed, cancelled
            'created_at': datetime.now().isoformat(),
            'started_at': None,
            'completed_at': None,
            'result': None,
            'error': None,
            'logs': []
        }

        self.tasks[task_id] = task
        self._save_tasks()

        return task_id

    def get_task(self, task_id: str) -> Optional[Dict]:
        """Retorna uma tarefa pelo ID"""
        return self.tasks.get(task_id)

    def update_task_status(
        self,
        task_id: str,
        status: str,
        result: Optional[Any] = None,
        error: Optional[str] = None
    ):
        """Atualiza status de uma tarefa"""
        if task_id not in self.tasks:
            raise ValueError(f'Tarefa {task_id} não encontrada')

        task = self.tasks[task_id]
        task['status'] = status

        if status == 'running' and not task['started_at']:
            task['started_at'] = datetime.now().isoformat()

        if status in ['completed', 'failed', 'cancelled']:
            task['completed_at'] = datetime.now().isoformat()

        if result is not None:
            task['result'] = result

        if error is not None:
            task['error'] = error

        self._save_tasks()

    def add_task_log(self, task_id: str, message: str, level: str = 'info'):
        """Adiciona log a uma tarefa"""
        if task_id not in self.tasks:
            raise ValueError(f'Tarefa {task_id} não encontrada')

        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message
        }

        self.tasks[task_id]['logs'].append(log_entry)
        self._save_tasks()

    def get_all_tasks(self, status: Optional[str] = None) -> List[Dict]:
        """
        Retorna todas as tarefas

        Args:
            status: Filtrar por status (opcional)
        """
        tasks = list(self.tasks.values())

        if status:
            tasks = [t for t in tasks if t['status'] == status]

        # Ordenar por data de criação (mais recente primeiro)
        tasks.sort(key=lambda t: t['created_at'], reverse=True)

        return tasks

    def get_task_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de tarefas"""
        all_tasks = list(self.tasks.values())

        return {
            'total': len(all_tasks),
            'pending': len([t for t in all_tasks if t['status'] == 'pending']),
            'running': len([t for t in all_tasks if t['status'] == 'running']),
            'completed': len([t for t in all_tasks if t['status'] == 'completed']),
            'failed': len([t for t in all_tasks if t['status'] == 'failed']),
            'cancelled': len([t for t in all_tasks if t['status'] == 'cancelled']),
            'critical_pending': len([t for t in all_tasks if t['critical'] and t['status'] == 'pending'])
        }

    def _save_tasks(self):
        """Salva tarefas em arquivo"""
        tasks_file = self.storage_path / 'tasks.json'

        with open(tasks_file, 'w', encoding='utf-8') as f:
            json.dump(self.tasks, f, indent=2, ensure_ascii=False)

    def _load_tasks(self):
        """Carrega tarefas do arquivo"""
        tasks_file = self.storage_path / 'tasks.json'

        if tasks_file.exists():
            try:
                with open(tasks_file, 'r', encoding='utf-8') as f:
                    self.tasks = json.load(f)
            except Exception as e:
                print(f'Erro ao carregar tarefas: {e}')
                self.tasks = {}
