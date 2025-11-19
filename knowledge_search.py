# -*- coding: utf-8 -*-
"""
PROMETHEUS KNOWLEDGE SEARCH - Busca Semântica Profissional

USO:
    python knowledge_search.py "configurar RD Station clínica"
    python knowledge_search.py "automação marketing" --limit 20
    python knowledge_search.py "FastAPI endpoints" --threshold 0.8
"""

import os
import sys
import io
import asyncio
import argparse
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from prometheus_v3.knowledge.supabase_client import PrometheusSupabaseClient
from prometheus_v3.knowledge.chunk_processor import ChunkProcessor


async def search(query: str, limit: int = 10, threshold: float = 0.7, verbose: bool = False):
    """Busca semântica no Knowledge Brain"""

    print("="*70)
    print("🔍 PROMETHEUS KNOWLEDGE SEARCH")
    print("="*70)
    print(f"\nQuery: {query}")
    print(f"Limit: {limit} results")
    print(f"Threshold: {threshold} (similarity)")
    print()

    # Inicializar componentes
    if verbose:
        print("Initializing...")

    client = PrometheusSupabaseClient(use_service_role=False)  # Read-only
    chunker = ChunkProcessor()

    # Gerar embedding da query
    print("🧠 Generating query embedding...", end='', flush=True)
    query_embedding = await chunker.generate_embedding(query)
    print(" OK")

    # Busca semântica
    print(f"📚 Searching knowledge base...")
    results = await client.semantic_search(
        query_embedding,
        limit=limit,
        threshold=threshold
    )

    # Exibir resultados
    if not results:
        print("\n❌ No results found.")
        print(f"Try lowering threshold (current: {threshold})")
        return

    print(f"\n✅ Found {len(results)} results:\n")
    print("="*70)

    for i, result in enumerate(results, 1):
        similarity = result.get('similarity', 0)
        content = result.get('content', '')
        doc_name = result.get('document_name', 'Unknown')
        doc_source = result.get('document_source', 'unknown')
        tokens = result.get('tokens', 0)

        print(f"\n#{i} - Score: {similarity:.3f} ({similarity*100:.1f}%)")
        print(f"Source: {doc_source.upper()} / {doc_name}")
        print(f"Tokens: {tokens}")
        print("-"*70)

        # Mostrar preview do conteúdo (primeiras 300 chars)
        preview = content[:300] + "..." if len(content) > 300 else content
        print(preview)

        if verbose and len(content) > 300:
            print("\n[Full content]:")
            print(content)

    print("\n" + "="*70)
    print(f"📊 Total results: {len(results)}")


async def stats():
    """Mostra estatísticas do knowledge base"""

    print("="*70)
    print("📊 KNOWLEDGE BRAIN STATS")
    print("="*70)

    client = PrometheusSupabaseClient(use_service_role=False)
    stats_data = client.get_stats()

    print(f"\nTotal Documents: {stats_data.get('total_documents', 0)}")
    print(f"Total Chunks: {stats_data.get('total_chunks', 0)}")
    print("\nBy Source:")

    for source_info in stats_data.get('by_source', []):
        source = source_info.get('source_type', 'unknown')
        count = source_info.get('count', 0)
        print(f"  {source.upper()}: {count} documents")

    print("="*70)


async def main():
    parser = argparse.ArgumentParser(description='Prometheus Knowledge Search')
    parser.add_argument('query', nargs='?', help='Search query')
    parser.add_argument('--limit', type=int, default=10, help='Max results')
    parser.add_argument('--threshold', type=float, default=0.7, help='Min similarity (0-1)')
    parser.add_argument('--verbose', action='store_true', help='Show full content')
    parser.add_argument('--stats', action='store_true', help='Show knowledge base stats')

    args = parser.parse_args()

    if args.stats:
        await stats()
    elif args.query:
        await search(args.query, args.limit, args.threshold, args.verbose)
    else:
        parser.print_help()


if __name__ == '__main__':
    asyncio.run(main())
