# -*- coding: utf-8 -*-
"""
CHUNK PROCESSOR - Quebra Inteligente + Embeddings Profissionais

Funcionalidades:
- Quebra texto em chunks de 500-700 palavras
- Preserva parágrafos e contexto
- Gera embeddings com OpenAI ada-002
- Calcula tokens (para billing)
- Hash para deduplicação
"""

import os
import logging
import hashlib
from typing import List, Dict
from openai import OpenAI
import tiktoken

logger = logging.getLogger(__name__)


class ChunkProcessor:
    """Quebra textos em chunks e gera embeddings profissionais"""

    def __init__(
        self,
        chunk_size: int = 600,          # palavras
        chunk_overlap: int = 50,        # palavras de overlap
        max_tokens: int = 7000,         # limite de tokens (OpenAI ada-002 max = 8192)
        model: str = "text-embedding-ada-002"
    ):
        """
        Inicializa processador de chunks

        Args:
            chunk_size: Tamanho alvo do chunk (palavras)
            chunk_overlap: Overlap entre chunks (contexto)
            max_tokens: Limite máximo de tokens por chunk
            model: Modelo de embedding da OpenAI
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.max_tokens = max_tokens
        self.model = model

        # Cliente OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set in .env file")

        self.openai_client = OpenAI(api_key=api_key)

        # Tokenizer (para contagem precisa)
        self.encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

        logger.info(f"ChunkProcessor initialized: {chunk_size} words, overlap {chunk_overlap}")

    def split_into_chunks(
        self,
        text: str,
        metadata: Dict = None,
        preserve_paragraphs: bool = True
    ) -> List[Dict]:
        """
        Quebra texto em chunks inteligentes

        Args:
            text: Texto completo a ser quebrado
            metadata: Metadados a anexar em cada chunk
            preserve_paragraphs: Se True, evita quebrar no meio de parágrafos

        Returns:
            Lista de dicts com:
                - chunk_index (int)
                - content (str)
                - content_hash (str)
                - tokens (int)
                - metadata (dict)
        """
        chunks = []

        if preserve_paragraphs:
            # Quebra por parágrafos primeiro
            paragraphs = text.split('\n\n')
            current_chunk = []
            current_words = 0

            for para in paragraphs:
                para_words = len(para.split())

                # Se parágrafo sozinho já é grande, quebra ele
                if para_words > self.chunk_size * 1.5:
                    # Salva chunk atual
                    if current_chunk:
                        chunks.append(self._create_chunk(
                            ' '.join(current_chunk),
                            len(chunks),
                            metadata
                        ))
                        current_chunk = []
                        current_words = 0

                    # Quebra parágrafo grande em sentenças
                    sentences = para.split('. ')
                    for sent in sentences:
                        sent_words = len(sent.split())

                        if current_words + sent_words > self.chunk_size:
                            if current_chunk:
                                chunks.append(self._create_chunk(
                                    ' '.join(current_chunk),
                                    len(chunks),
                                    metadata
                                ))
                            current_chunk = [sent]
                            current_words = sent_words
                        else:
                            current_chunk.append(sent)
                            current_words += sent_words

                # Se adicionar parágrafo ultrapassa limite, fecha chunk
                elif current_words + para_words > self.chunk_size:
                    if current_chunk:
                        chunks.append(self._create_chunk(
                            ' '.join(current_chunk),
                            len(chunks),
                            metadata
                        ))
                    current_chunk = [para]
                    current_words = para_words
                else:
                    current_chunk.append(para)
                    current_words += para_words

            # Último chunk
            if current_chunk:
                chunks.append(self._create_chunk(
                    ' '.join(current_chunk),
                    len(chunks),
                    metadata
                ))

        else:
            # Quebra simples por palavras
            words = text.split()

            for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
                chunk_words = words[i:i + self.chunk_size]
                chunk_text = ' '.join(chunk_words)

                chunks.append(self._create_chunk(
                    chunk_text,
                    len(chunks),
                    metadata
                ))

        logger.info(f"Split text into {len(chunks)} chunks (avg {sum(c['tokens'] for c in chunks) // len(chunks)} tokens)")
        return chunks

    def _create_chunk(self, text: str, index: int, metadata: Dict = None) -> Dict:
        """Cria dict de chunk com metadados"""
        # Hash para deduplicação
        content_hash = hashlib.md5(text.encode('utf-8')).hexdigest()

        # Conta tokens
        tokens = len(self.encoding.encode(text))

        # VALIDAÇÃO: Se exceder limite, trunca
        if tokens > self.max_tokens:
            logger.warning(f"Chunk {index} has {tokens} tokens, truncating to {self.max_tokens}")
            # Trunca texto para caber no limite
            encoded = self.encoding.encode(text)[:self.max_tokens]
            text = self.encoding.decode(encoded)
            tokens = len(encoded)
            content_hash = hashlib.md5(text.encode('utf-8')).hexdigest()

        return {
            'chunk_index': index,
            'content': text,
            'content_hash': content_hash,
            'tokens': tokens,
            'metadata': metadata or {},
            'embedding': None  # Será preenchido depois
        }

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Gera embedding profissional usando OpenAI ada-002

        Args:
            text: Texto para gerar embedding

        Returns:
            Vetor de 1536 dimensões
        """
        try:
            response = self.openai_client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def process_chunks(
        self,
        chunks: List[Dict],
        show_progress: bool = False
    ) -> List[Dict]:
        """
        Adiciona embeddings a cada chunk

        Args:
            chunks: Lista de chunks sem embeddings
            show_progress: Se True, mostra progresso

        Returns:
            Lista de chunks com embeddings
        """
        total = len(chunks)

        for i, chunk in enumerate(chunks):
            if show_progress:
                print(f"\rGenerating embeddings: {i+1}/{total}", end='', flush=True)

            # Gera embedding
            chunk['embedding'] = await self.generate_embedding(chunk['content'])

        if show_progress:
            print()  # Nova linha

        logger.info(f"Generated {total} embeddings")
        return chunks

    def estimate_cost(self, text: str) -> float:
        """
        Estima custo de embeddings para o texto

        Args:
            text: Texto completo

        Returns:
            Custo estimado em USD
        """
        # OpenAI ada-002: $0.0001 / 1K tokens
        tokens = len(self.encoding.encode(text))
        cost = (tokens / 1000) * 0.0001
        return cost


# Exemplo de uso
if __name__ == "__main__":
    import asyncio

    processor = ChunkProcessor(chunk_size=500)

    test_text = """
    Lorem ipsum dolor sit amet, consectetur adipiscing elit.
    Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

    Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris.
    Duis aute irure dolor in reprehenderit in voluptate velit esse.
    """ * 50  # Texto grande para múltiplos chunks

    # Quebra em chunks
    chunks = processor.split_into_chunks(test_text, metadata={'source': 'test'})
    print(f"Created {len(chunks)} chunks")

    # Estima custo
    cost = processor.estimate_cost(test_text)
    print(f"Estimated cost: ${cost:.4f}")
