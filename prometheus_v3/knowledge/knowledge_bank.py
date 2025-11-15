# -*- coding: utf-8 -*-
"""
KNOWLEDGE BANK - Sistema Unificado de Conhecimento
Usa MemoryManager (V2) + Ingestores + Cache Multi-Layer
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import json

logger = logging.getLogger(__name__)


@dataclass
class Knowledge:
    """Unidade de conhecimento"""
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    embedding: Optional[List[float]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    source: str = "unknown"

    def to_dict(self) -> Dict[str, Any]:
        """Converte para dict"""
        return {
            'content': self.content,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'source': self.source
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Knowledge':
        """Cria a partir de dict"""
        timestamp = data.get('timestamp')
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return cls(
            content=data['content'],
            metadata=data.get('metadata', {}),
            timestamp=timestamp or datetime.now(),
            source=data.get('source', 'unknown')
        )


class KnowledgeBank:
    """
    Sistema unificado de conhecimento

    Gerencia conhecimento de múltiplas fontes usando:
    - MemoryManager (V2) para FAISS
    - Ingestores para múltiplas fontes
    - Cache multi-layer para performance
    """

    def __init__(
        self,
        memory_manager=None,
        cache=None,
        ingestors: List[Any] = None,
        data_dir: Path = None
    ):
        """
        Args:
            memory_manager: MemoryManager (V2) - se None, tenta carregar
            cache: SmartCache - se None, cria novo
            ingestors: Lista de ingestores
            data_dir: Diretório para dados
        """
        self.memory_manager = memory_manager
        self.cache = cache
        self.ingestors = ingestors or []

        # Data directory
        if data_dir is None:
            data_dir = Path(__file__).parent.parent.parent / 'data' / 'knowledge'
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Stats
        self.stats = {
            'total_chunks': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'ingestions': 0,
            'searches': 0
        }

        # Load stats
        self._load_stats()

        logger.info(f"KnowledgeBank initialized with {len(self.ingestors)} ingestors")

    def _load_stats(self):
        """Carrega estatísticas salvas"""
        stats_file = self.data_dir / 'stats.json'
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    self.stats.update(json.load(f))
                logger.info(f"Stats loaded: {self.stats['total_chunks']} chunks")
            except Exception as e:
                logger.warning(f"Failed to load stats: {e}")

    def _save_stats(self):
        """Salva estatísticas"""
        stats_file = self.data_dir / 'stats.json'
        try:
            with open(stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save stats: {e}")

    async def search(
        self,
        query: str,
        limit: int = 5,
        min_score: float = 0.7,
        use_cache: bool = True
    ) -> List[Knowledge]:
        """
        Busca conhecimento relevante

        Args:
            query: Query de busca
            limit: Número máximo de resultados
            min_score: Score mínimo de similaridade
            use_cache: Se True, usa cache

        Returns:
            Lista de Knowledge objects
        """
        self.stats['searches'] += 1

        # Tenta cache primeiro
        if use_cache and self.cache:
            cached = await self.cache.get(query)
            if cached:
                self.stats['cache_hits'] += 1
                logger.debug(f"Cache HIT for query: {query[:50]}...")
                return cached

        self.stats['cache_misses'] += 1
        logger.debug(f"Cache MISS for query: {query[:50]}...")

        # Busca no MemoryManager (V2)
        results = []

        if self.memory_manager:
            try:
                # MemoryManager tem método search
                memory_results = await self._search_memory(query, limit)
                results.extend(memory_results)
            except Exception as e:
                logger.error(f"Error searching memory: {e}")

        # Filtra por score mínimo
        results = [r for r in results if r.metadata.get('score', 0) >= min_score]

        # Limita resultados
        results = results[:limit]

        # Cacheia resultado
        if use_cache and self.cache and results:
            await self.cache.set(query, results)

        logger.info(f"Search returned {len(results)} results for: {query[:50]}...")
        return results

    async def _search_memory(self, query: str, limit: int) -> List[Knowledge]:
        """
        Busca no MemoryManager (V2)

        Para ser implementado quando integrar com MemoryManager real
        Por ora, retorna lista vazia
        """
        # TODO: Integrar com MemoryManager (V2) real
        # memory_results = self.memory_manager.search(query, limit=limit)
        # converter para Knowledge objects

        logger.debug("MemoryManager search not yet integrated - returning empty")
        return []

    async def store(self, knowledge: Knowledge) -> bool:
        """
        Armazena conhecimento

        Args:
            knowledge: Knowledge object

        Returns:
            True se sucesso
        """
        try:
            if self.memory_manager:
                # TODO: Integrar com MemoryManager (V2)
                # self.memory_manager.store(knowledge.content, metadata=knowledge.metadata)
                pass

            self.stats['total_chunks'] += 1
            self._save_stats()

            logger.debug(f"Stored knowledge from source: {knowledge.source}")
            return True

        except Exception as e:
            logger.error(f"Error storing knowledge: {e}")
            return False

    async def store_batch(self, knowledge_list: List[Knowledge]) -> int:
        """
        Armazena múltiplos conhecimentos

        Args:
            knowledge_list: Lista de Knowledge objects

        Returns:
            Número de itens armazenados com sucesso
        """
        stored = 0
        for knowledge in knowledge_list:
            if await self.store(knowledge):
                stored += 1

        logger.info(f"Stored {stored}/{len(knowledge_list)} knowledge chunks")
        return stored

    async def ingest_all(self, background: bool = False) -> Dict[str, int]:
        """
        Roda todos os ingestores

        Args:
            background: Se True, roda em background

        Returns:
            Dict com contagem por ingestor
        """
        if background:
            # Roda em background task
            asyncio.create_task(self._run_ingestion())
            return {'status': 'running_in_background'}
        else:
            return await self._run_ingestion()

    async def _run_ingestion(self) -> Dict[str, int]:
        """Executa ingestão de todos os ingestores"""
        results = {}

        logger.info(f"Starting ingestion from {len(self.ingestors)} sources...")

        for ingestor in self.ingestors:
            try:
                logger.info(f"Running ingestor: {ingestor.__class__.__name__}")

                # Busca novos chunks
                chunks = await ingestor.fetch_new()

                # Armazena
                stored = await self.store_batch(chunks)

                results[ingestor.__class__.__name__] = stored
                self.stats['ingestions'] += 1

                logger.info(f"{ingestor.__class__.__name__}: {stored} chunks stored")

            except Exception as e:
                logger.error(f"Ingestor {ingestor.__class__.__name__} failed: {e}")
                results[ingestor.__class__.__name__] = 0

        self._save_stats()

        total_stored = sum(results.values())
        logger.info(f"Ingestion complete: {total_stored} total chunks")

        return results

    async def store_task_result(self, task_description: str, plan: Any, result: Any):
        """
        Armazena resultado de tarefa bem-sucedida para aprendizado

        Args:
            task_description: Descrição da tarefa
            plan: Plano de execução usado
            result: Resultado da execução
        """
        if not result or not getattr(result, 'success', False):
            return  # Só armazena sucessos

        knowledge = Knowledge(
            content=f"Task: {task_description}\nPlan: {plan}\nResult: Success",
            metadata={
                'type': 'task_result',
                'success': True,
                'task': task_description,
                'timestamp': datetime.now().isoformat()
            },
            source='task_execution'
        )

        await self.store(knowledge)
        logger.info(f"Stored successful task result: {task_description[:50]}...")

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas"""
        if self.stats['searches'] > 0:
            hit_rate = self.stats['cache_hits'] / self.stats['searches']
        else:
            hit_rate = 0.0

        return {
            **self.stats,
            'cache_hit_rate': hit_rate,
            'ingestors_count': len(self.ingestors)
        }

    def add_ingestor(self, ingestor):
        """Adiciona um ingestor"""
        self.ingestors.append(ingestor)
        logger.info(f"Added ingestor: {ingestor.__class__.__name__}")

    async def clear_cache(self):
        """Limpa cache"""
        if self.cache:
            await self.cache.clear()
            logger.info("Cache cleared")
