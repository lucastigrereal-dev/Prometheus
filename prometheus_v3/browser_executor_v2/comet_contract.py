"""
Comet Contract
Contratos de comunicação com Comet (agente de navegador)
"""

import json
from pathlib import Path
from typing import Optional, Any, List
from dataclasses import dataclass, asdict, field
from datetime import datetime
import logging

from .browser_action_schema import ActionSchema, ActionType

logger = logging.getLogger("prometheus.comet_contract")


@dataclass
class CometAction:
    """
    Ação individual para Comet
    """
    action: ActionSchema
    description: str = ""
    critical: bool = False
    retry_on_fail: bool = False
    max_retries: int = 3

    def to_dict(self) -> dict[str, Any]:
        return {
            "action": self.action.to_dict(),
            "description": self.description,
            "critical": self.critical,
            "retry_on_fail": self.retry_on_fail,
            "max_retries": self.max_retries
        }


@dataclass
class CometFlow:
    """
    Flow de ações para Comet (sequência de ações)
    """
    flow_id: str
    name: str
    description: str
    actions: List[CometAction] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_action(self, action: CometAction) -> 'CometFlow':
        """Adiciona ação ao flow"""
        self.actions.append(action)
        return self

    def to_dict(self) -> dict[str, Any]:
        return {
            "flow_id": self.flow_id,
            "name": self.name,
            "description": self.description,
            "actions": [a.to_dict() for a in self.actions],
            "created_at": self.created_at,
            "metadata": self.metadata
        }

    def to_json(self) -> str:
        """Converte flow para JSON"""
        return json.dumps(self.to_dict(), indent=2)

    def save_to_file(self, file_path: str | Path) -> bool:
        """
        Salva flow em arquivo JSON

        Args:
            file_path: Caminho do arquivo

        Returns:
            True se salvo com sucesso
        """
        try:
            path = Path(file_path)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, 'w', encoding='utf-8') as f:
                f.write(self.to_json())

            logger.info(f"Flow salvo: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Erro ao salvar flow: {e}")
            return False

    @classmethod
    def load_from_file(cls, file_path: str | Path) -> Optional['CometFlow']:
        """
        Carrega flow de arquivo JSON

        Args:
            file_path: Caminho do arquivo

        Returns:
            CometFlow ou None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Reconstruir ações
            actions = []
            for action_data in data.get("actions", []):
                action_schema = ActionSchema(**action_data["action"])
                comet_action = CometAction(
                    action=action_schema,
                    description=action_data.get("description", ""),
                    critical=action_data.get("critical", False),
                    retry_on_fail=action_data.get("retry_on_fail", False),
                    max_retries=action_data.get("max_retries", 3)
                )
                actions.append(comet_action)

            flow = cls(
                flow_id=data["flow_id"],
                name=data["name"],
                description=data["description"],
                actions=actions,
                created_at=data.get("created_at", datetime.now().isoformat()),
                metadata=data.get("metadata", {})
            )

            logger.info(f"Flow carregado: {file_path}")
            return flow

        except Exception as e:
            logger.error(f"Erro ao carregar flow: {e}")
            return None


class CometContract:
    """
    Gerenciador de contratos Comet

    Responsável por:
    - Criar flows de automação
    - Validar contratos
    - Salvar/carregar flows
    - Gerar contratos para Comet
    """

    def __init__(self, contracts_dir: str | Path = "runtime/comet_contracts"):
        self.contracts_dir = Path(contracts_dir)
        self.contracts_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"CometContract inicializado: {contracts_dir}")

    def create_flow(
        self,
        flow_id: str,
        name: str,
        description: str,
        metadata: Optional[dict] = None
    ) -> CometFlow:
        """
        Cria novo flow

        Args:
            flow_id: ID único do flow
            name: Nome do flow
            description: Descrição
            metadata: Metadados adicionais

        Returns:
            CometFlow
        """
        return CometFlow(
            flow_id=flow_id,
            name=name,
            description=description,
            metadata=metadata or {}
        )

    def save_flow(self, flow: CometFlow) -> bool:
        """
        Salva flow no diretório de contratos

        Args:
            flow: CometFlow

        Returns:
            True se salvo com sucesso
        """
        file_path = self.contracts_dir / f"{flow.flow_id}.json"
        return flow.save_to_file(file_path)

    def load_flow(self, flow_id: str) -> Optional[CometFlow]:
        """
        Carrega flow por ID

        Args:
            flow_id: ID do flow

        Returns:
            CometFlow ou None
        """
        file_path = self.contracts_dir / f"{flow_id}.json"
        return CometFlow.load_from_file(file_path)

    def list_flows(self) -> List[dict]:
        """
        Lista todos os flows disponíveis

        Returns:
            Lista de metadados de flows
        """
        flows = []

        for file_path in self.contracts_dir.glob("*.json"):
            try:
                flow = CometFlow.load_from_file(file_path)
                if flow:
                    flows.append({
                        "flow_id": flow.flow_id,
                        "name": flow.name,
                        "description": flow.description,
                        "actions_count": len(flow.actions),
                        "created_at": flow.created_at
                    })
            except Exception as e:
                logger.error(f"Erro ao listar flow {file_path}: {e}")

        return flows

    def validate_flow(self, flow: CometFlow) -> tuple[bool, List[str]]:
        """
        Valida flow

        Args:
            flow: CometFlow

        Returns:
            Tupla (is_valid, errors)
        """
        errors = []

        if not flow.flow_id:
            errors.append("Flow ID é obrigatório")

        if not flow.name:
            errors.append("Nome é obrigatório")

        if len(flow.actions) == 0:
            errors.append("Flow deve ter pelo menos uma ação")

        # Validar cada ação
        for i, comet_action in enumerate(flow.actions):
            is_valid, error = comet_action.action.validate()
            if not is_valid:
                errors.append(f"Ação {i}: {error}")

        is_valid = len(errors) == 0

        return is_valid, errors

    def generate_contract_file(self, flow: CometFlow) -> Optional[str]:
        """
        Gera arquivo de contrato para Comet

        Args:
            flow: CometFlow

        Returns:
            Caminho do arquivo gerado ou None
        """
        # Validar flow
        is_valid, errors = self.validate_flow(flow)

        if not is_valid:
            logger.error(f"Flow inválido: {errors}")
            return None

        # Salvar flow
        success = self.save_flow(flow)

        if success:
            file_path = self.contracts_dir / f"{flow.flow_id}.json"
            return str(file_path)

        return None
