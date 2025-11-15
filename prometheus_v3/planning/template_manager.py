# -*- coding: utf-8 -*-
"""
TEMPLATE MANAGER - Aprende Padrões de Execução Bem-Sucedidos

Economia: 60% dos custos após 100 tarefas usando templates
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ExecutionTemplate:
    """Template de execução aprendido"""
    id: str
    pattern: str  # Padrão da tarefa (ex: "criar endpoint {framework}")
    intent: str
    steps: List[Dict[str, Any]]
    success_count: int = 0
    total_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None

    @property
    def success_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.success_count / self.total_count


class TemplateManager:
    """
    Gerencia templates de execução aprendidos

    Workflow:
    1. Salva planos bem-sucedidos como templates
    2. Busca templates similares para novas tarefas
    3. Instantia template com novos parâmetros
    4. Track success rate
    """

    def __init__(self, templates_dir: Path = None):
        if templates_dir is None:
            templates_dir = Path(__file__).parent.parent.parent / 'data' / 'templates'

        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        self.templates: List[ExecutionTemplate] = []
        self._load_templates()

        logger.info(f"TemplateManager: {len(self.templates)} templates loaded")

    def _load_templates(self):
        """Carrega templates salvos"""
        manifest = self.templates_dir / 'templates.json'
        if not manifest.exists():
            return

        try:
            with open(manifest, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for t in data:
                template = ExecutionTemplate(
                    id=t['id'],
                    pattern=t['pattern'],
                    intent=t['intent'],
                    steps=t['steps'],
                    success_count=t.get('success_count', 0),
                    total_count=t.get('total_count', 0),
                    created_at=datetime.fromisoformat(t['created_at']),
                    last_used=datetime.fromisoformat(t['last_used']) if t.get('last_used') else None
                )
                self.templates.append(template)

        except Exception as e:
            logger.error(f"Error loading templates: {e}")

    def _save_templates(self):
        """Salva templates"""
        manifest = self.templates_dir / 'templates.json'

        try:
            data = []
            for t in self.templates:
                data.append({
                    'id': t.id,
                    'pattern': t.pattern,
                    'intent': t.intent,
                    'steps': t.steps,
                    'success_count': t.success_count,
                    'total_count': t.total_count,
                    'created_at': t.created_at.isoformat(),
                    'last_used': t.last_used.isoformat() if t.last_used else None
                })

            with open(manifest, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Error saving templates: {e}")

    async def find_matching_template(
        self,
        task_description: str,
        intent: str,
        min_similarity: float = 0.90
    ) -> Optional[ExecutionTemplate]:
        """
        Busca template matching

        Args:
            task_description: Descrição da tarefa
            intent: Intent classificado
            min_similarity: Similaridade mínima (0-1)

        Returns:
            Template ou None
        """
        # Filtrar por intent
        candidates = [t for t in self.templates if t.intent == intent]

        if not candidates:
            return None

        # Busca por similaridade simples (keyword matching)
        best_match = None
        best_score = 0.0

        task_lower = task_description.lower()

        for template in candidates:
            score = self._calculate_similarity(task_lower, template.pattern.lower())

            if score > best_score and score >= min_similarity:
                best_score = score
                best_match = template

        if best_match:
            logger.info(f"Template match found: {best_match.pattern} (score: {best_score:.2f})")
            best_match.last_used = datetime.now()
            self._save_templates()

        return best_match

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calcula similaridade simples entre textos"""
        words1 = set(text1.split())
        words2 = set(text2.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    async def save_successful_execution(
        self,
        task_description: str,
        intent: str,
        steps: List[Dict[str, Any]],
        entities: Dict[str, Any]
    ):
        """
        Salva execução bem-sucedida como template

        Args:
            task_description: Descrição da tarefa
            intent: Intent
            steps: Steps executados
            entities: Entidades extraídas
        """
        # Extrai padrão genérico
        pattern = self._extract_pattern(task_description, entities)

        # Busca se já existe template similar
        existing = await self.find_matching_template(pattern, intent, min_similarity=0.95)

        if existing:
            # Atualiza template existente
            existing.success_count += 1
            existing.total_count += 1
            logger.info(f"Updated template: {existing.pattern} (rate: {existing.success_rate:.1%})")
        else:
            # Cria novo template
            template_id = f"tpl_{len(self.templates)+1:04d}"

            template = ExecutionTemplate(
                id=template_id,
                pattern=pattern,
                intent=intent,
                steps=steps,
                success_count=1,
                total_count=1
            )

            self.templates.append(template)
            logger.info(f"New template created: {pattern}")

        self._save_templates()

    def _extract_pattern(self, task: str, entities: Dict[str, Any]) -> str:
        """
        Extrai padrão genérico da tarefa

        Ex: "Criar endpoint FastAPI de status" → "criar endpoint {framework}"
        """
        pattern = task.lower()

        # Substitui valores específicos por placeholders
        for key, value in entities.items():
            if isinstance(value, str) and value in pattern:
                pattern = pattern.replace(value.lower(), f"{{{key}}}")

        return pattern

    async def record_execution_result(self, template: ExecutionTemplate, success: bool):
        """Registra resultado de uso de template"""
        template.total_count += 1
        if success:
            template.success_count += 1

        self._save_templates()

        logger.info(f"Template {template.id}: rate={template.success_rate:.1%}")

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas"""
        if not self.templates:
            return {
                'total_templates': 0,
                'avg_success_rate': 0.0,
                'total_uses': 0
            }

        total_uses = sum(t.total_count for t in self.templates)
        avg_rate = sum(t.success_rate for t in self.templates) / len(self.templates)

        return {
            'total_templates': len(self.templates),
            'avg_success_rate': avg_rate,
            'total_uses': total_uses,
            'best_template': max(self.templates, key=lambda t: t.success_rate).pattern if self.templates else None
        }
