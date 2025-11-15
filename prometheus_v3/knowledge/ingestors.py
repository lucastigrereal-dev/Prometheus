# -*- coding: utf-8 -*-
"""
INGESTORES - Importam conhecimento de múltiplas fontes

- PerplexityIngestor: Busca em Perplexity API
- ClaudeHistoryIngestor: Importa histórico Claude Desktop
- GPTHistoryIngestor: Importa histórico ChatGPT
"""

import asyncio
import logging
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod

from .knowledge_bank import Knowledge

logger = logging.getLogger(__name__)


class BaseIngestor(ABC):
    """Classe base para ingestores"""

    def __init__(self, name: str, data_dir: Path = None):
        self.name = name

        if data_dir is None:
            data_dir = Path(__file__).parent.parent.parent / 'data' / 'ingestors' / name
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.last_sync_file = self.data_dir / 'last_sync.txt'

    def _get_last_sync(self) -> Optional[datetime]:
        """Retorna timestamp do último sync"""
        if not self.last_sync_file.exists():
            return None

        try:
            with open(self.last_sync_file, 'r') as f:
                timestamp_str = f.read().strip()
                return datetime.fromisoformat(timestamp_str)
        except Exception as e:
            logger.warning(f"Error reading last sync: {e}")
            return None

    def _save_last_sync(self, timestamp: datetime = None):
        """Salva timestamp do último sync"""
        if timestamp is None:
            timestamp = datetime.now()

        try:
            with open(self.last_sync_file, 'w') as f:
                f.write(timestamp.isoformat())
        except Exception as e:
            logger.warning(f"Error saving last sync: {e}")

    @abstractmethod
    async def fetch_new(self) -> List[Knowledge]:
        """
        Busca novos chunks desde último sync

        Returns:
            Lista de Knowledge objects
        """
        pass


class PerplexityIngestor(BaseIngestor):
    """
    Ingestor que busca conhecimento em Perplexity

    Requer PERPLEXITY_API_KEY em variáveis de ambiente
    """

    def __init__(
        self,
        api_key: str = None,
        topics: List[str] = None,
        max_per_topic: int = 5
    ):
        super().__init__('perplexity')

        self.api_key = api_key or os.getenv('PERPLEXITY_API_KEY')
        self.max_per_topic = max_per_topic

        # Topics padrão se não fornecidos
        if topics is None:
            topics = [
                'python best practices 2024',
                'fastapi patterns and examples',
                'async programming python',
                'AI agent architectures',
                'playwright automation'
            ]
        self.topics = topics

        logger.info(f"PerplexityIngestor initialized with {len(topics)} topics")

    async def fetch_new(self) -> List[Knowledge]:
        """
        Busca em Perplexity sobre os tópicos configurados

        Returns:
            Lista de Knowledge objects
        """
        chunks = []

        if not self.api_key:
            logger.warning("PERPLEXITY_API_KEY not set - returning mock data")
            # Retorna dados mock para demonstração
            return self._get_mock_data()

        logger.info(f"Fetching from Perplexity: {len(self.topics)} topics...")

        for topic in self.topics:
            try:
                # TODO: Implementar chamada real para Perplexity API
                # Por ora, usando mock data
                topic_chunks = await self._fetch_topic(topic)
                chunks.extend(topic_chunks)

            except Exception as e:
                logger.error(f"Error fetching topic '{topic}': {e}")

        self._save_last_sync()
        logger.info(f"Perplexity: fetched {len(chunks)} chunks")

        return chunks

    async def _fetch_topic(self, topic: str) -> List[Knowledge]:
        """Busca um tópico específico"""
        # TODO: Implementar chamada real
        # Por ora, retorna mock
        return []

    def _get_mock_data(self) -> List[Knowledge]:
        """Retorna dados mock para demonstração"""
        mock_topics = {
            'python best practices': 'Use type hints for better code clarity. Follow PEP 8 style guide. Use dataclasses for data containers. Prefer composition over inheritance.',
            'fastapi patterns': 'Use dependency injection for database sessions. Implement proper error handlers. Use Pydantic models for validation. Structure routes in separate modules.',
            'async programming': 'Use asyncio.gather for concurrent tasks. Avoid blocking operations in async functions. Use asyncio.create_task for background tasks. Handle cancellation properly.'
        }

        chunks = []
        for topic, content in mock_topics.items():
            chunk = Knowledge(
                content=f"Topic: {topic}\n\n{content}",
                metadata={
                    'source_type': 'perplexity',
                    'topic': topic,
                    'mock': True
                },
                source='perplexity'
            )
            chunks.append(chunk)

        return chunks


class ClaudeHistoryIngestor(BaseIngestor):
    """
    Ingestor que importa histórico de conversas do Claude Desktop

    Procura em locais comuns do Claude Desktop
    """

    def __init__(self, conversations_path: Path = None):
        super().__init__('claude_history')

        # Tenta encontrar diretório de conversas do Claude
        if conversations_path is None:
            conversations_path = self._find_claude_conversations()

        self.conversations_path = conversations_path

        logger.info(f"ClaudeHistoryIngestor initialized: {conversations_path}")

    def _find_claude_conversations(self) -> Optional[Path]:
        """
        Tenta encontrar diretório de conversas do Claude Desktop

        Locais comuns:
        - Windows: %APPDATA%/Claude/conversations
        - Mac: ~/Library/Application Support/Claude/conversations
        - Linux: ~/.config/Claude/conversations
        """
        possible_paths = []

        # Windows
        if os.name == 'nt':
            appdata = Path(os.getenv('APPDATA', ''))
            possible_paths.append(appdata / 'Claude' / 'conversations')

        # Mac/Linux
        else:
            home = Path.home()
            possible_paths.extend([
                home / 'Library' / 'Application Support' / 'Claude' / 'conversations',
                home / '.config' / 'Claude' / 'conversations'
            ])

        for path in possible_paths:
            if path.exists():
                logger.info(f"Found Claude conversations at: {path}")
                return path

        logger.warning("Claude conversations directory not found")
        return None

    async def fetch_new(self) -> List[Knowledge]:
        """
        Importa conversas do Claude Desktop

        Returns:
            Lista de Knowledge objects
        """
        chunks = []

        if not self.conversations_path or not self.conversations_path.exists():
            logger.warning("Claude conversations path not available - returning mock")
            return self._get_mock_data()

        logger.info(f"Scanning Claude conversations in: {self.conversations_path}")

        # Procura arquivos JSON
        for conv_file in self.conversations_path.glob('*.json'):
            try:
                chunks_from_file = await self._process_conversation_file(conv_file)
                chunks.extend(chunks_from_file)

            except Exception as e:
                logger.error(f"Error processing {conv_file.name}: {e}")

        self._save_last_sync()
        logger.info(f"Claude History: fetched {len(chunks)} chunks")

        return chunks

    async def _process_conversation_file(self, file_path: Path) -> List[Knowledge]:
        """Processa um arquivo de conversa"""
        chunks = []

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                conversation = json.load(f)

            # Extrai mensagens do assistente com código
            messages = conversation.get('messages', [])

            for msg in messages:
                if msg.get('role') == 'assistant':
                    content = msg.get('content', '')

                    # Filtra mensagens relevantes (com código, explicações técnicas, etc)
                    if self._is_relevant(content):
                        chunk = Knowledge(
                            content=content,
                            metadata={
                                'source_type': 'claude_history',
                                'file': file_path.name,
                                'timestamp': msg.get('timestamp', datetime.now().isoformat())
                            },
                            source='claude_history'
                        )
                        chunks.append(chunk)

        except Exception as e:
            logger.error(f"Error reading conversation file: {e}")

        return chunks

    def _is_relevant(self, content: str) -> bool:
        """Verifica se conteúdo é relevante para armazenar"""
        # Heurísticas simples
        relevance_indicators = [
            '```',  # Blocos de código
            'def ',  # Definições Python
            'class ',  # Classes
            'async ',  # Código assíncrono
            'import ',  # Imports
            'Example:',  # Exemplos
            'Here\'s how',  # Explicações
        ]

        content_lower = content.lower()

        # Precisa ter pelo menos um indicador
        has_indicator = any(ind.lower() in content_lower for ind in relevance_indicators)

        # Não deve ser muito curto
        long_enough = len(content) > 100

        return has_indicator and long_enough

    def _get_mock_data(self) -> List[Knowledge]:
        """Retorna dados mock"""
        mock_conversations = [
            {
                'content': '''Here's how to create a FastAPI endpoint:

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/status")
async def get_status():
    return {"status": "ok", "version": "1.0"}
```

This creates a simple health check endpoint.''',
                'topic': 'fastapi endpoint'
            },
            {
                'content': '''To handle async operations properly:

```python
import asyncio

async def process_items(items):
    tasks = [process_item(item) for item in items]
    results = await asyncio.gather(*tasks)
    return results
```

Use asyncio.gather for concurrent processing.''',
                'topic': 'async patterns'
            }
        ]

        chunks = []
        for conv in mock_conversations:
            chunk = Knowledge(
                content=conv['content'],
                metadata={
                    'source_type': 'claude_history',
                    'topic': conv['topic'],
                    'mock': True
                },
                source='claude_history'
            )
            chunks.append(chunk)

        return chunks


class GPTHistoryIngestor(BaseIngestor):
    """
    Ingestor que importa histórico do ChatGPT

    Requer export JSON do ChatGPT (https://chat.openai.com/settings/data_controls)
    """

    def __init__(self, export_file: Path = None):
        super().__init__('gpt_history')

        if export_file is None:
            # Procura em locais comuns
            export_file = self._find_gpt_export()

        self.export_file = export_file

        logger.info(f"GPTHistoryIngestor initialized: {export_file}")

    def _find_gpt_export(self) -> Optional[Path]:
        """
        Procura arquivo de export do ChatGPT

        Procura em:
        - Downloads
        - Documents
        - data/exports
        """
        possible_locations = [
            Path.home() / 'Downloads' / 'conversations.json',
            Path.home() / 'Documents' / 'chatgpt_export.json',
            Path(__file__).parent.parent.parent / 'data' / 'exports' / 'chatgpt.json'
        ]

        for path in possible_locations:
            if path.exists():
                logger.info(f"Found ChatGPT export at: {path}")
                return path

        logger.warning("ChatGPT export file not found")
        return None

    async def fetch_new(self) -> List[Knowledge]:
        """
        Importa conversas do export do ChatGPT

        Returns:
            Lista de Knowledge objects
        """
        chunks = []

        if not self.export_file or not self.export_file.exists():
            logger.warning("ChatGPT export file not available - returning mock")
            return self._get_mock_data()

        logger.info(f"Processing ChatGPT export: {self.export_file}")

        try:
            with open(self.export_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Formato do export do ChatGPT
            conversations = data if isinstance(data, list) else [data]

            for conversation in conversations:
                chunks_from_conv = self._process_conversation(conversation)
                chunks.extend(chunks_from_conv)

        except Exception as e:
            logger.error(f"Error processing ChatGPT export: {e}")

        self._save_last_sync()
        logger.info(f"GPT History: fetched {len(chunks)} chunks")

        return chunks

    def _process_conversation(self, conversation: Dict) -> List[Knowledge]:
        """Processa uma conversa do export"""
        chunks = []

        try:
            # Estrutura do export pode variar
            messages = conversation.get('mapping', {})

            for msg_id, msg_data in messages.items():
                message = msg_data.get('message', {})

                if message.get('author', {}).get('role') == 'assistant':
                    content = message.get('content', {}).get('parts', [''])[0]

                    # Filtra conteúdo relevante
                    if self._is_programming_related(content):
                        chunk = Knowledge(
                            content=content,
                            metadata={
                                'source_type': 'gpt_history',
                                'conversation_id': conversation.get('id'),
                                'model': message.get('metadata', {}).get('model_slug', 'unknown')
                            },
                            source='gpt_history'
                        )
                        chunks.append(chunk)

        except Exception as e:
            logger.error(f"Error processing conversation: {e}")

        return chunks

    def _is_programming_related(self, content: str) -> bool:
        """Verifica se conteúdo é relacionado a programação"""
        if not content or len(content) < 100:
            return False

        programming_keywords = [
            'python', 'javascript', 'code', 'function', 'class',
            'def ', 'async', 'await', 'import', 'from ',
            '```', 'fastapi', 'django', 'react', 'node'
        ]

        content_lower = content.lower()
        return any(kw in content_lower for kw in programming_keywords)

    def _get_mock_data(self) -> List[Knowledge]:
        """Retorna dados mock"""
        mock_data = [
            {
                'content': '''Here's a Python decorator pattern:

```python
def retry(max_attempts=3):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_attempts - 1:
                        raise
            return wrapper
        return decorator
```

Use this to automatically retry failed operations.''',
                'model': 'gpt-4'
            }
        ]

        chunks = []
        for item in mock_data:
            chunk = Knowledge(
                content=item['content'],
                metadata={
                    'source_type': 'gpt_history',
                    'model': item['model'],
                    'mock': True
                },
                source='gpt_history'
            )
            chunks.append(chunk)

        return chunks
