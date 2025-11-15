# -*- coding: utf-8 -*-
"""
SMART CACHE - Cache Multi-Layer para Redução de Custos

Camadas:
- L1: Memória RAM (exact match) - 100ms, $0
- L2: Disco/Redis (exact match) - 5ms, $0
- L3: FAISS (semantic match) - 50ms, $0
- L4: Cache Miss - chama IA real - $0.01-0.05
"""

import asyncio
import hashlib
import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, List
from collections import OrderedDict

logger = logging.getLogger(__name__)


class SmartCache:
    """
    Cache multi-layer inteligente

    Reduz custos de API em ~70% através de:
    - L1: Cache em RAM para queries exatas
    - L2: Cache em disco para persistência
    - L3: Cache semântico com FAISS (similaridade > 95%)
    """

    def __init__(
        self,
        l1_max_size: int = 1000,
        l2_enabled: bool = True,
        l3_enabled: bool = False,  # FAISS semantic cache
        l3_threshold: float = 0.95,
        ttl_seconds: int = 3600,  # 1 hour
        cache_dir: Path = None
    ):
        """
        Args:
            l1_max_size: Tamanho máximo do cache L1 (RAM)
            l2_enabled: Se True, usa cache L2 (disco)
            l3_enabled: Se True, usa cache L3 (FAISS semantic)
            l3_threshold: Threshold de similaridade para L3
            ttl_seconds: Tempo de vida do cache em segundos
            cache_dir: Diretório para cache L2
        """
        # L1: RAM cache (OrderedDict para LRU)
        self.l1_cache: OrderedDict = OrderedDict()
        self.l1_max_size = l1_max_size

        # L2: Disk cache
        self.l2_enabled = l2_enabled
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent.parent / 'data' / 'cache'
        self.cache_dir = Path(cache_dir)
        if self.l2_enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

        # L3: FAISS semantic cache
        self.l3_enabled = l3_enabled
        self.l3_threshold = l3_threshold
        self.l3_index = None  # TODO: Integrar com FAISS

        # TTL
        self.ttl = timedelta(seconds=ttl_seconds)

        # Stats
        self.stats = {
            'l1_hits': 0,
            'l1_misses': 0,
            'l2_hits': 0,
            'l2_misses': 0,
            'l3_hits': 0,
            'l3_misses': 0,
            'total_requests': 0
        }

        logger.info(f"SmartCache initialized: L1={l1_max_size}, L2={l2_enabled}, L3={l3_enabled}")

    def _hash_key(self, key: str) -> str:
        """Gera hash MD5 da chave"""
        return hashlib.md5(key.encode()).hexdigest()

    def _is_expired(self, timestamp: datetime) -> bool:
        """Verifica se entry expirou"""
        return datetime.now() - timestamp > self.ttl

    async def get(self, key: str) -> Optional[Any]:
        """
        Busca no cache (L1 -> L2 -> L3)

        Args:
            key: Chave de busca

        Returns:
            Valor cacheado ou None
        """
        self.stats['total_requests'] += 1

        # L1: RAM cache (exact match)
        l1_result = self._get_l1(key)
        if l1_result is not None:
            self.stats['l1_hits'] += 1
            logger.debug(f"L1 HIT: {key[:50]}...")
            return l1_result

        self.stats['l1_misses'] += 1

        # L2: Disk cache (exact match)
        if self.l2_enabled:
            l2_result = await self._get_l2(key)
            if l2_result is not None:
                self.stats['l2_hits'] += 1
                logger.debug(f"L2 HIT: {key[:50]}...")
                # Promove para L1
                self._set_l1(key, l2_result)
                return l2_result

            self.stats['l2_misses'] += 1

        # L3: FAISS semantic cache (similarity > threshold)
        if self.l3_enabled:
            l3_result = await self._get_l3(key)
            if l3_result is not None:
                self.stats['l3_hits'] += 1
                logger.debug(f"L3 HIT (semantic): {key[:50]}...")
                # Promove para L1 e L2
                self._set_l1(key, l3_result)
                if self.l2_enabled:
                    await self._set_l2(key, l3_result)
                return l3_result

            self.stats['l3_misses'] += 1

        # Cache miss total
        logger.debug(f"CACHE MISS: {key[:50]}...")
        return None

    def _get_l1(self, key: str) -> Optional[Any]:
        """Busca no cache L1 (RAM)"""
        entry = self.l1_cache.get(key)

        if entry is None:
            return None

        # Verifica expiração
        if self._is_expired(entry['timestamp']):
            del self.l1_cache[key]
            return None

        # Move para final (LRU)
        self.l1_cache.move_to_end(key)

        return entry['value']

    async def _get_l2(self, key: str) -> Optional[Any]:
        """Busca no cache L2 (disco)"""
        hash_key = self._hash_key(key)
        cache_file = self.cache_dir / f"{hash_key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                entry = json.load(f)

            # Verifica expiração
            timestamp = datetime.fromisoformat(entry['timestamp'])
            if self._is_expired(timestamp):
                cache_file.unlink()
                return None

            return entry['value']

        except Exception as e:
            logger.warning(f"Error reading L2 cache: {e}")
            return None

    async def _get_l3(self, key: str) -> Optional[Any]:
        """
        Busca no cache L3 (FAISS semantic)

        TODO: Implementar busca semântica com FAISS
        Por ora, retorna None
        """
        # TODO: Integrar com FAISS
        # 1. Gerar embedding da key
        # 2. Buscar em FAISS com threshold
        # 3. Se score > threshold, retornar valor cacheado

        return None

    async def set(self, key: str, value: Any):
        """
        Armazena no cache (L1 e L2)

        Args:
            key: Chave
            value: Valor a cachear
        """
        # L1: RAM
        self._set_l1(key, value)

        # L2: Disco
        if self.l2_enabled:
            await self._set_l2(key, value)

    def _set_l1(self, key: str, value: Any):
        """Armazena no cache L1 (RAM)"""
        # Remove mais antigo se cheio (LRU)
        if len(self.l1_cache) >= self.l1_max_size:
            self.l1_cache.popitem(last=False)

        self.l1_cache[key] = {
            'value': value,
            'timestamp': datetime.now()
        }

    async def _set_l2(self, key: str, value: Any):
        """Armazena no cache L2 (disco)"""
        hash_key = self._hash_key(key)
        cache_file = self.cache_dir / f"{hash_key}.json"

        try:
            entry = {
                'key': key,  # Armazena key original para debug
                'value': value,
                'timestamp': datetime.now().isoformat()
            }

            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(entry, f, indent=2, ensure_ascii=False, default=str)

        except Exception as e:
            logger.warning(f"Error writing L2 cache: {e}")

    async def clear(self):
        """Limpa todo o cache"""
        # L1
        self.l1_cache.clear()
        logger.info("L1 cache cleared")

        # L2
        if self.l2_enabled:
            for cache_file in self.cache_dir.glob("*.json"):
                try:
                    cache_file.unlink()
                except Exception as e:
                    logger.warning(f"Error deleting cache file: {e}")
            logger.info("L2 cache cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do cache"""
        total_requests = self.stats['total_requests']

        if total_requests == 0:
            return {
                **self.stats,
                'hit_rate': 0.0,
                'l1_hit_rate': 0.0,
                'l2_hit_rate': 0.0,
                'l3_hit_rate': 0.0
            }

        total_hits = (
            self.stats['l1_hits'] +
            self.stats['l2_hits'] +
            self.stats['l3_hits']
        )

        return {
            **self.stats,
            'hit_rate': total_hits / total_requests,
            'l1_hit_rate': self.stats['l1_hits'] / total_requests,
            'l2_hit_rate': self.stats['l2_hits'] / total_requests,
            'l3_hit_rate': self.stats['l3_hits'] / total_requests,
            'l1_size': len(self.l1_cache),
            'l1_max_size': self.l1_max_size
        }

    async def cleanup_expired(self):
        """Remove entradas expiradas do cache L2"""
        if not self.l2_enabled:
            return

        removed = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    entry = json.load(f)

                timestamp = datetime.fromisoformat(entry['timestamp'])
                if self._is_expired(timestamp):
                    cache_file.unlink()
                    removed += 1

            except Exception as e:
                logger.warning(f"Error cleaning cache file: {e}")

        if removed > 0:
            logger.info(f"Cleaned {removed} expired cache entries")
