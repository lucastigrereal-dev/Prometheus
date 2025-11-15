"""
MEMORY MANAGER - Sistema de Memória Evolutiva
Memória vetorial com embeddings, cache distribuído e aprendizado contínuo
"""

import json
import time
import hashlib
import pickle
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
from collections import defaultdict, deque
import asyncio
import os

# Importações condicionais
try:
    import redis
    from redis import asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("Redis não disponível - usando memória local")

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("OpenAI não disponível para embeddings")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMER_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMER_AVAILABLE = False
    print("Sentence Transformers não disponível")

try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Supabase não disponível")

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    print("FAISS não disponível - usando busca linear")

logger = logging.getLogger('MemoryManager')

# ============================================================================
# ESTRUTURAS DE DADOS
# ============================================================================

class MemoryType(Enum):
    """Tipos de memória"""
    SHORT_TERM = "short_term"      # Últimas interações (cache)
    LONG_TERM = "long_term"        # Conhecimento permanente
    PROCEDURAL = "procedural"      # Como fazer coisas (templates)
    EPISODIC = "episodic"          # Eventos específicos
    SEMANTIC = "semantic"          # Fatos e conceitos
    WORKING = "working"            # Contexto atual

@dataclass
class Memory:
    """Representa uma memória"""
    id: str
    type: MemoryType
    content: str
    embedding: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    importance: float = 0.5  # 0.0 a 1.0
    decay_rate: float = 0.1  # Taxa de esquecimento
    associations: List[str] = field(default_factory=list)  # IDs relacionados
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        data = asdict(self)
        data['type'] = self.type.value
        data['created_at'] = self.created_at.isoformat()
        data['accessed_at'] = self.accessed_at.isoformat()
        if self.embedding is not None:
            data['embedding'] = self.embedding.tolist()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Memory':
        """Cria do dicionário"""
        data = data.copy()
        data['type'] = MemoryType(data['type'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['accessed_at'] = datetime.fromisoformat(data['accessed_at'])
        if 'embedding' in data and data['embedding']:
            data['embedding'] = np.array(data['embedding'])
        return cls(**data)

@dataclass
class Template:
    """Template de execução bem-sucedida"""
    id: str
    name: str
    description: str
    task_type: str
    steps: List[Dict[str, Any]]
    success_rate: float = 0.0
    usage_count: int = 0
    total_time: float = 0.0
    average_time: float = 0.0
    required_capabilities: List[str] = field(default_factory=list)
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_used: Optional[datetime] = None
    
    def update_stats(self, success: bool, execution_time: float):
        """Atualiza estatísticas do template"""
        self.usage_count += 1
        self.total_time += execution_time
        self.average_time = self.total_time / self.usage_count
        
        if success:
            self.success_rate = ((self.success_rate * (self.usage_count - 1)) + 1) / self.usage_count
        else:
            self.success_rate = (self.success_rate * (self.usage_count - 1)) / self.usage_count
        
        self.last_used = datetime.now()

# ============================================================================
# EMBEDDING MANAGER - Gerenciador de Embeddings
# ============================================================================

class EmbeddingManager:
    """Gerencia criação e busca de embeddings"""
    
    def __init__(self, provider: str = "openai"):
        self.provider = provider
        self.model = None
        self.dimension = 1536  # Padrão OpenAI
        
        self._initialize_model()
    
    def _initialize_model(self):
        """Inicializa modelo de embedding"""
        if self.provider == "openai" and OPENAI_AVAILABLE:
            self.model = "text-embedding-ada-002"
            logger.info("Using OpenAI embeddings")
            
        elif self.provider == "sentence_transformers" and SENTENCE_TRANSFORMER_AVAILABLE:
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            self.dimension = 384
            logger.info("Using Sentence Transformers")
            
        else:
            logger.warning("No embedding model available - using random vectors")
            self.provider = "random"
    
    async def create_embedding(self, text: str) -> np.ndarray:
        """Cria embedding para texto"""
        if self.provider == "openai" and OPENAI_AVAILABLE:
            try:
                response = await asyncio.to_thread(
                    openai.Embedding.create,
                    input=text,
                    model=self.model
                )
                return np.array(response['data'][0]['embedding'])
            except Exception as e:
                logger.error(f"OpenAI embedding failed: {e}")
                return self._random_embedding()
                
        elif self.provider == "sentence_transformers" and self.model:
            try:
                embedding = await asyncio.to_thread(
                    self.model.encode,
                    text
                )
                return embedding
            except Exception as e:
                logger.error(f"Sentence Transformer failed: {e}")
                return self._random_embedding()
                
        else:
            return self._random_embedding()
    
    def _random_embedding(self) -> np.ndarray:
        """Cria embedding aleatório (fallback)"""
        # Usa hash do texto para consistência
        hash_value = hashlib.md5(text.encode()).hexdigest()
        np.random.seed(int(hash_value[:8], 16))
        return np.random.randn(self.dimension)
    
    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calcula similaridade coseno"""
        dot_product = np.dot(vec1, vec2)
        norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)
        if norm_product == 0:
            return 0.0
        return dot_product / norm_product

# ============================================================================
# VECTOR STORE - Armazenamento Vetorial
# ============================================================================

class VectorStore:
    """Armazenamento e busca vetorial"""
    
    def __init__(self, dimension: int = 1536):
        self.dimension = dimension
        self.index = None
        self.id_map: Dict[int, str] = {}  # idx -> memory_id
        self.vectors: List[np.ndarray] = []
        
        self._initialize_index()
    
    def _initialize_index(self):
        """Inicializa índice vetorial"""
        if FAISS_AVAILABLE:
            # Usa FAISS para busca eficiente
            self.index = faiss.IndexFlatL2(self.dimension)
            logger.info("Using FAISS for vector search")
        else:
            # Fallback para busca linear
            logger.info("Using linear search (FAISS not available)")
    
    def add_vector(self, memory_id: str, vector: np.ndarray):
        """Adiciona vetor ao índice"""
        if self.index:
            # FAISS
            idx = len(self.id_map)
            self.id_map[idx] = memory_id
            self.index.add(vector.reshape(1, -1).astype('float32'))
        else:
            # Linear
            self.vectors.append(vector)
            idx = len(self.vectors) - 1
            self.id_map[idx] = memory_id
    
    def search(
        self,
        query_vector: np.ndarray,
        k: int = 10,
        threshold: float = 0.7
    ) -> List[Tuple[str, float]]:
        """Busca k vetores mais similares"""
        
        if self.index:
            # FAISS
            distances, indices = self.index.search(
                query_vector.reshape(1, -1).astype('float32'),
                min(k, len(self.id_map))
            )
            
            results = []
            for idx, dist in zip(indices[0], distances[0]):
                if idx >= 0:  # FAISS retorna -1 para não encontrado
                    similarity = 1.0 / (1.0 + dist)  # Converte distância em similaridade
                    if similarity >= threshold:
                        memory_id = self.id_map[idx]
                        results.append((memory_id, similarity))
            
            return results
            
        else:
            # Busca linear com similaridade coseno
            similarities = []
            for idx, vector in enumerate(self.vectors):
                sim = self._cosine_similarity(query_vector, vector)
                if sim >= threshold:
                    similarities.append((self.id_map[idx], sim))
            
            # Ordena por similaridade
            similarities.sort(key=lambda x: x[1], reverse=True)
            return similarities[:k]
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calcula similaridade coseno"""
        dot_product = np.dot(vec1, vec2)
        norm_product = np.linalg.norm(vec1) * np.linalg.norm(vec2)
        if norm_product == 0:
            return 0.0
        return dot_product / norm_product
    
    def remove_vector(self, memory_id: str):
        """Remove vetor do índice"""
        # Encontra índice
        idx_to_remove = None
        for idx, mid in self.id_map.items():
            if mid == memory_id:
                idx_to_remove = idx
                break
        
        if idx_to_remove is not None:
            del self.id_map[idx_to_remove]
            
            # Se usando lista, remove também
            if not self.index:
                del self.vectors[idx_to_remove]
                
                # Reindexar
                new_map = {}
                for i, (old_idx, mid) in enumerate(self.id_map.items()):
                    if old_idx > idx_to_remove:
                        new_map[i] = mid
                    else:
                        new_map[old_idx] = mid
                self.id_map = new_map

# ============================================================================
# CACHE MANAGER - Gerenciador de Cache
# ============================================================================

class CacheManager:
    """Gerencia cache de memória de curto prazo"""
    
    def __init__(self, redis_config: Dict[str, Any] = None):
        self.redis_client = None
        self.local_cache: Dict[str, Any] = {}
        self.cache_ttl = 3600  # 1 hora padrão
        
        if REDIS_AVAILABLE and redis_config:
            self._initialize_redis(redis_config)
    
    def _initialize_redis(self, config: Dict[str, Any]):
        """Inicializa conexão Redis"""
        try:
            self.redis_client = redis.Redis(
                host=config.get('host', 'localhost'),
                port=config.get('port', 6379),
                db=config.get('db', 0),
                password=config.get('password'),
                decode_responses=True
            )
            self.redis_client.ping()
            logger.info("✅ Redis connected")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            self.redis_client = None
    
    async def get(self, key: str) -> Optional[Any]:
        """Obtém valor do cache"""
        if self.redis_client:
            try:
                value = await asyncio.to_thread(self.redis_client.get, key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.error(f"Redis get failed: {e}")
        
        # Fallback para cache local
        if key in self.local_cache:
            item = self.local_cache[key]
            if item['expires'] > time.time():
                return item['value']
            else:
                del self.local_cache[key]
        
        return None
    
    async def set(self, key: str, value: Any, ttl: int = None):
        """Define valor no cache"""
        ttl = ttl or self.cache_ttl
        
        if self.redis_client:
            try:
                await asyncio.to_thread(
                    self.redis_client.setex,
                    key,
                    ttl,
                    json.dumps(value)
                )
                return
            except Exception as e:
                logger.error(f"Redis set failed: {e}")
        
        # Fallback para cache local
        self.local_cache[key] = {
            'value': value,
            'expires': time.time() + ttl
        }
    
    async def delete(self, key: str):
        """Remove do cache"""
        if self.redis_client:
            try:
                await asyncio.to_thread(self.redis_client.delete, key)
            except:
                pass
        
        if key in self.local_cache:
            del self.local_cache[key]
    
    def clear_expired(self):
        """Limpa itens expirados do cache local"""
        current_time = time.time()
        expired_keys = [
            key for key, item in self.local_cache.items()
            if item['expires'] <= current_time
        ]
        for key in expired_keys:
            del self.local_cache[key]

# ============================================================================
# TEMPLATE LIBRARY - Biblioteca de Templates
# ============================================================================

class TemplateLibrary:
    """Gerencia templates de execução bem-sucedida"""
    
    def __init__(self, storage_path: str = "./templates"):
        self.storage_path = storage_path
        self.templates: Dict[str, Template] = {}
        self.task_type_index: Dict[str, List[str]] = defaultdict(list)
        
        # Cria diretório se não existir
        os.makedirs(storage_path, exist_ok=True)
        
        # Carrega templates existentes
        self._load_templates()
    
    def _load_templates(self):
        """Carrega templates do disco"""
        template_files = [f for f in os.listdir(self.storage_path) if f.endswith('.json')]
        
        for file in template_files:
            try:
                with open(os.path.join(self.storage_path, file), 'r') as f:
                    data = json.load(f)
                    template = Template(**data)
                    self.add_template(template)
            except Exception as e:
                logger.error(f"Failed to load template {file}: {e}")
    
    def add_template(self, template: Template):
        """Adiciona template à biblioteca"""
        self.templates[template.id] = template
        self.task_type_index[template.task_type].append(template.id)
        
        # Salva no disco
        self._save_template(template)
    
    def _save_template(self, template: Template):
        """Salva template no disco"""
        file_path = os.path.join(self.storage_path, f"{template.id}.json")
        
        data = {
            'id': template.id,
            'name': template.name,
            'description': template.description,
            'task_type': template.task_type,
            'steps': template.steps,
            'success_rate': template.success_rate,
            'usage_count': template.usage_count,
            'total_time': template.total_time,
            'average_time': template.average_time,
            'required_capabilities': template.required_capabilities,
            'parameters': template.parameters,
            'created_at': template.created_at.isoformat(),
            'last_used': template.last_used.isoformat() if template.last_used else None
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def find_template(
        self,
        task_type: str,
        min_success_rate: float = 0.7
    ) -> Optional[Template]:
        """Encontra melhor template para tipo de tarefa"""
        
        candidates = []
        for template_id in self.task_type_index.get(task_type, []):
            template = self.templates[template_id]
            if template.success_rate >= min_success_rate:
                candidates.append(template)
        
        if not candidates:
            return None
        
        # Retorna template com melhor success rate
        return max(candidates, key=lambda t: t.success_rate)
    
    def create_from_execution(
        self,
        task_type: str,
        steps: List[Dict[str, Any]],
        execution_time: float,
        success: bool
    ) -> Template:
        """Cria template a partir de execução"""
        import uuid
        
        template = Template(
            id=str(uuid.uuid4()),
            name=f"Template for {task_type}",
            description=f"Auto-generated template for {task_type} tasks",
            task_type=task_type,
            steps=steps,
            success_rate=1.0 if success else 0.0,
            usage_count=1,
            total_time=execution_time,
            average_time=execution_time
        )
        
        self.add_template(template)
        return template

# ============================================================================
# MEMORY MANAGER - Gerenciador Principal
# ============================================================================

class MemoryManager:
    """
    Gerenciador principal de memória do Prometheus
    Integra todos os subsistemas de memória
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Subsistemas
        self.embedding_manager = EmbeddingManager(
            provider=self.config.get('embedding_provider', 'openai')
        )
        self.vector_store = VectorStore(
            dimension=self.embedding_manager.dimension
        )
        self.cache_manager = CacheManager(
            redis_config=self.config.get('redis')
        )
        self.template_library = TemplateLibrary(
            storage_path=self.config.get('template_path', './templates')
        )
        
        # Armazenamento de memórias
        self.memories: Dict[str, Memory] = {}
        self.type_index: Dict[MemoryType, List[str]] = defaultdict(list)
        
        # Configurações
        self.max_short_term = 1000
        self.max_long_term = 10000
        self.similarity_threshold = 0.7
        self.decay_enabled = True
        
        # Supabase para persistência
        self.supabase_client = None
        if SUPABASE_AVAILABLE and 'supabase' in self.config:
            self._initialize_supabase()
        
        logger.info("✅ Memory Manager initialized")
    
    def _initialize_supabase(self):
        """Inicializa cliente Supabase"""
        try:
            self.supabase_client = create_client(
                self.config['supabase']['url'],
                self.config['supabase']['key']
            )
            logger.info("✅ Supabase connected")
        except Exception as e:
            logger.error(f"Supabase initialization failed: {e}")
    
    async def store(
        self,
        content: str,
        memory_type: MemoryType,
        metadata: Dict[str, Any] = None,
        importance: float = 0.5
    ) -> Memory:
        """Armazena nova memória"""
        import uuid
        
        # Cria memória
        memory = Memory(
            id=str(uuid.uuid4()),
            type=memory_type,
            content=content,
            metadata=metadata or {},
            importance=importance
        )
        
        # Cria embedding
        memory.embedding = await self.embedding_manager.create_embedding(content)
        
        # Adiciona ao vector store
        self.vector_store.add_vector(memory.id, memory.embedding)
        
        # Armazena localmente
        self.memories[memory.id] = memory
        self.type_index[memory_type].append(memory.id)
        
        # Cache se short-term
        if memory_type == MemoryType.SHORT_TERM:
            await self.cache_manager.set(
                f"memory:{memory.id}",
                memory.to_dict(),
                ttl=3600  # 1 hora
            )
        
        # Persiste se long-term
        if memory_type == MemoryType.LONG_TERM and self.supabase_client:
            await self._persist_to_supabase(memory)
        
        # Gerencia limites
        await self._manage_memory_limits()
        
        logger.info(f"Stored {memory_type.value} memory: {memory.id}")
        return memory
    
    async def recall(
        self,
        query: str,
        memory_types: List[MemoryType] = None,
        limit: int = 10
    ) -> List[Memory]:
        """Recupera memórias relevantes"""
        
        # Verifica cache primeiro
        cache_key = f"recall:{hashlib.md5(query.encode()).hexdigest()}"
        cached = await self.cache_manager.get(cache_key)
        if cached:
            return [Memory.from_dict(m) for m in cached]
        
        # Cria embedding da query
        query_embedding = await self.embedding_manager.create_embedding(query)
        
        # Busca vetorial
        similar = self.vector_store.search(
            query_embedding,
            k=limit * 2,  # Busca mais para filtrar depois
            threshold=self.similarity_threshold
        )
        
        # Filtra por tipo se especificado
        results = []
        for memory_id, similarity in similar:
            if memory_id in self.memories:
                memory = self.memories[memory_id]
                
                if memory_types and memory.type not in memory_types:
                    continue
                
                # Atualiza acesso
                memory.accessed_at = datetime.now()
                memory.access_count += 1
                
                # Aplica decay se habilitado
                if self.decay_enabled:
                    self._apply_decay(memory)
                
                results.append(memory)
                
                if len(results) >= limit:
                    break
        
        # Cacheia resultado
        await self.cache_manager.set(
            cache_key,
            [m.to_dict() for m in results],
            ttl=600  # 10 minutos
        )
        
        return results
    
    def _apply_decay(self, memory: Memory):
        """Aplica decaimento à importância da memória"""
        time_since_access = (datetime.now() - memory.accessed_at).days
        decay_factor = np.exp(-memory.decay_rate * time_since_access)
        memory.importance *= decay_factor
        
        # Reforço por acesso
        memory.importance = min(1.0, memory.importance * (1 + 0.1 * np.log1p(memory.access_count)))
    
    async def consolidate(self):
        """Consolida memórias similares"""
        # Agrupa memórias por tipo
        for memory_type in MemoryType:
            type_memories = [
                self.memories[mid]
                for mid in self.type_index[memory_type]
                if mid in self.memories
            ]
            
            if len(type_memories) < 2:
                continue
            
            # Encontra grupos similares
            groups = []
            processed = set()
            
            for memory in type_memories:
                if memory.id in processed:
                    continue
                
                # Busca similares
                similar = self.vector_store.search(
                    memory.embedding,
                    k=5,
                    threshold=0.9  # Alta similaridade para consolidação
                )
                
                group = [memory]
                for sim_id, _ in similar:
                    if sim_id != memory.id and sim_id not in processed:
                        if sim_id in self.memories:
                            group.append(self.memories[sim_id])
                            processed.add(sim_id)
                
                if len(group) > 1:
                    groups.append(group)
                processed.add(memory.id)
            
            # Consolida grupos
            for group in groups:
                await self._consolidate_group(group)
    
    async def _consolidate_group(self, memories: List[Memory]):
        """Consolida grupo de memórias similares"""
        if len(memories) < 2:
            return
        
        # Cria memória consolidada
        combined_content = "\n".join([m.content for m in memories])
        combined_metadata = {}
        for m in memories:
            combined_metadata.update(m.metadata)
        
        # Calcula importância média ponderada
        total_access = sum(m.access_count for m in memories)
        avg_importance = sum(m.importance * m.access_count for m in memories) / max(total_access, 1)
        
        # Cria nova memória consolidada
        consolidated = await self.store(
            content=f"[CONSOLIDATED] {combined_content[:500]}...",
            memory_type=memories[0].type,
            metadata={
                **combined_metadata,
                'consolidated_from': [m.id for m in memories],
                'consolidation_date': datetime.now().isoformat()
            },
            importance=avg_importance
        )
        
        # Remove memórias originais
        for memory in memories:
            await self.forget(memory.id)
        
        logger.info(f"Consolidated {len(memories)} memories into {consolidated.id}")
    
    async def forget(self, memory_id: str):
        """Esquece uma memória"""
        if memory_id in self.memories:
            memory = self.memories[memory_id]
            
            # Remove do vector store
            self.vector_store.remove_vector(memory_id)
            
            # Remove do cache
            await self.cache_manager.delete(f"memory:{memory_id}")
            
            # Remove dos índices
            self.type_index[memory.type].remove(memory_id)
            
            # Remove do armazenamento
            del self.memories[memory_id]
            
            logger.info(f"Forgot memory: {memory_id}")
    
    async def learn_from_execution(
        self,
        task_type: str,
        steps: List[Dict[str, Any]],
        result: Any,
        success: bool,
        execution_time: float
    ):
        """Aprende com execução de tarefa"""
        
        # Cria memória episódica
        episode_content = json.dumps({
            'task_type': task_type,
            'steps': steps,
            'result': str(result)[:500],
            'success': success,
            'execution_time': execution_time
        })
        
        await self.store(
            content=episode_content,
            memory_type=MemoryType.EPISODIC,
            metadata={
                'task_type': task_type,
                'success': success,
                'execution_time': execution_time
            },
            importance=0.8 if success else 0.3
        )
        
        # Se sucesso, considera criar template
        if success:
            existing_template = self.template_library.find_template(task_type)
            
            if existing_template:
                # Atualiza template existente
                existing_template.update_stats(success, execution_time)
            else:
                # Cria novo template se taxa de sucesso boa
                self.template_library.create_from_execution(
                    task_type=task_type,
                    steps=steps,
                    execution_time=execution_time,
                    success=success
                )
    
    async def _manage_memory_limits(self):
        """Gerencia limites de memória"""
        # Limita short-term
        short_term_ids = self.type_index[MemoryType.SHORT_TERM]
        if len(short_term_ids) > self.max_short_term:
            # Remove mais antigas
            memories_to_remove = sorted(
                [self.memories[mid] for mid in short_term_ids if mid in self.memories],
                key=lambda m: m.accessed_at
            )[:len(short_term_ids) - self.max_short_term]
            
            for memory in memories_to_remove:
                await self.forget(memory.id)
        
        # Limita long-term
        long_term_ids = self.type_index[MemoryType.LONG_TERM]
        if len(long_term_ids) > self.max_long_term:
            # Remove menos importantes
            memories_to_remove = sorted(
                [self.memories[mid] for mid in long_term_ids if mid in self.memories],
                key=lambda m: m.importance
            )[:len(long_term_ids) - self.max_long_term]
            
            for memory in memories_to_remove:
                await self.forget(memory.id)
    
    async def _persist_to_supabase(self, memory: Memory):
        """Persiste memória no Supabase"""
        if not self.supabase_client:
            return
        
        try:
            data = memory.to_dict()
            # Converte embedding para string
            if 'embedding' in data:
                data['embedding'] = json.dumps(data['embedding'])
            
            await asyncio.to_thread(
                self.supabase_client.table('memories').insert(data).execute
            )
            
        except Exception as e:
            logger.error(f"Failed to persist to Supabase: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da memória"""
        stats = {
            'total_memories': len(self.memories),
            'by_type': {},
            'cache_size': len(self.cache_manager.local_cache),
            'templates': len(self.template_library.templates),
            'vector_store_size': len(self.vector_store.id_map)
        }
        
        for memory_type in MemoryType:
            stats['by_type'][memory_type.value] = len(self.type_index[memory_type])
        
        return stats

# ============================================================================
# EXEMPLO DE USO
# ============================================================================

async def example_usage():
    """Demonstra uso do Memory Manager"""
    
    # Configuração
    config = {
        'embedding_provider': 'sentence_transformers',  # ou 'openai'
        'redis': {
            'host': 'localhost',
            'port': 6379,
            'db': 0
        },
        'template_path': './templates'
    }
    
    # Cria manager
    manager = MemoryManager(config)
    
    # Armazena memórias
    print("Armazenando memórias...")
    
    memory1 = await manager.store(
        content="O cliente João Silva precisa de um site para sua empresa de consultoria",
        memory_type=MemoryType.LONG_TERM,
        metadata={'client': 'João Silva', 'project': 'website'},
        importance=0.8
    )
    
    memory2 = await manager.store(
        content="Sites de consultoria geralmente precisam de páginas sobre serviços, equipe e contato",
        memory_type=MemoryType.SEMANTIC,
        metadata={'domain': 'web_development', 'type': 'consultancy'},
        importance=0.7
    )
    
    memory3 = await manager.store(
        content="Última vez criamos site com React e TailwindCSS em 3 dias",
        memory_type=MemoryType.EPISODIC,
        metadata={'technology': 'React', 'duration': '3 days'},
        importance=0.6
    )
    
    # Recupera memórias relevantes
    print("\n🔍 Buscando memórias sobre 'criar site consultoria'...")
    
    relevant = await manager.recall(
        query="criar site para consultoria",
        memory_types=[MemoryType.LONG_TERM, MemoryType.SEMANTIC],
        limit=5
    )
    
    for memory in relevant:
        print(f"  - [{memory.type.value}] {memory.content[:100]}...")
        print(f"    Importância: {memory.importance:.2f}, Acessos: {memory.access_count}")
    
    # Aprende com execução
    print("\n📚 Aprendendo com execução...")
    
    await manager.learn_from_execution(
        task_type="create_website",
        steps=[
            {'action': 'analyze_requirements', 'duration': 10},
            {'action': 'create_design', 'duration': 30},
            {'action': 'develop_frontend', 'duration': 120},
            {'action': 'test_deploy', 'duration': 20}
        ],
        result="Website successfully created",
        success=True,
        execution_time=180
    )
    
    # Estatísticas
    print("\n📊 Estatísticas da memória:")
    stats = manager.get_stats()
    print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    asyncio.run(example_usage())
