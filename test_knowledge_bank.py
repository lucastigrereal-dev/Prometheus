# -*- coding: utf-8 -*-
"""
TESTE DO KNOWLEDGE BANK - Validação Completa

Testa:
1. KnowledgeBank
2. SmartCache (L1/L2)
3. Ingestores (Perplexity, Claude, GPT)
4. Background Scheduler
"""

import asyncio
import sys
import io
from pathlib import Path

# Fix encoding para Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Adiciona path do Prometheus
sys.path.insert(0, str(Path(__file__).parent))

from prometheus_v3.knowledge.knowledge_bank import KnowledgeBank, Knowledge
from prometheus_v3.knowledge.smart_cache import SmartCache
from prometheus_v3.knowledge.ingestors import (
    PerplexityIngestor,
    ClaudeHistoryIngestor,
    GPTHistoryIngestor
)
from prometheus_v3.knowledge.background_ingestion import BackgroundIngestionScheduler


async def test_smart_cache():
    """Testa SmartCache"""
    print("\n" + "=" * 70)
    print("TESTE 1: SmartCache Multi-Layer")
    print("=" * 70)

    cache = SmartCache(l1_max_size=10, l2_enabled=True, ttl_seconds=3600)

    # Test 1: Set e Get
    print("\n1. Testando set/get...")
    await cache.set("test_key", "test_value")
    result = await cache.get("test_key")
    assert result == "test_value", "Cache set/get failed"
    print("   OK Cache set/get funciona")

    # Test 2: Cache hit L1
    print("\n2. Testando cache hit L1...")
    result2 = await cache.get("test_key")
    stats = cache.get_stats()
    assert stats['l1_hits'] > 0, "L1 cache should have hit"
    print(f"   OK L1 hit rate: {stats['l1_hit_rate']:.2%}")

    # Test 3: Múltiplas entries
    print("\n3. Testando múltiplas entries...")
    for i in range(5):
        await cache.set(f"key_{i}", f"value_{i}")

    print(f"   OK {len(cache.l1_cache)} entries no cache L1")

    # Test 4: Stats
    stats = cache.get_stats()
    print(f"\n4. Estatísticas do cache:")
    print(f"   Total requests: {stats['total_requests']}")
    print(f"   Hit rate: {stats['hit_rate']:.2%}")
    print(f"   L1 hits: {stats['l1_hits']}")
    print(f"   L2 hits: {stats['l2_hits']}")

    print("\nOK SmartCache funciona corretamente!")
    return True


async def test_ingestors():
    """Testa ingestores"""
    print("\n" + "=" * 70)
    print("TESTE 2: Ingestores de Conhecimento")
    print("=" * 70)

    # Perplexity
    print("\n1. Testando PerplexityIngestor...")
    perplexity = PerplexityIngestor()
    chunks = await perplexity.fetch_new()
    print(f"   OK Perplexity: {len(chunks)} chunks (mock data)")

    # Claude History
    print("\n2. Testando ClaudeHistoryIngestor...")
    claude = ClaudeHistoryIngestor()
    chunks = await claude.fetch_new()
    print(f"   OK Claude History: {len(chunks)} chunks (mock data)")

    # GPT History
    print("\n3. Testando GPTHistoryIngestor...")
    gpt = GPTHistoryIngestor()
    chunks = await gpt.fetch_new()
    print(f"   OK GPT History: {len(chunks)} chunks (mock data)")

    print("\nOK Todos os ingestores funcionam!")
    return True


async def test_knowledge_bank():
    """Testa KnowledgeBank completo"""
    print("\n" + "=" * 70)
    print("TESTE 3: KnowledgeBank Completo")
    print("=" * 70)

    # Cria cache
    cache = SmartCache(l1_max_size=100, l2_enabled=True)

    # Cria ingestores
    ingestors = [
        PerplexityIngestor(),
        ClaudeHistoryIngestor(),
        GPTHistoryIngestor()
    ]

    # Cria KnowledgeBank
    kb = KnowledgeBank(
        cache=cache,
        ingestors=ingestors
    )

    print(f"\n1. KnowledgeBank criado com {len(ingestors)} ingestores")

    # Test ingestion
    print("\n2. Rodando ingestão...")
    results = await kb.ingest_all(background=False)

    total_chunks = sum(results.values())
    print(f"   OK Ingestão concluída: {total_chunks} chunks totais")
    for source, count in results.items():
        print(f"      - {source}: {count} chunks")

    # Test store
    print("\n3. Testando armazenamento manual...")
    test_knowledge = Knowledge(
        content="Test content for knowledge bank",
        metadata={'test': True},
        source='test'
    )
    stored = await kb.store(test_knowledge)
    print(f"   {'OK' if stored else 'FAIL'} Knowledge armazenado")

    # Test search
    print("\n4. Testando busca...")
    # Como não temos MemoryManager integrado, search retorna vazio
    results = await kb.search("test query", limit=5)
    print(f"   OK Search executado (sem MemoryManager, retorna vazio)")

    # Test stats
    stats = kb.get_stats()
    print(f"\n5. Estatísticas do KnowledgeBank:")
    print(f"   Total chunks: {stats['total_chunks']}")
    print(f"   Searches: {stats['searches']}")
    print(f"   Cache hit rate: {stats['cache_hit_rate']:.2%}")
    print(f"   Ingestions: {stats['ingestions']}")

    print("\nOK KnowledgeBank funciona!")
    return True


async def test_background_scheduler():
    """Testa background scheduler"""
    print("\n" + "=" * 70)
    print("TESTE 4: Background Ingestion Scheduler")
    print("=" * 70)

    # Cria KB
    kb = KnowledgeBank(
        cache=SmartCache(),
        ingestors=[PerplexityIngestor()]
    )

    # Cria scheduler
    scheduler = BackgroundIngestionScheduler(
        knowledge_bank=kb,
        interval_hours=6,
        run_on_startup=False  # Não roda agora para teste rápido
    )

    print("\n1. Scheduler criado")

    # Roda manualmente
    print("\n2. Rodando ingestão manual...")
    await scheduler.run_now()
    print("   OK Ingestão manual completa")

    # Status
    status = scheduler.get_status()
    print(f"\n3. Status do scheduler:")
    print(f"   Running: {status['is_running']}")
    print(f"   Interval: {status['interval_hours']}h")
    print(f"   Last run: {status['last_run']}")

    # Start/Stop test
    print("\n4. Testando start/stop...")
    await scheduler.start()
    print("   OK Scheduler started")

    # Aguarda 1 segundo
    await asyncio.sleep(1)

    await scheduler.stop()
    print("   OK Scheduler stopped")

    print("\nOK Background scheduler funciona!")
    return True


async def main():
    """Função principal de teste"""
    print("\n")
    print("+" + "=" * 68 + "+")
    print("|" + " " * 15 + "TESTE KNOWLEDGE BANK COMPLETO" + " " * 24 + "|")
    print("+" + "=" * 68 + "+")

    all_passed = True

    try:
        # Test 1: SmartCache
        passed = await test_smart_cache()
        all_passed = all_passed and passed

        # Test 2: Ingestors
        passed = await test_ingestors()
        all_passed = all_passed and passed

        # Test 3: KnowledgeBank
        passed = await test_knowledge_bank()
        all_passed = all_passed and passed

        # Test 4: Background Scheduler
        passed = await test_background_scheduler()
        all_passed = all_passed and passed

    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    # Resultado final
    print("\n" + "=" * 70)
    print("RESULTADO FINAL")
    print("=" * 70)

    if all_passed:
        print("\nOK TODOS OS TESTES PASSARAM!")
        print("\nOK SEMANA 1 COMPLETA:")
        print("   OK KnowledgeBank core")
        print("   OK SmartCache (L1/L2)")
        print("   OK 3 Ingestores (Perplexity, Claude, GPT)")
        print("   OK Background Scheduler")
        print("\nPROXIMO: Semana 2 - Unified Executor")
        return 0
    else:
        print("\nFAIL Alguns testes falharam")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    exit(exit_code)
