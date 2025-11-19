# -*- coding: utf-8 -*-
"""
PROMETHEUS KNOWLEDGE INGEST - Sistema de Importação Completo

USO:
    python knowledge_ingest.py                    # Processa tudo em inbox_raw/
    python knowledge_ingest.py --source claude    # Só arquivos Claude
    python knowledge_ingest.py --dry-run          # Simula sem subir

FLUXO:
    1. Lê arquivos de knowledge/inbox_raw/{claude,gpt,perplexity}/
    2. Sanitiza dados sensíveis (API keys, CPF, etc)
    3. Quebra em chunks de 500-700 palavras
    4. Gera embeddings com OpenAI
    5. Upload para Supabase
    6. Move para knowledge/cleaned/
"""

import os
import sys
import io
import asyncio
import argparse
import hashlib
import shutil
import json
from pathlib import Path
from datetime import datetime

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from prometheus_v3.knowledge.supabase_client import PrometheusSupabaseClient
from prometheus_v3.knowledge.data_sanitizer import DataSanitizer
from prometheus_v3.knowledge.chunk_processor import ChunkProcessor


class KnowledgeIngestPipeline:
    """Pipeline completo de ingestão"""

    def __init__(self, dry_run: bool = False):
        self.base_path = Path(__file__).parent / "knowledge"
        self.inbox = self.base_path / "inbox_raw"
        self.cleaned = self.base_path / "cleaned"
        self.logs = self.base_path / "logs"

        # Inicializa componentes
        print("Initializing components...")
        self.supabase = PrometheusSupabaseClient(use_service_role=True)
        self.sanitizer = DataSanitizer()
        self.chunker = ChunkProcessor(chunk_size=600)
        self.dry_run = dry_run

        self.stats = {
            'files_processed': 0,
            'chunks_created': 0,
            'redactions': 0,
            'cost_usd': 0.0,
            'errors': []
        }

    async def process_file(self, file_path: Path, source_type: str):
        """Processa um arquivo completo"""
        print(f"\n📄 {file_path.name}")

        # 1. Ler arquivo
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            raw_content = f.read()

        if not raw_content.strip():
            print("   ⚠️  Empty file, skipping")
            return

        # 2. Sanitizar
        clean_text, redacted = self.sanitizer.sanitize(raw_content)
        if redacted:
            print(f"   🔒 Sanitized: {len(redacted)} types")
            self.stats['redactions'] += len(redacted)

        # 3. Hash para deduplicação
        file_hash = hashlib.md5(clean_text.encode()).hexdigest()

        # 4. Quebrar em chunks
        chunks = self.chunker.split_into_chunks(
            clean_text,
            metadata={'source': source_type, 'file': file_path.name}
        )
        print(f"   📦 {len(chunks)} chunks (avg {sum(c['tokens'] for c in chunks) // len(chunks)} tokens)")

        # 5. Gerar embeddings
        print(f"   🧠 Generating embeddings...", end='', flush=True)
        chunks_with_embeddings = await self.chunker.process_chunks(chunks)
        print(" OK")

        # 6. Estimar custo
        cost = self.chunker.estimate_cost(clean_text)
        self.stats['cost_usd'] += cost
        print(f"   💰 Cost: ${cost:.4f}")

        if self.dry_run:
            print(f"   🔍 DRY RUN - Would upload {len(chunks)} chunks")
            self.stats['files_processed'] += 1
            self.stats['chunks_created'] += len(chunks)
            return

        # 7. Upload Supabase
        try:
            print(f"   ☁️  Uploading...", end='', flush=True)

            # Document
            doc_id = await self.supabase.upsert_document(
                file_hash=file_hash,
                file_name=file_path.name,
                source_type=source_type,
                original_path=str(file_path),
                total_chunks=len(chunks),
                metadata={'redactions': redacted}
            )

            # Chunks
            for chunk in chunks_with_embeddings:
                chunk['document_id'] = doc_id

            uploaded = await self.supabase.insert_chunks(chunks_with_embeddings)
            print(f" OK ({uploaded} new)")

        except Exception as e:
            print(f"\n   ❌ Upload error: {e}")
            self.stats['errors'].append(str(e))
            return

        # 8. Mover para cleaned/
        today = datetime.now().strftime("%Y-%m-%d")
        dest_dir = self.cleaned / today
        dest_dir.mkdir(parents=True, exist_ok=True)

        shutil.move(str(file_path), str(dest_dir / file_path.name))
        print(f"   ✅ Moved to cleaned/{today}/")

        self.stats['files_processed'] += 1
        self.stats['chunks_created'] += len(chunks)

    async def run(self, source_filter: str = None):
        """Executa pipeline"""
        print("="*70)
        print("🧠 PROMETHEUS KNOWLEDGE INGEST")
        print("="*70)

        sources = ['claude', 'gpt', 'perplexity']
        if source_filter:
            sources = [source_filter]

        for source in sources:
            source_dir = self.inbox / source
            if not source_dir.exists():
                continue

            files = list(source_dir.glob("*.txt")) + \
                    list(source_dir.glob("*.md")) + \
                    list(source_dir.glob("*.json"))

            if not files:
                continue

            print(f"\n📂 {source.upper()}: {len(files)} files")

            for file_path in files:
                try:
                    await self.process_file(file_path, source)
                except Exception as e:
                    print(f"   ❌ Error: {e}")
                    self.stats['errors'].append(str(e))

        # Relatório
        print("\n" + "="*70)
        print("📊 SUMMARY")
        print("="*70)
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Chunks created: {self.stats['chunks_created']}")
        print(f"Sanitizations: {self.stats['redactions']}")
        print(f"Total cost: ${self.stats['cost_usd']:.4f}")
        print(f"Errors: {len(self.stats['errors'])}")

        # Log
        log_file = self.logs / f"ingest_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        with open(log_file, 'w') as f:
            json.dump(self.stats, f, indent=2)

        print(f"\n📝 Log: {log_file}")


async def main():
    parser = argparse.ArgumentParser(description='Prometheus Knowledge Ingest')
    parser.add_argument('--source', choices=['claude', 'gpt', 'perplexity'])
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()

    pipeline = KnowledgeIngestPipeline(dry_run=args.dry_run)
    await pipeline.run(source_filter=args.source)


if __name__ == '__main__':
    asyncio.run(main())
