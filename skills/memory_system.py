"""
PROMETHEUS MEMORY SYSTEM - Sistema de Memória Contextual Persistente
Implementa memória de longo prazo com embeddings, aprendizado de padrões e perfil comportamental
"""

import json
import sqlite3
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, Counter
import hashlib
import pickle
import os
import re
from pathlib import Path
import logging

# Para embeddings locais (alternativa ao Pinecone/Weaviate)
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    print("sentence-transformers não instalado. Usando fallback sem embeddings.")

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Memory:
    """Estrutura de uma memória"""
    id: str
    timestamp: datetime
    command: str
    response: str
    skill_used: str
    context: Dict[str, Any]
    embedding: Optional[List[float]] = None
    user_satisfaction: Optional[float] = None
    execution_time: float = 0.0
    error: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if not self.id:
            self.id = self._generate_id()
    
    def _generate_id(self) -> str:
        """Gera ID único baseado no conteúdo"""
        content = f"{self.timestamp}{self.command}{self.skill_used}"
        return hashlib.md5(content.encode()).hexdigest()

@dataclass
class UserPattern:
    """Padrão de comportamento do usuário"""
    pattern_type: str  # 'daily', 'weekly', 'command_sequence', 'preference'
    pattern_data: Dict[str, Any]
    frequency: int
    confidence: float
    last_seen: datetime
    predictions: List[str]

class PrometheusMemorySystem:
    """Sistema de Memória Contextual com Aprendizado"""
    
    def __init__(self, db_path: str = "prometheus_memory.db", 
                 embeddings_model: str = "all-MiniLM-L6-v2"):
        """
        Inicializa o sistema de memória
        
        Args:
            db_path: Caminho do banco SQLite
            embeddings_model: Modelo de embeddings para usar
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # Inicializa modelo de embeddings se disponível
        self.embeddings_model = None
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embeddings_model = SentenceTransformer(embeddings_model)
                logger.info(f"Modelo de embeddings {embeddings_model} carregado")
            except Exception as e:
                logger.warning(f"Erro ao carregar modelo de embeddings: {e}")
        
        # Cria tabelas
        self._create_tables()
        
        # Caches em memória
        self.short_term_memory: List[Memory] = []  # Últimas 100 interações
        self.working_patterns: Dict[str, UserPattern] = {}  # Padrões ativos
        self.command_frequency: Counter = Counter()  # Frequência de comandos
        self.skill_performance: Dict[str, Dict] = defaultdict(lambda: {
            'success_rate': 0.0,
            'avg_time': 0.0,
            'total_uses': 0
        })
        
        # Carrega dados históricos
        self._load_historical_data()
        
        # Análise de padrões
        self.pattern_analyzer = PatternAnalyzer(self)
        
    def _create_tables(self):
        """Cria tabelas no banco de dados"""
        
        # Tabela de memórias
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id TEXT PRIMARY KEY,
                timestamp REAL,
                command TEXT,
                response TEXT,
                skill_used TEXT,
                context TEXT,
                embedding BLOB,
                user_satisfaction REAL,
                execution_time REAL,
                error TEXT,
                tags TEXT
            )
        """)
        
        # Tabela de padrões
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS patterns (
                id TEXT PRIMARY KEY,
                pattern_type TEXT,
                pattern_data TEXT,
                frequency INTEGER,
                confidence REAL,
                last_seen REAL,
                predictions TEXT
            )
        """)
        
        # Tabela de perfil do usuário
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profile (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at REAL
            )
        """)
        
        # Índices para performance
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON memories(timestamp)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_skill ON memories(skill_used)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_command ON memories(command)")
        
        self.conn.commit()
    
    def remember(self, command: str, response: str, skill_used: str, 
                 context: Dict[str, Any], execution_time: float = 0.0,
                 error: Optional[str] = None) -> Memory:
        """
        Armazena uma nova memória
        
        Args:
            command: Comando executado
            response: Resposta gerada
            skill_used: Skill utilizada
            context: Contexto adicional
            execution_time: Tempo de execução
            error: Erro se houver
            
        Returns:
            Memory object criado
        """
        # Cria objeto Memory
        memory = Memory(
            id="",
            timestamp=datetime.now(),
            command=command,
            response=response,
            skill_used=skill_used,
            context=context,
            execution_time=execution_time,
            error=error
        )
        
        # Gera embedding se disponível
        if self.embeddings_model:
            memory.embedding = self._generate_embedding(command)
        
        # Extrai tags automaticamente
        memory.tags = self._extract_tags(command)
        
        # Adiciona à memória de curto prazo
        self.short_term_memory.append(memory)
        if len(self.short_term_memory) > 100:
            self.short_term_memory.pop(0)
        
        # Salva no banco
        self._save_memory(memory)
        
        # Atualiza estatísticas
        self._update_statistics(memory)
        
        # Analisa padrões em background
        self.pattern_analyzer.analyze_new_memory(memory)
        
        logger.info(f"Memória armazenada: {memory.id[:8]}... - {skill_used}")
        
        return memory
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Gera embedding para o texto"""
        if not self.embeddings_model:
            return None
        
        try:
            embedding = self.embeddings_model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Erro ao gerar embedding: {e}")
            return None
    
    def _extract_tags(self, command: str) -> List[str]:
        """Extrai tags relevantes do comando"""
        tags = []
        
        # Tags de tempo
        if any(word in command.lower() for word in ['hoje', 'amanhã', 'ontem']):
            tags.append('temporal')
        
        # Tags de ação
        action_words = ['criar', 'deletar', 'abrir', 'fechar', 'enviar', 'listar']
        for action in action_words:
            if action in command.lower():
                tags.append(f'action:{action}')
        
        # Tags de urgência
        if any(word in command.lower() for word in ['urgente', 'importante', 'rápido']):
            tags.append('urgent')
        
        # Tags de tipo de dado
        if any(word in command.lower() for word in ['arquivo', 'pasta', 'documento']):
            tags.append('filesystem')
        if any(word in command.lower() for word in ['email', 'mensagem', 'whatsapp']):
            tags.append('communication')
        
        return tags
    
    def _save_memory(self, memory: Memory):
        """Salva memória no banco de dados"""
        self.cursor.execute("""
            INSERT OR REPLACE INTO memories 
            (id, timestamp, command, response, skill_used, context, 
             embedding, user_satisfaction, execution_time, error, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            memory.id,
            memory.timestamp.timestamp(),
            memory.command,
            memory.response,
            memory.skill_used,
            json.dumps(memory.context),
            pickle.dumps(memory.embedding) if memory.embedding else None,
            memory.user_satisfaction,
            memory.execution_time,
            memory.error,
            json.dumps(memory.tags)
        ))
        self.conn.commit()
    
    def _update_statistics(self, memory: Memory):
        """Atualiza estatísticas baseadas na nova memória"""
        # Atualiza frequência de comandos
        self.command_frequency[memory.skill_used] += 1
        
        # Atualiza performance da skill
        skill_stats = self.skill_performance[memory.skill_used]
        skill_stats['total_uses'] += 1
        
        if not memory.error:
            skill_stats['success_rate'] = (
                (skill_stats['success_rate'] * (skill_stats['total_uses'] - 1) + 1) 
                / skill_stats['total_uses']
            )
        else:
            skill_stats['success_rate'] = (
                (skill_stats['success_rate'] * (skill_stats['total_uses'] - 1)) 
                / skill_stats['total_uses']
            )
        
        # Atualiza tempo médio
        skill_stats['avg_time'] = (
            (skill_stats['avg_time'] * (skill_stats['total_uses'] - 1) + memory.execution_time) 
            / skill_stats['total_uses']
        )
    
    def recall(self, query: str, limit: int = 5, 
               use_semantic: bool = True) -> List[Memory]:
        """
        Busca memórias relevantes
        
        Args:
            query: Query de busca
            limit: Número máximo de resultados
            use_semantic: Usar busca semântica se disponível
            
        Returns:
            Lista de memórias relevantes
        """
        if use_semantic and self.embeddings_model:
            return self._semantic_search(query, limit)
        else:
            return self._keyword_search(query, limit)
    
    def _semantic_search(self, query: str, limit: int) -> List[Memory]:
        """Busca semântica usando embeddings"""
        query_embedding = self._generate_embedding(query)
        if not query_embedding:
            return self._keyword_search(query, limit)
        
        # Busca todas as memórias com embeddings
        self.cursor.execute("""
            SELECT id, timestamp, command, response, skill_used, 
                   context, embedding, tags
            FROM memories 
            WHERE embedding IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT 1000
        """)
        
        results = []
        for row in self.cursor.fetchall():
            if row[6]:  # Se tem embedding
                memory_embedding = pickle.loads(row[6])
                # Calcula similaridade coseno
                similarity = self._cosine_similarity(query_embedding, memory_embedding)
                
                memory = Memory(
                    id=row[0],
                    timestamp=datetime.fromtimestamp(row[1]),
                    command=row[2],
                    response=row[3],
                    skill_used=row[4],
                    context=json.loads(row[5]),
                    tags=json.loads(row[7]) if row[7] else []
                )
                results.append((similarity, memory))
        
        # Ordena por similaridade e retorna top N
        results.sort(key=lambda x: x[0], reverse=True)
        return [memory for _, memory in results[:limit]]
    
    def _keyword_search(self, query: str, limit: int) -> List[Memory]:
        """Busca por palavras-chave"""
        # Busca em comandos e respostas
        self.cursor.execute("""
            SELECT id, timestamp, command, response, skill_used, 
                   context, tags
            FROM memories 
            WHERE command LIKE ? OR response LIKE ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (f'%{query}%', f'%{query}%', limit))
        
        results = []
        for row in self.cursor.fetchall():
            memory = Memory(
                id=row[0],
                timestamp=datetime.fromtimestamp(row[1]),
                command=row[2],
                response=row[3],
                skill_used=row[4],
                context=json.loads(row[5]),
                tags=json.loads(row[6]) if row[6] else []
            )
            results.append(memory)
        
        return results
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calcula similaridade coseno entre dois vetores"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def get_user_profile(self) -> Dict[str, Any]:
        """Retorna perfil completo do usuário baseado em padrões"""
        profile = {
            'most_used_skills': self.command_frequency.most_common(5),
            'skill_performance': dict(self.skill_performance),
            'active_patterns': {},
            'usage_stats': {},
            'preferences': {},
            'predictions': []
        }
        
        # Padrões ativos
        for pattern_id, pattern in self.working_patterns.items():
            profile['active_patterns'][pattern_id] = {
                'type': pattern.pattern_type,
                'confidence': pattern.confidence,
                'predictions': pattern.predictions[:3]
            }
        
        # Estatísticas de uso
        self.cursor.execute("""
            SELECT 
                COUNT(*) as total_commands,
                COUNT(DISTINCT DATE(timestamp, 'unixepoch')) as days_active,
                AVG(execution_time) as avg_execution_time
            FROM memories
        """)
        
        stats = self.cursor.fetchone()
        if stats:
            profile['usage_stats'] = {
                'total_commands': stats[0],
                'days_active': stats[1],
                'avg_execution_time': stats[2] or 0
            }
        
        # Preferências detectadas
        profile['preferences'] = self._detect_preferences()
        
        # Próximas ações previstas
        profile['predictions'] = self.predict_next_actions()
        
        return profile
    
    def _detect_preferences(self) -> Dict[str, Any]:
        """Detecta preferências do usuário"""
        preferences = {}
        
        # Horário preferido de uso
        self.cursor.execute("""
            SELECT strftime('%H', timestamp, 'unixepoch') as hour, COUNT(*) as count
            FROM memories
            GROUP BY hour
            ORDER BY count DESC
            LIMIT 3
        """)
        
        peak_hours = self.cursor.fetchall()
        if peak_hours:
            preferences['peak_usage_hours'] = [int(h[0]) for h in peak_hours]
        
        # Dia da semana preferido
        self.cursor.execute("""
            SELECT strftime('%w', timestamp, 'unixepoch') as weekday, COUNT(*) as count
            FROM memories
            GROUP BY weekday
            ORDER BY count DESC
            LIMIT 1
        """)
        
        peak_day = self.cursor.fetchone()
        if peak_day:
            days = ['Domingo', 'Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado']
            preferences['most_active_day'] = days[int(peak_day[0])]
        
        return preferences
    
    def predict_next_actions(self, context: Optional[Dict] = None) -> List[Tuple[str, float]]:
        """
        Prevê próximas ações baseado em padrões
        
        Returns:
            Lista de (ação, confiança)
        """
        predictions = []
        current_time = datetime.now()
        current_hour = current_time.hour
        current_weekday = current_time.weekday()
        
        # Busca padrões temporais
        self.cursor.execute("""
            SELECT command, COUNT(*) as frequency
            FROM memories
            WHERE strftime('%H', timestamp, 'unixepoch') = ?
            GROUP BY command
            ORDER BY frequency DESC
            LIMIT 5
        """, (str(current_hour),))
        
        for row in self.cursor.fetchall():
            confidence = min(row[1] / 10, 1.0)  # Normaliza confiança
            predictions.append((row[0], confidence))
        
        # Busca sequências comuns
        if self.short_term_memory:
            last_command = self.short_term_memory[-1].command
            
            self.cursor.execute("""
                SELECT m2.command, COUNT(*) as frequency
                FROM memories m1
                JOIN memories m2 ON m2.timestamp > m1.timestamp
                WHERE m1.command = ?
                AND m2.timestamp - m1.timestamp < 3600  -- Dentro de 1 hora
                GROUP BY m2.command
                ORDER BY frequency DESC
                LIMIT 3
            """, (last_command,))
            
            for row in self.cursor.fetchall():
                confidence = min(row[1] / 5, 0.8)
                predictions.append((row[0], confidence))
        
        # Remove duplicatas e ordena por confiança
        seen = set()
        unique_predictions = []
        for pred in sorted(predictions, key=lambda x: x[1], reverse=True):
            if pred[0] not in seen:
                seen.add(pred[0])
                unique_predictions.append(pred)
        
        return unique_predictions[:5]
    
    def suggest_automation(self) -> List[Dict[str, Any]]:
        """Sugere automações baseadas em padrões repetitivos"""
        suggestions = []
        
        # Busca comandos mais frequentes
        self.cursor.execute("""
            SELECT command, skill_used, COUNT(*) as frequency
            FROM memories
            WHERE error IS NULL
            GROUP BY command, skill_used
            HAVING frequency > 5
            ORDER BY frequency DESC
            LIMIT 10
        """)
        
        for row in self.cursor.fetchall():
            command, skill, frequency = row
            
            # Verifica se há padrão temporal
            self.cursor.execute("""
                SELECT 
                    strftime('%H', timestamp, 'unixepoch') as hour,
                    COUNT(*) as count
                FROM memories
                WHERE command = ?
                GROUP BY hour
                HAVING count > 2
                ORDER BY count DESC
                LIMIT 1
            """, (command,))
            
            time_pattern = self.cursor.fetchone()
            
            suggestion = {
                'command': command,
                'skill': skill,
                'frequency': frequency,
                'automation_type': 'scheduled' if time_pattern else 'trigger',
                'confidence': min(frequency / 20, 1.0)
            }
            
            if time_pattern:
                suggestion['suggested_time'] = f"{time_pattern[0]}:00"
                suggestion['description'] = f"Executar '{command}' automaticamente às {time_pattern[0]}:00"
            else:
                suggestion['description'] = f"Criar atalho para '{command}' (usado {frequency} vezes)"
            
            suggestions.append(suggestion)
        
        return suggestions
    
    def _load_historical_data(self):
        """Carrega dados históricos na inicialização"""
        # Carrega últimas memórias
        self.cursor.execute("""
            SELECT id, timestamp, command, response, skill_used, 
                   context, tags, execution_time, error
            FROM memories
            ORDER BY timestamp DESC
            LIMIT 100
        """)
        
        for row in self.cursor.fetchall():
            memory = Memory(
                id=row[0],
                timestamp=datetime.fromtimestamp(row[1]),
                command=row[2],
                response=row[3],
                skill_used=row[4],
                context=json.loads(row[5]),
                tags=json.loads(row[6]) if row[6] else [],
                execution_time=row[7] or 0,
                error=row[8]
            )
            self.short_term_memory.append(memory)
        
        # Carrega estatísticas de skills
        self.cursor.execute("""
            SELECT 
                skill_used,
                COUNT(*) as total,
                COUNT(CASE WHEN error IS NULL THEN 1 END) as success,
                AVG(execution_time) as avg_time
            FROM memories
            GROUP BY skill_used
        """)
        
        for row in self.cursor.fetchall():
            skill = row[0]
            self.skill_performance[skill] = {
                'total_uses': row[1],
                'success_rate': row[2] / row[1] if row[1] > 0 else 0,
                'avg_time': row[3] or 0
            }
        
        logger.info(f"Carregadas {len(self.short_term_memory)} memórias recentes")


class PatternAnalyzer:
    """Analisador de padrões comportamentais"""
    
    def __init__(self, memory_system: PrometheusMemorySystem):
        self.memory_system = memory_system
        self.patterns_queue = []
        
    def analyze_new_memory(self, memory: Memory):
        """Analisa nova memória em busca de padrões"""
        # Adiciona à fila
        self.patterns_queue.append(memory)
        
        # Analisa a cada 10 memórias
        if len(self.patterns_queue) >= 10:
            self._process_patterns()
            self.patterns_queue.clear()
    
    def _process_patterns(self):
        """Processa padrões na fila"""
        # Detecta padrões temporais
        self._detect_temporal_patterns()
        
        # Detecta sequências de comandos
        self._detect_command_sequences()
        
        # Detecta preferências
        self._detect_user_preferences()
    
    def _detect_temporal_patterns(self):
        """Detecta padrões baseados em tempo"""
        current_hour = datetime.now().hour
        
        # Busca comandos frequentes neste horário
        self.memory_system.cursor.execute("""
            SELECT command, COUNT(*) as frequency
            FROM memories
            WHERE strftime('%H', timestamp, 'unixepoch') = ?
            GROUP BY command
            HAVING frequency > 3
        """, (str(current_hour),))
        
        for row in self.memory_system.cursor.fetchall():
            pattern = UserPattern(
                pattern_type='hourly',
                pattern_data={'hour': current_hour, 'command': row[0]},
                frequency=row[1],
                confidence=min(row[1] / 10, 1.0),
                last_seen=datetime.now(),
                predictions=[row[0]]
            )
            
            pattern_id = f"hourly_{current_hour}_{row[0][:20]}"
            self.memory_system.working_patterns[pattern_id] = pattern
    
    def _detect_command_sequences(self):
        """Detecta sequências comuns de comandos"""
        if len(self.memory_system.short_term_memory) < 2:
            return
        
        # Analisa pares de comandos
        for i in range(len(self.memory_system.short_term_memory) - 1):
            cmd1 = self.memory_system.short_term_memory[i].command
            cmd2 = self.memory_system.short_term_memory[i + 1].command
            
            # Verifica se essa sequência é comum
            self.memory_system.cursor.execute("""
                SELECT COUNT(*) as frequency
                FROM memories m1
                JOIN memories m2 ON m2.timestamp > m1.timestamp
                WHERE m1.command = ? AND m2.command = ?
                AND m2.timestamp - m1.timestamp < 3600
            """, (cmd1, cmd2))
            
            result = self.memory_system.cursor.fetchone()
            if result and result[0] > 3:
                pattern = UserPattern(
                    pattern_type='sequence',
                    pattern_data={'sequence': [cmd1, cmd2]},
                    frequency=result[0],
                    confidence=min(result[0] / 5, 1.0),
                    last_seen=datetime.now(),
                    predictions=[cmd2]
                )
                
                pattern_id = f"seq_{hash(cmd1 + cmd2)}"
                self.memory_system.working_patterns[pattern_id] = pattern
    
    def _detect_user_preferences(self):
        """Detecta preferências do usuário"""
        # Analisa preferências de horário
        self.memory_system.cursor.execute("""
            SELECT 
                strftime('%H', timestamp, 'unixepoch') as hour,
                skill_used,
                COUNT(*) as count
            FROM memories
            WHERE timestamp > ?
            GROUP BY hour, skill_used
            HAVING count > 2
            ORDER BY count DESC
        """, ((datetime.now() - timedelta(days=7)).timestamp(),))
        
        for row in self.memory_system.cursor.fetchall():
            hour, skill, count = row
            pattern = UserPattern(
                pattern_type='preference',
                pattern_data={'hour': int(hour), 'preferred_skill': skill},
                frequency=count,
                confidence=min(count / 10, 1.0),
                last_seen=datetime.now(),
                predictions=[f"usar {skill}"]
            )
            
            pattern_id = f"pref_{hour}_{skill}"
            self.memory_system.working_patterns[pattern_id] = pattern


# Interface para integração com Prometheus
class PrometheusMemoryInterface:
    """Interface simplificada para integração com o Prometheus principal"""
    
    def __init__(self, db_path: str = "C:\\Users\\lucas\\Prometheus\\memory\\prometheus_memory.db"):
        """Inicializa interface de memória"""
        # Cria diretório se não existir
        memory_dir = os.path.dirname(db_path)
        if memory_dir and not os.path.exists(memory_dir):
            os.makedirs(memory_dir)
        
        self.memory_system = PrometheusMemorySystem(db_path)
        logger.info("Sistema de memória inicializado")
    
    def process_command(self, command: str, skill: str, 
                        context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Processa comando com contexto de memória
        
        Returns:
            Dict com sugestões e contexto relevante
        """
        context = context or {}
        
        # Busca memórias relevantes
        relevant_memories = self.memory_system.recall(command, limit=3)
        
        # Obtém previsões
        predictions = self.memory_system.predict_next_actions(context)
        
        # Monta resposta
        response = {
            'relevant_context': [
                {
                    'command': mem.command,
                    'response': mem.response,
                    'when': mem.timestamp.isoformat()
                }
                for mem in relevant_memories
            ],
            'predictions': [
                {'action': pred[0], 'confidence': pred[1]}
                for pred in predictions
            ],
            'user_profile': self.memory_system.get_user_profile(),
            'suggestions': []
        }
        
        # Adiciona sugestões baseadas em contexto
        current_hour = datetime.now().hour
        if 8 <= current_hour <= 10:
            response['suggestions'].append("Verificar emails (padrão matinal detectado)")
        elif 14 <= current_hour <= 15:
            response['suggestions'].append("Revisar tarefas da tarde (padrão pós-almoço)")
        
        return response
    
    def save_interaction(self, command: str, response: str, 
                         skill_used: str, execution_time: float,
                         success: bool = True):
        """Salva interação na memória"""
        error = None if success else "Comando falhou"
        
        memory = self.memory_system.remember(
            command=command,
            response=response,
            skill_used=skill_used,
            context={'timestamp': datetime.now().isoformat()},
            execution_time=execution_time,
            error=error
        )
        
        logger.info(f"Interação salva: {memory.id[:8]}...")
        
        # Verifica se deve sugerir automação
        suggestions = self.memory_system.suggest_automation()
        if suggestions:
            logger.info(f"💡 Sugestões de automação disponíveis: {len(suggestions)}")
            for sug in suggestions[:3]:
                logger.info(f"  - {sug['description']}")
        
        return memory.id
    
    def get_insights(self) -> Dict[str, Any]:
        """Retorna insights sobre o uso"""
        profile = self.memory_system.get_user_profile()
        
        insights = {
            'total_interactions': profile['usage_stats'].get('total_commands', 0),
            'days_active': profile['usage_stats'].get('days_active', 0),
            'favorite_skills': profile['most_used_skills'][:3],
            'peak_hours': profile['preferences'].get('peak_usage_hours', []),
            'automations_available': len(self.memory_system.suggest_automation()),
            'patterns_detected': len(self.memory_system.working_patterns),
            'predictions_available': len(profile['predictions'])
        }
        
        return insights


if __name__ == "__main__":
    # Teste do sistema
    print("🧠 Testando Sistema de Memória Prometheus...")
    
    # Inicializa
    memory_interface = PrometheusMemoryInterface("test_memory.db")
    
    # Simula algumas interações
    test_commands = [
        ("listar arquivos C:\\Users\\lucas\\Documents", "system_control", 0.5),
        ("abrir pasta Downloads", "system_control", 0.3),
        ("status n8n", "n8n_client", 1.2),
        ("criar lead teste@email.com", "rdstation_client", 2.1),
        ("listar arquivos C:\\Users\\lucas\\Documents", "system_control", 0.4),
        ("whatsapp 5511999999999 'Teste'", "whatsapp_api", 3.5),
    ]
    
    print("\n📝 Salvando interações de teste...")
    for cmd, skill, exec_time in test_commands:
        memory_interface.save_interaction(
            command=cmd,
            response=f"Executado: {cmd}",
            skill_used=skill,
            execution_time=exec_time,
            success=True
        )
        print(f"  ✓ {cmd[:50]}...")
    
    # Testa recuperação
    print("\n🔍 Testando busca de memórias...")
    context = memory_interface.process_command(
        "listar arquivos", 
        "system_control"
    )
    
    print(f"\n📊 Contexto relevante encontrado:")
    for ctx in context['relevant_context']:
        print(f"  - {ctx['command'][:50]}... ({ctx['when']})")
    
    print(f"\n🔮 Previsões:")
    for pred in context['predictions']:
        print(f"  - {pred['action'][:50]}... (confiança: {pred['confidence']:.2f})")
    
    # Mostra insights
    insights = memory_interface.get_insights()
    print(f"\n💡 Insights:")
    print(f"  - Total de interações: {insights['total_interactions']}")
    print(f"  - Dias ativos: {insights['days_active']}")
    print(f"  - Skills favoritas: {insights['favorite_skills']}")
    print(f"  - Horários de pico: {insights['peak_hours']}")
    print(f"  - Automações disponíveis: {insights['automations_available']}")
    print(f"  - Padrões detectados: {insights['patterns_detected']}")
    
    print("\n✅ Sistema de Memória testado com sucesso!")
