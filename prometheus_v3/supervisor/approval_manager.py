"""
Approval Manager - Gerencia aprovações de tarefas críticas
PRINCÍPIOS:
- Tarefas críticas requerem aprovação manual
- Sistema de aprovação/rejeição com motivo
- Histórico completo de decisões
- Timeout configurável
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json

class ApprovalManager:
    """Gerenciador de aprovações para tarefas críticas"""

    APPROVAL_STATUS = ['pending', 'approved', 'rejected', 'expired']

    def __init__(self, data_dir: str = "data/supervisor"):
        """
        Inicializa ApprovalManager

        Args:
            data_dir: Diretório para armazenar dados de aprovações
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.approvals_file = self.data_dir / "approvals.json"
        self.approvals = self._load_approvals()

    def _load_approvals(self) -> Dict[str, Dict[str, Any]]:
        """Carrega aprovações do arquivo"""
        if self.approvals_file.exists():
            try:
                with open(self.approvals_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erro ao carregar aprovações: {e}")
                return {}
        return {}

    def _save_approvals(self):
        """Salva aprovações no arquivo"""
        try:
            with open(self.approvals_file, 'w', encoding='utf-8') as f:
                json.dump(self.approvals, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar aprovações: {e}")

    def request_approval(
        self,
        task_id: str,
        task_description: str,
        task_action: str,
        task_params: Dict[str, Any],
        reason: str,
        timeout_minutes: int = 60,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Solicita aprovação para uma tarefa crítica

        Args:
            task_id: ID da tarefa
            task_description: Descrição da tarefa
            task_action: Ação a ser executada
            task_params: Parâmetros da ação
            reason: Motivo da aprovação
            timeout_minutes: Tempo limite para aprovação
            metadata: Metadados adicionais

        Returns:
            Dict com status da aprovação
        """
        approval_id = f"approval_{task_id}"

        # Verificar se já existe
        if approval_id in self.approvals:
            existing = self.approvals[approval_id]
            if existing['status'] == 'pending':
                return {
                    'approval_id': approval_id,
                    'status': 'pending',
                    'message': 'Aprovação já solicitada anteriormente'
                }

        # Calcular expiração
        created_at = datetime.now()
        expires_at = created_at + timedelta(minutes=timeout_minutes)

        # Criar registro de aprovação
        approval_record = {
            'approval_id': approval_id,
            'task_id': task_id,
            'task_description': task_description,
            'task_action': task_action,
            'task_params': task_params,
            'reason': reason,
            'status': 'pending',
            'created_at': created_at.isoformat(),
            'expires_at': expires_at.isoformat(),
            'timeout_minutes': timeout_minutes,
            'approved_at': None,
            'approved_by': None,
            'rejection_reason': None,
            'metadata': metadata or {}
        }

        self.approvals[approval_id] = approval_record
        self._save_approvals()

        return {
            'approval_id': approval_id,
            'status': 'pending',
            'expires_at': expires_at.isoformat(),
            'message': f'Aprovação solicitada. Expira em {timeout_minutes} minutos.'
        }

    def approve(
        self,
        approval_id: str,
        approved_by: str = "user",
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Aprova uma solicitação

        Args:
            approval_id: ID da aprovação
            approved_by: Quem aprovou
            notes: Notas adicionais

        Returns:
            Dict com resultado
        """
        if approval_id not in self.approvals:
            return {
                'success': False,
                'error': f'Aprovação {approval_id} não encontrada'
            }

        approval = self.approvals[approval_id]

        # Verificar status
        if approval['status'] != 'pending':
            return {
                'success': False,
                'error': f'Aprovação já foi {approval["status"]}'
            }

        # Verificar se expirou
        expires_at = datetime.fromisoformat(approval['expires_at'])
        if datetime.now() > expires_at:
            approval['status'] = 'expired'
            self._save_approvals()
            return {
                'success': False,
                'error': 'Solicitação de aprovação expirou'
            }

        # Aprovar
        approval['status'] = 'approved'
        approval['approved_at'] = datetime.now().isoformat()
        approval['approved_by'] = approved_by
        if notes:
            approval['approval_notes'] = notes

        self._save_approvals()

        return {
            'success': True,
            'approval_id': approval_id,
            'task_id': approval['task_id'],
            'message': 'Tarefa aprovada para execução'
        }

    def reject(
        self,
        approval_id: str,
        rejection_reason: str,
        rejected_by: str = "user"
    ) -> Dict[str, Any]:
        """
        Rejeita uma solicitação

        Args:
            approval_id: ID da aprovação
            rejection_reason: Motivo da rejeição
            rejected_by: Quem rejeitou

        Returns:
            Dict com resultado
        """
        if approval_id not in self.approvals:
            return {
                'success': False,
                'error': f'Aprovação {approval_id} não encontrada'
            }

        approval = self.approvals[approval_id]

        # Verificar status
        if approval['status'] != 'pending':
            return {
                'success': False,
                'error': f'Aprovação já foi {approval["status"]}'
            }

        # Rejeitar
        approval['status'] = 'rejected'
        approval['rejected_at'] = datetime.now().isoformat()
        approval['rejected_by'] = rejected_by
        approval['rejection_reason'] = rejection_reason

        self._save_approvals()

        return {
            'success': True,
            'approval_id': approval_id,
            'task_id': approval['task_id'],
            'message': 'Tarefa rejeitada'
        }

    def get_approval(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """
        Retorna detalhes de uma aprovação

        Args:
            approval_id: ID da aprovação

        Returns:
            Dict com detalhes ou None
        """
        return self.approvals.get(approval_id)

    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """
        Retorna todas as aprovações pendentes (não expiradas)

        Returns:
            Lista de aprovações pendentes
        """
        pending = []
        now = datetime.now()

        for approval_id, approval in self.approvals.items():
            if approval['status'] == 'pending':
                expires_at = datetime.fromisoformat(approval['expires_at'])

                # Verificar se expirou
                if now > expires_at:
                    approval['status'] = 'expired'
                    continue

                pending.append(approval)

        # Salvar se houver mudanças (expirações)
        self._save_approvals()

        return sorted(pending, key=lambda x: x['created_at'], reverse=True)

    def get_approval_history(
        self,
        limit: int = 10,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retorna histórico de aprovações

        Args:
            limit: Número máximo de resultados
            status: Filtrar por status (opcional)

        Returns:
            Lista de aprovações
        """
        approvals = list(self.approvals.values())

        # Filtrar por status se especificado
        if status:
            approvals = [a for a in approvals if a['status'] == status]

        # Ordenar por data de criação (mais recente primeiro)
        approvals.sort(key=lambda x: x['created_at'], reverse=True)

        return approvals[:limit]

    def get_approval_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas de aprovações

        Returns:
            Dict com estatísticas
        """
        total = len(self.approvals)
        pending = len([a for a in self.approvals.values() if a['status'] == 'pending'])
        approved = len([a for a in self.approvals.values() if a['status'] == 'approved'])
        rejected = len([a for a in self.approvals.values() if a['status'] == 'rejected'])
        expired = len([a for a in self.approvals.values() if a['status'] == 'expired'])

        # Calcular tempo médio de aprovação
        approval_times = []
        for approval in self.approvals.values():
            if approval['status'] == 'approved' and approval.get('approved_at'):
                created = datetime.fromisoformat(approval['created_at'])
                approved_time = datetime.fromisoformat(approval['approved_at'])
                delta = (approved_time - created).total_seconds() / 60  # minutos
                approval_times.append(delta)

        avg_approval_time = sum(approval_times) / len(approval_times) if approval_times else 0

        return {
            'total': total,
            'pending': pending,
            'approved': approved,
            'rejected': rejected,
            'expired': expired,
            'approval_rate': (approved / total * 100) if total > 0 else 0,
            'avg_approval_time_minutes': round(avg_approval_time, 2)
        }

    def cleanup_expired(self, days: int = 7) -> int:
        """
        Remove aprovações expiradas antigas

        Args:
            days: Remover aprovações expiradas há mais de X dias

        Returns:
            Número de aprovações removidas
        """
        cutoff = datetime.now() - timedelta(days=days)
        to_remove = []

        for approval_id, approval in self.approvals.items():
            if approval['status'] == 'expired':
                created = datetime.fromisoformat(approval['created_at'])
                if created < cutoff:
                    to_remove.append(approval_id)

        for approval_id in to_remove:
            del self.approvals[approval_id]

        if to_remove:
            self._save_approvals()

        return len(to_remove)
