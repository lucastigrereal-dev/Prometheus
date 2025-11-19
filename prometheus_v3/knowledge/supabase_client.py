# -*- coding: utf-8 -*-
"""
SUPABASE CLIENT - Conexão Profissional com Prometheus Knowledge Brain

Funcionalidades:
- Upsert de documentos com deduplicação automática
- Insert em batch de chunks
- Busca semântica vetorial
- Gestão de embeddings
"""

import os
import logging
from typing import List, Dict, Optional
from datetime import datetime
from supabase import create_client, Client

logger = logging.getLogger(__name__)


class PrometheusSupabaseClient:
    """Cliente Supabase profissional para Prometheus Knowledge Brain"""

    def __init__(self, use_service_role: bool = False):
        """
        Inicializa cliente Supabase

        Args:
            use_service_role: Se True, usa SERVICE_ROLE_KEY (admin), senão usa ANON_KEY
        """
        self.url = os.getenv("SUPABASE_URL")

        if use_service_role:
            self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            logger.info("Using SERVICE_ROLE_KEY (admin permissions)")
        else:
            self.key = os.getenv("SUPABASE_ANON_KEY")
            logger.info("Using ANON_KEY (public permissions)")

        if not self.url or not self.key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_*_KEY must be set in .env file"
            )

        self.client: Client = create_client(self.url, self.key)
        logger.info(f"Supabase client initialized: {self.url}")

    async def upsert_document(
        self,
        file_hash: str,
        file_name: str,
        source_type: str,
        original_path: str,
        total_chunks: int,
        metadata: Dict = None
    ) -> Optional[str]:
        """
        Insere ou atualiza documento (deduplicação automática por hash)

        Args:
            file_hash: MD5 hash do conteúdo
            file_name: Nome do arquivo
            source_type: 'claude', 'gpt', 'perplexity'
            original_path: Caminho original do arquivo
            total_chunks: Número total de chunks
            metadata: Metadados adicionais (opcional)

        Returns:
            UUID do documento (existente ou novo)
        """
        try:
            # Busca por hash para detectar duplicata
            existing = self.client.table('documents')\
                .select('id, relevance_count')\
                .eq('file_hash', file_hash)\
                .execute()

            if existing.data:
                # Documento já existe: incrementa relevance_count
                doc_id = existing.data[0]['id']
                new_count = existing.data[0]['relevance_count'] + 1

                self.client.table('documents')\
                    .update({
                        'relevance_count': new_count,
                        'updated_at': datetime.now().isoformat()
                    })\
                    .eq('id', doc_id)\
                    .execute()

                logger.info(f"Document already exists: {file_name} (count: {new_count})")
                return doc_id

            else:
                # Novo documento: insere
                data = {
                    'file_name': file_name,
                    'file_hash': file_hash,
                    'source_type': source_type,
                    'original_path': original_path,
                    'total_chunks': total_chunks,
                    'metadata': metadata or {},
                    'relevance_count': 1
                }

                result = self.client.table('documents').insert(data).execute()
                doc_id = result.data[0]['id']

                logger.info(f"New document inserted: {file_name} ({doc_id})")
                return doc_id

        except Exception as e:
            logger.error(f"Error upserting document: {e}")
            raise

    async def insert_chunks(self, chunks: List[Dict]) -> int:
        """
        Insere chunks em batch com deduplicação

        Args:
            chunks: Lista de dicts com:
                - document_id (UUID)
                - chunk_index (int)
                - content (str)
                - content_hash (str)
                - embedding (List[float])
                - tokens (int)
                - metadata (dict)

        Returns:
            Número de chunks inseridos (novos)
        """
        inserted_count = 0

        try:
            for chunk in chunks:
                # Verifica se chunk já existe (por hash)
                existing = self.client.table('document_chunks')\
                    .select('id')\
                    .eq('content_hash', chunk['content_hash'])\
                    .execute()

                if not existing.data:
                    # Chunk novo: insere
                    self.client.table('document_chunks').insert(chunk).execute()
                    inserted_count += 1
                else:
                    logger.debug(f"Chunk already exists: {chunk['content_hash'][:16]}...")

            logger.info(f"Inserted {inserted_count}/{len(chunks)} new chunks")
            return inserted_count

        except Exception as e:
            logger.error(f"Error inserting chunks: {e}")
            raise

    async def semantic_search(
        self,
        query_embedding: List[float],
        limit: int = 10,
        threshold: float = 0.7
    ) -> List[Dict]:
        """
        Busca semântica por similaridade vetorial

        Args:
            query_embedding: Vetor de 1536 dimensões (OpenAI ada-002)
            limit: Número máximo de resultados
            threshold: Similaridade mínima (0-1)

        Returns:
            Lista de chunks relevantes com metadados
        """
        try:
            result = self.client.rpc(
                'match_documents',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': threshold,
                    'match_count': limit
                }
            ).execute()

            logger.info(f"Semantic search found {len(result.data)} results")
            return result.data

        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            raise

    def get_stats(self) -> Dict:
        """Retorna estatísticas do banco de conhecimento"""
        try:
            # Total de documentos
            docs = self.client.table('documents')\
                .select('count', count='exact')\
                .execute()

            # Total de chunks
            chunks = self.client.table('document_chunks')\
                .select('count', count='exact')\
                .execute()

            # Documentos por fonte
            by_source = self.client.table('documents')\
                .select('source_type, count')\
                .execute()

            return {
                'total_documents': docs.count,
                'total_chunks': chunks.count,
                'by_source': by_source.data
            }

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}

    def health_check(self) -> bool:
        """Verifica se conexão está OK"""
        try:
            self.client.table('documents').select('count', count='exact').execute()
            return True
        except:
            return False
