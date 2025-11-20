#!/usr/bin/env python
"""
🧬 PROMETHEUS SELF-IMPROVEMENT ENGINE
Sistema de auto-evolução que torna o Prometheus cada vez mais inteligente
Aprende com cada execução, erro e sucesso
"""

import json
import sqlite3
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib
import asyncio

# Machine Learning
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import KMeans
    ML_READY = True
except ImportError:
    ML_READY = False
    print("[!] Instale: pip install scikit-learn numpy")


@dataclass
class Experience:
    """Experiência individual do Prometheus"""
    id: str
    timestamp: datetime
    task: str
    approach: str
    steps_taken: List[Dict]
    outcome: str  # success, partial, failure
    time_taken: float
    errors: List[str]
    learnings: Dict
    confidence: float
    

@dataclass 
class Pattern:
    """Padrão aprendido de múltiplas experiências"""
    pattern_id: str
    pattern_type: str  # task_pattern, error_pattern, success_pattern
    description: str
    occurrences: int
    success_rate: float
    avg_time: float
    best_approach: Dict
    recommendations: List[str]


class PrometheusMemory:
    """
    [BRAIN] MEMÓRIA DE LONGO PRAZO
    Armazena todas as experiências e aprendizados
    """
    
    def __init__(self, db_path: str = "prometheus_memory.db"):
        self.db_path = db_path
        self.conn = self._init_database()
        self.vectorizer = TfidfVectorizer() if ML_READY else None
        self.task_embeddings = {}
        
    def _init_database(self) -> sqlite3.Connection:
        """Inicializa banco de dados de memória"""
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Tabela de experiências
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS experiences (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                task TEXT,
                approach TEXT,
                steps_taken TEXT,
                outcome TEXT,
                time_taken REAL,
                errors TEXT,
                learnings TEXT,
                confidence REAL
            )
        ''')
        
        # Tabela de padrões
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patterns (
                pattern_id TEXT PRIMARY KEY,
                pattern_type TEXT,
                description TEXT,
                occurrences INTEGER,
                success_rate REAL,
                avg_time REAL,
                best_approach TEXT,
                recommendations TEXT,
                last_updated TEXT
            )
        ''')
        
        # Tabela de habilidades
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skills (
                skill_id TEXT PRIMARY KEY,
                skill_name TEXT,
                proficiency REAL,
                usage_count INTEGER,
                success_count INTEGER,
                last_used TEXT,
                metadata TEXT
            )
        ''')
        
        # Índices para busca rápida
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_task ON experiences(task)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_outcome ON experiences(outcome)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_pattern_type ON patterns(pattern_type)')
        
        conn.commit()
        print(f"[BOOK] Memória inicializada: {self.db_path}")
        return conn
    
    def remember_experience(self, experience: Experience):
        """Armazena uma experiência na memória"""
        
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO experiences 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            experience.id,
            experience.timestamp.isoformat(),
            experience.task,
            experience.approach,
            json.dumps(experience.steps_taken),
            experience.outcome,
            experience.time_taken,
            json.dumps(experience.errors),
            json.dumps(experience.learnings),
            experience.confidence
        ))
        
        self.conn.commit()
        
        # Atualizar embeddings se ML disponível
        if ML_READY:
            self._update_embeddings(experience.task)
    
    def recall_similar_experiences(self, task: str, limit: int = 5) -> List[Experience]:
        """Busca experiências similares à tarefa atual"""
        
        if ML_READY and self.task_embeddings:
            # Busca por similaridade usando embeddings
            similar_tasks = self._find_similar_tasks(task, limit)
            
            cursor = self.conn.cursor()
            placeholders = ','.join('?' * len(similar_tasks))
            
            cursor.execute(f'''
                SELECT * FROM experiences 
                WHERE task IN ({placeholders})
                ORDER BY confidence DESC, outcome DESC
                LIMIT ?
            ''', (*similar_tasks, limit))
        else:
            # Busca simples por palavras-chave
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM experiences 
                WHERE task LIKE ?
                ORDER BY confidence DESC, outcome DESC
                LIMIT ?
            ''', (f'%{task}%', limit))
        
        rows = cursor.fetchall()
        experiences = []
        
        for row in rows:
            exp = Experience(
                id=row[0],
                timestamp=datetime.fromisoformat(row[1]),
                task=row[2],
                approach=row[3],
                steps_taken=json.loads(row[4]),
                outcome=row[5],
                time_taken=row[6],
                errors=json.loads(row[7]),
                learnings=json.loads(row[8]),
                confidence=row[9]
            )
            experiences.append(exp)
        
        return experiences
    
    def _update_embeddings(self, task: str):
        """Atualiza embeddings de tarefas para busca por similaridade"""
        
        if not ML_READY:
            return
        
        # Coletar todas as tarefas únicas
        cursor = self.conn.cursor()
        cursor.execute('SELECT DISTINCT task FROM experiences')
        tasks = [row[0] for row in cursor.fetchall()]
        
        if len(tasks) > 1:
            # Criar embeddings
            self.task_embeddings = self.vectorizer.fit_transform(tasks)
    
    def _find_similar_tasks(self, task: str, limit: int) -> List[str]:
        """Encontra tarefas similares usando embeddings"""
        
        if not ML_READY or self.task_embeddings is None:
            return [task]
        
        # Embedding da tarefa atual
        task_embedding = self.vectorizer.transform([task])
        
        # Calcular similaridades
        similarities = cosine_similarity(task_embedding, self.task_embeddings)[0]
        
        # Índices das tarefas mais similares
        similar_indices = similarities.argsort()[-limit:][::-1]
        
        # Recuperar tarefas
        cursor = self.conn.cursor()
        cursor.execute('SELECT DISTINCT task FROM experiences')
        all_tasks = [row[0] for row in cursor.fetchall()]
        
        return [all_tasks[i] for i in similar_indices if i < len(all_tasks)]
    
    def identify_patterns(self) -> List[Pattern]:
        """Identifica padrões nas experiências"""
        
        patterns = []
        
        # Padrões de sucesso
        success_patterns = self._analyze_success_patterns()
        patterns.extend(success_patterns)
        
        # Padrões de erro
        error_patterns = self._analyze_error_patterns()
        patterns.extend(error_patterns)
        
        # Padrões de tempo
        time_patterns = self._analyze_time_patterns()
        patterns.extend(time_patterns)
        
        # Salvar padrões no banco
        self._save_patterns(patterns)
        
        return patterns
    
    def _analyze_success_patterns(self) -> List[Pattern]:
        """Analisa padrões de sucesso"""
        
        cursor = self.conn.cursor()
        
        # Agrupar por approach e calcular taxa de sucesso
        cursor.execute('''
            SELECT approach, 
                   COUNT(*) as total,
                   SUM(CASE WHEN outcome = 'success' THEN 1 ELSE 0 END) as successes,
                   AVG(time_taken) as avg_time
            FROM experiences
            GROUP BY approach
            HAVING total > 3
        ''')
        
        patterns = []
        
        for row in cursor.fetchall():
            approach = row[0]
            total = row[1]
            successes = row[2]
            avg_time = row[3]
            success_rate = successes / total
            
            if success_rate > 0.7:  # Padrão de sucesso
                pattern = Pattern(
                    pattern_id=f"success_{hashlib.md5(approach.encode()).hexdigest()[:8]}",
                    pattern_type="success_pattern",
                    description=f"Abordagem bem-sucedida: {approach}",
                    occurrences=total,
                    success_rate=success_rate,
                    avg_time=avg_time,
                    best_approach={"approach": approach},
                    recommendations=[
                        f"Use '{approach}' para tarefas similares",
                        f"Taxa de sucesso: {success_rate*100:.1f}%",
                        f"Tempo médio: {avg_time:.2f}s"
                    ]
                )
                patterns.append(pattern)
        
        return patterns
    
    def _analyze_error_patterns(self) -> List[Pattern]:
        """Analisa padrões de erro recorrentes"""
        
        cursor = self.conn.cursor()
        
        # Coletar todos os erros
        cursor.execute('SELECT errors FROM experiences WHERE errors != "[]"')
        
        error_counts = defaultdict(int)
        
        for row in cursor.fetchall():
            errors = json.loads(row[0])
            for error in errors:
                error_counts[error] += 1
        
        patterns = []
        
        # Criar padrões para erros frequentes
        for error, count in error_counts.items():
            if count > 2:  # Erro recorrente
                pattern = Pattern(
                    pattern_id=f"error_{hashlib.md5(error.encode()).hexdigest()[:8]}",
                    pattern_type="error_pattern",
                    description=f"Erro recorrente: {error[:100]}",
                    occurrences=count,
                    success_rate=0.0,
                    avg_time=0.0,
                    best_approach={
                        "avoid": error,
                        "mitigation": self._suggest_error_mitigation(error)
                    },
                    recommendations=[
                        f"Evite: {error[:50]}",
                        f"Ocorrências: {count}",
                        "Implementar tratamento específico"
                    ]
                )
                patterns.append(pattern)
        
        return patterns
    
    def _analyze_time_patterns(self) -> List[Pattern]:
        """Analisa padrões de tempo de execução"""
        
        cursor = self.conn.cursor()
        
        # Tarefas mais rápidas vs mais lentas
        cursor.execute('''
            SELECT task, AVG(time_taken) as avg_time, COUNT(*) as count
            FROM experiences
            WHERE outcome = 'success'
            GROUP BY task
            HAVING count > 2
            ORDER BY avg_time
        ''')
        
        patterns = []
        rows = cursor.fetchall()
        
        if rows:
            # Padrão para tarefas rápidas
            fastest = rows[:3]
            for task, avg_time, count in fastest:
                pattern = Pattern(
                    pattern_id=f"fast_{hashlib.md5(task.encode()).hexdigest()[:8]}",
                    pattern_type="time_pattern",
                    description=f"Tarefa rápida: {task[:50]}",
                    occurrences=count,
                    success_rate=1.0,
                    avg_time=avg_time,
                    best_approach={"task": task, "optimization": "already_optimized"},
                    recommendations=[
                        f"Tempo ótimo: {avg_time:.2f}s",
                        "Use como referência para tarefas similares"
                    ]
                )
                patterns.append(pattern)
        
        return patterns
    
    def _suggest_error_mitigation(self, error: str) -> str:
        """Sugere mitigação para erro"""
        
        error_lower = error.lower()
        
        if "timeout" in error_lower:
            return "Aumentar timeout ou implementar retry com backoff"
        elif "not found" in error_lower:
            return "Verificar existência antes de acessar"
        elif "permission" in error_lower:
            return "Verificar permissões ou executar como admin"
        elif "connection" in error_lower:
            return "Implementar retry com verificação de conectividade"
        else:
            return "Adicionar tratamento de exceção específico"
    
    def _save_patterns(self, patterns: List[Pattern]):
        """Salva padrões identificados no banco"""
        
        cursor = self.conn.cursor()
        
        for pattern in patterns:
            cursor.execute('''
                INSERT OR REPLACE INTO patterns 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                pattern.pattern_id,
                pattern.pattern_type,
                pattern.description,
                pattern.occurrences,
                pattern.success_rate,
                pattern.avg_time,
                json.dumps(pattern.best_approach),
                json.dumps(pattern.recommendations),
                datetime.now().isoformat()
            ))
        
        self.conn.commit()
        print(f"[SAVE] {len(patterns)} padrões salvos")


class PrometheusLearningEngine:
    """
    [BOOK] ENGINE DE APRENDIZADO
    Aprende continuamente e melhora estratégias
    """
    
    def __init__(self, memory: PrometheusMemory):
        self.memory = memory
        self.current_task = None
        self.learning_rate = 0.1
        self.improvement_suggestions = []
        
    async def learn_from_execution(self, task: str, execution_data: Dict) -> Dict:
        """Aprende com uma execução"""
        
        # Criar experiência
        experience = self._create_experience(task, execution_data)
        
        # Armazenar na memória
        self.memory.remember_experience(experience)
        
        # Analisar e extrair aprendizados
        learnings = await self._analyze_execution(experience)
        
        # Atualizar habilidades
        self._update_skills(experience, learnings)
        
        # Gerar sugestões de melhoria
        suggestions = self._generate_improvements(experience, learnings)
        
        return {
            'experience_id': experience.id,
            'learnings': learnings,
            'suggestions': suggestions,
            'patterns_found': len(learnings.get('patterns', []))
        }
    
    def _create_experience(self, task: str, execution_data: Dict) -> Experience:
        """Cria experiência a partir dos dados de execução"""
        
        exp_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(task.encode()).hexdigest()[:8]}"
        
        return Experience(
            id=exp_id,
            timestamp=datetime.now(),
            task=task,
            approach=execution_data.get('strategy_used', 'unknown'),
            steps_taken=execution_data.get('steps', []),
            outcome='success' if execution_data.get('success') else 'failure',
            time_taken=execution_data.get('time_taken', 0),
            errors=execution_data.get('errors', []),
            learnings=execution_data.get('learnings', {}),
            confidence=execution_data.get('confidence', 0.5)
        )
    
    async def _analyze_execution(self, experience: Experience) -> Dict:
        """Analisa execução profundamente"""
        
        learnings = {
            'patterns': [],
            'optimizations': [],
            'warnings': [],
            'insights': []
        }
        
        # Buscar experiências similares
        similar = self.memory.recall_similar_experiences(experience.task, limit=10)
        
        if similar:
            # Comparar com experiências anteriores
            
            # Tempo relativo
            avg_time = sum(e.time_taken for e in similar) / len(similar)
            if experience.time_taken < avg_time * 0.8:
                learnings['insights'].append(f"Execução 20% mais rápida que a média!")
            elif experience.time_taken > avg_time * 1.5:
                learnings['warnings'].append(f"Execução 50% mais lenta que o esperado")
            
            # Taxa de sucesso
            success_rate = sum(1 for e in similar if e.outcome == 'success') / len(similar)
            if experience.outcome == 'success' and success_rate < 0.5:
                learnings['insights'].append(f"Sucesso em tarefa difícil (taxa histórica: {success_rate*100:.1f}%)")
            
            # Abordagens bem-sucedidas
            successful_approaches = [e.approach for e in similar if e.outcome == 'success']
            if successful_approaches:
                most_common = max(set(successful_approaches), key=successful_approaches.count)
                if experience.approach != most_common:
                    learnings['optimizations'].append(f"Considere usar '{most_common}' (mais bem-sucedida)")
        
        # Identificar padrões
        patterns = self.memory.identify_patterns()
        relevant_patterns = [p for p in patterns if self._is_pattern_relevant(p, experience)]
        learnings['patterns'] = [p.description for p in relevant_patterns]
        
        return learnings
    
    def _is_pattern_relevant(self, pattern: Pattern, experience: Experience) -> bool:
        """Verifica se um padrão é relevante para a experiência"""
        
        # Simplificado - verificar se tem palavras em comum
        pattern_words = set(pattern.description.lower().split())
        experience_words = set(experience.task.lower().split())
        
        common_words = pattern_words.intersection(experience_words)
        
        return len(common_words) > 0
    
    def _update_skills(self, experience: Experience, learnings: Dict):
        """Atualiza habilidades baseado na experiência"""
        
        cursor = self.memory.conn.cursor()
        
        # Extrair skill da tarefa (simplificado)
        skill_name = self._extract_skill(experience.task)
        skill_id = hashlib.md5(skill_name.encode()).hexdigest()[:8]
        
        # Buscar skill existente
        cursor.execute('SELECT * FROM skills WHERE skill_id = ?', (skill_id,))
        row = cursor.fetchone()
        
        if row:
            # Atualizar skill existente
            usage_count = row[3] + 1
            success_count = row[4] + (1 if experience.outcome == 'success' else 0)
            proficiency = success_count / usage_count
            
            cursor.execute('''
                UPDATE skills 
                SET proficiency = ?, usage_count = ?, success_count = ?, last_used = ?
                WHERE skill_id = ?
            ''', (proficiency, usage_count, success_count, datetime.now().isoformat(), skill_id))
        else:
            # Criar nova skill
            cursor.execute('''
                INSERT INTO skills VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                skill_id,
                skill_name,
                1.0 if experience.outcome == 'success' else 0.0,
                1,
                1 if experience.outcome == 'success' else 0,
                datetime.now().isoformat(),
                json.dumps({'created_from': experience.task})
            ))
        
        self.memory.conn.commit()
    
    def _extract_skill(self, task: str) -> str:
        """Extrai nome da habilidade da tarefa"""
        
        # Simplificado - pegar primeira palavra significativa
        words = task.lower().split()
        
        action_words = ['criar', 'analisar', 'buscar', 'executar', 'debugar', 
                       'escrever', 'configurar', 'instalar', 'automatizar']
        
        for word in words:
            if word in action_words:
                return word
        
        return 'general'
    
    def _generate_improvements(self, experience: Experience, learnings: Dict) -> List[str]:
        """Gera sugestões de melhoria"""
        
        suggestions = []
        
        # Baseado em erros
        if experience.errors:
            suggestions.append(f"Implementar tratamento para: {experience.errors[0][:50]}")
        
        # Baseado em tempo
        if experience.time_taken > 30:
            suggestions.append("Considerar paralelização de tarefas independentes")
        
        # Baseado em confiança
        if experience.confidence < 0.7:
            suggestions.append("Aumentar validações intermediárias para maior confiança")
        
        # Baseado em padrões
        if learnings.get('patterns'):
            suggestions.append(f"Aplicar padrão: {learnings['patterns'][0]}")
        
        # Baseado em otimizações identificadas
        suggestions.extend(learnings.get('optimizations', []))
        
        return suggestions
    
    async def suggest_best_approach(self, task: str) -> Dict:
        """Sugere melhor abordagem baseado no aprendizado"""
        
        # Buscar experiências similares bem-sucedidas
        similar = self.memory.recall_similar_experiences(task, limit=20)
        successful = [e for e in similar if e.outcome == 'success']
        
        if not successful:
            return {
                'approach': 'exploratory',
                'confidence': 0.3,
                'reason': 'Tarefa nova, sem experiências anteriores',
                'suggestions': ['Começar com abordagem cautelosa', 'Coletar máximo de informações']
            }
        
        # Encontrar melhor abordagem
        approach_scores = defaultdict(lambda: {'count': 0, 'total_confidence': 0, 'avg_time': 0})
        
        for exp in successful:
            approach_scores[exp.approach]['count'] += 1
            approach_scores[exp.approach]['total_confidence'] += exp.confidence
            approach_scores[exp.approach]['avg_time'] += exp.time_taken
        
        # Calcular scores
        best_approach = None
        best_score = 0
        
        for approach, data in approach_scores.items():
            avg_confidence = data['total_confidence'] / data['count']
            avg_time = data['avg_time'] / data['count']
            
            # Score: confiança alta, tempo baixo, muitas ocorrências
            score = (avg_confidence * data['count']) / (avg_time + 1)
            
            if score > best_score:
                best_score = score
                best_approach = approach
                best_data = data
        
        return {
            'approach': best_approach,
            'confidence': best_data['total_confidence'] / best_data['count'],
            'expected_time': best_data['avg_time'] / best_data['count'],
            'based_on': best_data['count'],
            'reason': f"Melhor histórico: {best_data['count']} sucessos",
            'suggestions': [
                f"Tempo esperado: {best_data['avg_time']/best_data['count']:.2f}s",
                f"Taxa de confiança: {(best_data['total_confidence']/best_data['count'])*100:.1f}%"
            ]
        }
    
    def get_skill_report(self) -> Dict:
        """Gera relatório de habilidades"""
        
        cursor = self.memory.conn.cursor()
        cursor.execute('''
            SELECT skill_name, proficiency, usage_count, success_count
            FROM skills
            ORDER BY proficiency DESC, usage_count DESC
        ''')
        
        skills = []
        for row in cursor.fetchall():
            skills.append({
                'name': row[0],
                'proficiency': row[1],
                'usage_count': row[2],
                'success_count': row[3],
                'mastery_level': self._calculate_mastery(row[1], row[2])
            })
        
        return {
            'total_skills': len(skills),
            'top_skills': skills[:5],
            'skills_to_improve': [s for s in skills if s['proficiency'] < 0.7],
            'mastered_skills': [s for s in skills if s['mastery_level'] == 'master']
        }
    
    def _calculate_mastery(self, proficiency: float, usage_count: int) -> str:
        """Calcula nível de maestria"""
        
        if usage_count < 5:
            return 'novice'
        elif proficiency < 0.5:
            return 'learning'
        elif proficiency < 0.7:
            return 'intermediate'
        elif proficiency < 0.9:
            return 'advanced'
        else:
            return 'master'


async def demonstration():
    """Demonstração do sistema de aprendizado"""
    
    print("\n" + "="*60)
    print("   🧬 PROMETHEUS SELF-IMPROVEMENT ENGINE")
    print("="*60 + "\n")
    
    # Criar sistema
    memory = PrometheusMemory("prometheus_demo_memory.db")
    learning_engine = PrometheusLearningEngine(memory)
    
    # Simular algumas execuções
    test_executions = [
        {
            'task': 'Criar relatório de vendas mensal',
            'success': True,
            'strategy_used': 'data_analysis',
            'time_taken': 45.2,
            'confidence': 0.85,
            'errors': []
        },
        {
            'task': 'Buscar informações sobre concorrentes',
            'success': True,
            'strategy_used': 'web_scraping',
            'time_taken': 120.5,
            'confidence': 0.78,
            'errors': []
        },
        {
            'task': 'Criar apresentação para reunião',
            'success': False,
            'strategy_used': 'template_based',
            'time_taken': 180.0,
            'confidence': 0.45,
            'errors': ['Template not found', 'Timeout error']
        },
        {
            'task': 'Criar relatório de análise de mercado',
            'success': True,
            'strategy_used': 'data_analysis',
            'time_taken': 38.7,
            'confidence': 0.92,
            'errors': []
        },
        {
            'task': 'Buscar dados de vendas no sistema',
            'success': True,
            'strategy_used': 'database_query',
            'time_taken': 15.3,
            'confidence': 0.95,
            'errors': []
        }
    ]
    
    print("[STATS] Simulando execuções e aprendizado...\n")
    
    for i, execution in enumerate(test_executions, 1):
        print(f"Execução {i}: {execution['task']}")
        
        # Aprender com a execução
        result = await learning_engine.learn_from_execution(
            execution['task'],
            execution
        )
        
        print(f"  ✓ Aprendizado registrado")
        print(f"  [BOOK] Insights: {len(result['learnings'].get('insights', []))}")
        print(f"  [IDEA] Sugestões: {len(result['suggestions'])}")
        
        if result['suggestions']:
            print(f"     → {result['suggestions'][0]}")
    
    print("\n" + "-"*60)
    print("[SEARCH] Testando sugestões baseadas em aprendizado...\n")
    
    # Testar sugestões para novas tarefas
    test_tasks = [
        "Criar relatório de performance trimestral",
        "Buscar tendências de mercado",
        "Criar dashboard de métricas"
    ]
    
    for task in test_tasks:
        print(f"[NOTE] Tarefa: {task}")
        suggestion = await learning_engine.suggest_best_approach(task)
        
        print(f"   [TARGET] Abordagem sugerida: {suggestion['approach']}")
        print(f"   [POWER] Confiança: {suggestion['confidence']*100:.1f}%")
        print(f"   ⏱️ Tempo esperado: {suggestion.get('expected_time', 0):.1f}s")
        print(f"   [STATS] Baseado em: {suggestion.get('based_on', 0)} experiências")
        print()
    
    # Relatório de habilidades
    print("-"*60)
    print("[STATS] RELATÓRIO DE HABILIDADES\n")
    
    skills_report = learning_engine.get_skill_report()
    
    print(f"Total de habilidades: {skills_report['total_skills']}")
    print("\nTop habilidades:")
    for skill in skills_report['top_skills']:
        print(f"  • {skill['name']}: {skill['proficiency']*100:.1f}% ({skill['mastery_level']})")
    
    # Identificar padrões
    print("\n" + "-"*60)
    print("[AI] PADRÕES IDENTIFICADOS\n")
    
    patterns = memory.identify_patterns()
    
    for pattern in patterns[:5]:
        print(f"[PATTERN] {pattern.description}")
        print(f"   Tipo: {pattern.pattern_type}")
        print(f"   Ocorrências: {pattern.occurrences}")
        if pattern.success_rate > 0:
            print(f"   Taxa de sucesso: {pattern.success_rate*100:.1f}%")
        if pattern.recommendations:
            print(f"   Recomendação: {pattern.recommendations[0]}")
        print()
    
    print("="*60)
    print("[*] SISTEMA DE AUTO-MELHORIA ATIVO!")
    print("O Prometheus agora aprende com cada execução")
    print("e fica mais inteligente a cada tarefa!")
    print("="*60)


# Alias for backward compatibility
SelfImprovementEngine = PrometheusLearningEngine


if __name__ == "__main__":
    # Executar demonstração
    asyncio.run(demonstration())
