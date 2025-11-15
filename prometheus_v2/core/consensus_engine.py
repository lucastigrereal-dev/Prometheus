"""
CONSENSUS ENGINE - Motor de Consenso Multi-IA
Sistema de votação, análise e síntese de respostas múltiplas
"""

import asyncio
import json
import time
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from collections import defaultdict, Counter

logger = logging.getLogger('ConsensusEngine')

# ============================================================================
# ESTRUTURAS DE DADOS
# ============================================================================

class ConsensusStrategy(Enum):
    """Estratégias de consenso disponíveis"""
    MAJORITY_VOTE = "majority_vote"      # Votação simples
    WEIGHTED_VOTE = "weighted_vote"      # Votação ponderada
    CONFIDENCE_BASED = "confidence_based" # Baseado em confiança
    SYNTHESIS = "synthesis"              # Síntese de respostas
    ARBITER = "arbiter"                  # Árbitro decide
    ENSEMBLE = "ensemble"                # Ensemble learning
    HIERARCHICAL = "hierarchical"        # Hierárquico

@dataclass
class AIVote:
    """Representa voto de uma IA"""
    provider: str
    content: str
    confidence: float = 0.5
    reasoning: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    timestamp: float = field(default_factory=time.time)

@dataclass
class ConsensusResult:
    """Resultado do processo de consenso"""
    final_answer: str
    strategy_used: ConsensusStrategy
    votes: List[AIVote]
    confidence: float
    agreement_score: float
    synthesis: Optional[str] = None
    dissenting_opinions: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0

# ============================================================================
# CONSENSUS ENGINE - Motor Principal
# ============================================================================

class ConsensusEngine:
    """
    Motor de consenso para decisões multi-IA
    Combina múltiplas respostas em decisão única e superior
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Pesos padrão por provider
        self.provider_weights = {
            'claude': 1.5,      # Melhor em raciocínio
            'gpt-4': 1.3,       # Melhor em criatividade
            'perplexity': 1.2,  # Melhor em pesquisa
            'gemini': 1.0,      # Baseline
            'grok': 1.1         # Bom em análise
        }
        
        # Configurações
        self.min_votes = self.config.get('min_votes', 2)
        self.max_votes = self.config.get('max_votes', 5)
        self.confidence_threshold = self.config.get('confidence_threshold', 0.6)
        self.arbiter_provider = self.config.get('arbiter', 'gpt-4')  # Aurora
        
        # Cache de decisões
        self.decision_cache = {}
        self.cache_ttl = 3600  # 1 hora
        
        # Métricas
        self.consensus_history = []
        self.strategy_success_rates = defaultdict(lambda: {'success': 0, 'total': 0})
        
        logger.info("✅ Consensus Engine initialized")
    
    async def reach_consensus(
        self,
        votes: List[AIVote],
        strategy: ConsensusStrategy = None,
        context: Dict[str, Any] = None
    ) -> ConsensusResult:
        """
        Alcança consenso entre múltiplos votos de IA
        """
        
        start_time = time.time()
        
        # Validação
        if len(votes) < self.min_votes:
            logger.warning(f"Insufficient votes: {len(votes)} < {self.min_votes}")
            return self._single_vote_result(votes[0] if votes else None)
        
        # Determina estratégia se não especificada
        if not strategy:
            strategy = self._select_best_strategy(votes, context)
        
        logger.info(f"Using consensus strategy: {strategy.value}")
        
        # Aplica estratégia
        if strategy == ConsensusStrategy.MAJORITY_VOTE:
            result = await self._majority_vote(votes)
            
        elif strategy == ConsensusStrategy.WEIGHTED_VOTE:
            result = await self._weighted_vote(votes)
            
        elif strategy == ConsensusStrategy.CONFIDENCE_BASED:
            result = await self._confidence_based(votes)
            
        elif strategy == ConsensusStrategy.SYNTHESIS:
            result = await self._synthesis(votes, context)
            
        elif strategy == ConsensusStrategy.ARBITER:
            result = await self._arbiter_decision(votes, context)
            
        elif strategy == ConsensusStrategy.ENSEMBLE:
            result = await self._ensemble_method(votes, context)
            
        elif strategy == ConsensusStrategy.HIERARCHICAL:
            result = await self._hierarchical_consensus(votes, context)
            
        else:
            result = await self._weighted_vote(votes)  # Default
        
        # Adiciona metadados
        result.processing_time = time.time() - start_time
        result.votes = votes
        result.strategy_used = strategy
        
        # Calcula métricas
        result.agreement_score = self._calculate_agreement_score(votes)
        result.confidence = self._calculate_final_confidence(result, votes)
        
        # Identifica opiniões divergentes
        result.dissenting_opinions = self._identify_dissenting_opinions(votes, result)
        
        # Adiciona ao histórico
        self._update_history(result)
        
        return result
    
    def _select_best_strategy(
        self,
        votes: List[AIVote],
        context: Dict[str, Any] = None
    ) -> ConsensusStrategy:
        """Seleciona melhor estratégia baseado no contexto"""
        
        # Análise dos votos
        confidence_variance = np.var([v.confidence for v in votes])
        has_high_confidence = any(v.confidence > 0.8 for v in votes)
        is_critical = context and context.get('priority') == 'critical'
        is_creative = context and 'creative' in context.get('task_type', '')
        
        # Decisão heurística
        if is_critical:
            # Tarefas críticas usam árbitro
            return ConsensusStrategy.ARBITER
        
        elif is_creative:
            # Tarefas criativas usam síntese
            return ConsensusStrategy.SYNTHESIS
        
        elif confidence_variance < 0.1 and has_high_confidence:
            # Alta concordância e confiança - voto simples
            return ConsensusStrategy.MAJORITY_VOTE
        
        elif confidence_variance > 0.3:
            # Alta discordância - precisa ensemble
            return ConsensusStrategy.ENSEMBLE
        
        else:
            # Caso padrão - voto ponderado
            return ConsensusStrategy.WEIGHTED_VOTE
    
    async def _majority_vote(self, votes: List[AIVote]) -> ConsensusResult:
        """Votação por maioria simples"""
        
        # Agrupa respostas similares
        vote_groups = self._group_similar_responses(votes)
        
        # Conta votos por grupo
        group_counts = {
            group_id: len(group_votes)
            for group_id, group_votes in vote_groups.items()
        }
        
        # Encontra maioria
        winning_group = max(group_counts, key=group_counts.get)
        winning_votes = vote_groups[winning_group]
        
        # Resposta final é a de maior confiança no grupo vencedor
        best_vote = max(winning_votes, key=lambda v: v.confidence)
        
        return ConsensusResult(
            final_answer=best_vote.content,
            strategy_used=ConsensusStrategy.MAJORITY_VOTE,
            votes=votes,
            confidence=best_vote.confidence,
            agreement_score=len(winning_votes) / len(votes),
            metadata={
                'winning_group_size': len(winning_votes),
                'total_groups': len(vote_groups)
            }
        )
    
    async def _weighted_vote(self, votes: List[AIVote]) -> ConsensusResult:
        """Votação ponderada por peso e confiança"""
        
        # Calcula peso total para cada resposta única
        response_weights = defaultdict(float)
        response_votes = defaultdict(list)
        
        for vote in votes:
            # Peso final = peso do provider * confiança
            provider_weight = self.provider_weights.get(vote.provider, 1.0)
            final_weight = provider_weight * vote.confidence * vote.weight
            
            # Usa hash para agrupar respostas idênticas
            response_hash = self._hash_response(vote.content)
            response_weights[response_hash] += final_weight
            response_votes[response_hash].append(vote)
        
        # Encontra resposta com maior peso
        winning_hash = max(response_weights, key=response_weights.get)
        winning_votes = response_votes[winning_hash]
        winning_weight = response_weights[winning_hash]
        
        # Melhor voto do grupo vencedor
        best_vote = max(winning_votes, key=lambda v: v.confidence)
        
        # Calcula confiança ponderada
        total_weight = sum(response_weights.values())
        weighted_confidence = winning_weight / total_weight if total_weight > 0 else 0
        
        return ConsensusResult(
            final_answer=best_vote.content,
            strategy_used=ConsensusStrategy.WEIGHTED_VOTE,
            votes=votes,
            confidence=weighted_confidence,
            agreement_score=len(winning_votes) / len(votes),
            metadata={
                'winning_weight': winning_weight,
                'total_weight': total_weight,
                'weight_distribution': dict(response_weights)
            }
        )
    
    async def _confidence_based(self, votes: List[AIVote]) -> ConsensusResult:
        """Decisão baseada em confiança"""
        
        # Filtra votos com confiança mínima
        confident_votes = [
            v for v in votes 
            if v.confidence >= self.confidence_threshold
        ]
        
        if not confident_votes:
            # Se nenhum voto confiante, pega o de maior confiança
            confident_votes = [max(votes, key=lambda v: v.confidence)]
        
        # Entre os confiantes, usa weighted vote
        if len(confident_votes) > 1:
            return await self._weighted_vote(confident_votes)
        else:
            vote = confident_votes[0]
            return ConsensusResult(
                final_answer=vote.content,
                strategy_used=ConsensusStrategy.CONFIDENCE_BASED,
                votes=votes,
                confidence=vote.confidence,
                agreement_score=1.0,
                metadata={'filtered_votes': len(votes) - len(confident_votes)}
            )
    
    async def _synthesis(
        self,
        votes: List[AIVote],
        context: Dict[str, Any] = None
    ) -> ConsensusResult:
        """Sintetiza múltiplas respostas em uma única superior"""
        
        # Extrai pontos principais de cada voto
        key_points = []
        for vote in votes:
            points = self._extract_key_points(vote.content)
            key_points.extend(points)
        
        # Remove duplicatas mantendo ordem
        seen = set()
        unique_points = []
        for point in key_points:
            if point not in seen:
                seen.add(point)
                unique_points.append(point)
        
        # Cria síntese
        synthesis = self._create_synthesis(unique_points, votes, context)
        
        # Calcula confiança da síntese
        avg_confidence = np.mean([v.confidence for v in votes])
        
        return ConsensusResult(
            final_answer=synthesis,
            strategy_used=ConsensusStrategy.SYNTHESIS,
            votes=votes,
            confidence=avg_confidence,
            agreement_score=self._calculate_agreement_score(votes),
            synthesis=synthesis,
            metadata={
                'key_points': len(unique_points),
                'sources': [v.provider for v in votes]
            }
        )
    
    def _extract_key_points(self, text: str) -> List[str]:
        """Extrai pontos principais do texto"""
        # Simplificado - seria NLP mais sofisticado
        
        points = []
        
        # Divide em sentenças
        sentences = text.split('. ')
        
        for sentence in sentences:
            # Ignora muito curtas ou muito longas
            if 10 < len(sentence) < 200:
                points.append(sentence.strip())
        
        return points[:5]  # Máximo 5 pontos por resposta
    
    def _create_synthesis(
        self,
        points: List[str],
        votes: List[AIVote],
        context: Dict[str, Any] = None
    ) -> str:
        """Cria síntese a partir dos pontos"""
        
        # Agrupa pontos por tema (simplificado)
        synthesis_parts = []
        
        # Introdução mencionando consenso
        if len(votes) > 2:
            synthesis_parts.append(
                f"Baseado na análise de {len(votes)} perspectivas diferentes:"
            )
        
        # Pontos principais
        for i, point in enumerate(points[:10], 1):
            synthesis_parts.append(f"{i}. {point}")
        
        # Conclusão
        if context and 'action_required' in context:
            synthesis_parts.append(
                "\nAção recomendada: Implementar as sugestões acima de forma integrada."
            )
        
        return "\n".join(synthesis_parts)
    
    async def _arbiter_decision(
        self,
        votes: List[AIVote],
        context: Dict[str, Any] = None
    ) -> ConsensusResult:
        """Árbitro (Aurora/GPT-4) decide entre as opções"""
        
        # Formata opções para o árbitro
        options = [
            {
                'source': vote.provider,
                'content': vote.content,
                'confidence': vote.confidence,
                'reasoning': vote.reasoning
            }
            for vote in votes
        ]
        
        # Simula decisão do árbitro (seria chamada real para GPT-4)
        # Em produção, isso chamaria gpt_provider.arbitrate()
        
        # Por enquanto, simula escolhendo a de maior confiança ponderada
        best_vote = max(
            votes,
            key=lambda v: v.confidence * self.provider_weights.get(v.provider, 1.0)
        )
        
        arbiter_reasoning = f"""
        Após análise das {len(votes)} opções apresentadas:
        - Opção escolhida: {best_vote.provider}
        - Razão: Maior combinação de confiança ({best_vote.confidence:.2f}) e expertise
        - Síntese: A resposta escolhida oferece o melhor equilíbrio entre precisão e aplicabilidade
        """
        
        return ConsensusResult(
            final_answer=best_vote.content,
            strategy_used=ConsensusStrategy.ARBITER,
            votes=votes,
            confidence=best_vote.confidence * 1.1,  # Boost por validação do árbitro
            agreement_score=1.0,  # Árbitro tem autoridade total
            synthesis=arbiter_reasoning,
            metadata={
                'arbiter': self.arbiter_provider,
                'chosen_provider': best_vote.provider,
                'arbiter_reasoning': arbiter_reasoning
            }
        )
    
    async def _ensemble_method(
        self,
        votes: List[AIVote],
        context: Dict[str, Any] = None
    ) -> ConsensusResult:
        """Método ensemble combinando múltiplas estratégias"""
        
        # Aplica múltiplas estratégias
        strategies_results = []
        
        # 1. Majority vote
        majority_result = await self._majority_vote(votes)
        strategies_results.append(('majority', majority_result))
        
        # 2. Weighted vote
        weighted_result = await self._weighted_vote(votes)
        strategies_results.append(('weighted', weighted_result))
        
        # 3. Confidence based
        confidence_result = await self._confidence_based(votes)
        strategies_results.append(('confidence', confidence_result))
        
        # Combina resultados
        # Conta quantas estratégias concordam
        answer_counts = Counter()
        confidence_sum = defaultdict(float)
        
        for strategy_name, result in strategies_results:
            answer_hash = self._hash_response(result.final_answer)
            answer_counts[answer_hash] += 1
            confidence_sum[answer_hash] += result.confidence
        
        # Resposta final é a mais votada entre as estratégias
        winning_hash = max(
            answer_counts,
            key=lambda h: (answer_counts[h], confidence_sum[h])
        )
        
        # Encontra o resultado original correspondente
        for _, result in strategies_results:
            if self._hash_response(result.final_answer) == winning_hash:
                final_answer = result.final_answer
                break
        
        ensemble_confidence = confidence_sum[winning_hash] / len(strategies_results)
        
        return ConsensusResult(
            final_answer=final_answer,
            strategy_used=ConsensusStrategy.ENSEMBLE,
            votes=votes,
            confidence=ensemble_confidence,
            agreement_score=answer_counts[winning_hash] / len(strategies_results),
            metadata={
                'strategies_used': len(strategies_results),
                'strategy_agreement': answer_counts[winning_hash],
                'all_results': [
                    (name, r.final_answer[:100]) 
                    for name, r in strategies_results
                ]
            }
        )
    
    async def _hierarchical_consensus(
        self,
        votes: List[AIVote],
        context: Dict[str, Any] = None
    ) -> ConsensusResult:
        """Consenso hierárquico - agrupa por confiança e decide por níveis"""
        
        # Divide votos em tiers de confiança
        high_confidence = [v for v in votes if v.confidence >= 0.8]
        medium_confidence = [v for v in votes if 0.5 <= v.confidence < 0.8]
        low_confidence = [v for v in votes if v.confidence < 0.5]
        
        # Tenta consenso começando pelo tier mais alto
        if high_confidence:
            if len(high_confidence) == 1:
                result = self._single_vote_result(high_confidence[0])
            else:
                result = await self._weighted_vote(high_confidence)
            result.metadata['tier'] = 'high'
            
        elif medium_confidence:
            result = await self._weighted_vote(medium_confidence)
            result.metadata['tier'] = 'medium'
            
        else:
            # Usa todos os votos se só tem low confidence
            result = await self._synthesis(votes, context)
            result.metadata['tier'] = 'low_synthesis'
        
        result.strategy_used = ConsensusStrategy.HIERARCHICAL
        result.metadata['confidence_distribution'] = {
            'high': len(high_confidence),
            'medium': len(medium_confidence),
            'low': len(low_confidence)
        }
        
        return result
    
    def _group_similar_responses(
        self,
        votes: List[AIVote],
        similarity_threshold: float = 0.8
    ) -> Dict[str, List[AIVote]]:
        """Agrupa respostas similares"""
        
        groups = {}
        
        for vote in votes:
            # Verifica se pertence a algum grupo existente
            assigned = False
            
            for group_id, group_votes in groups.items():
                # Compara com primeiro voto do grupo
                if self._calculate_similarity(vote.content, group_votes[0].content) >= similarity_threshold:
                    group_votes.append(vote)
                    assigned = True
                    break
            
            # Se não foi atribuído, cria novo grupo
            if not assigned:
                group_id = self._hash_response(vote.content)
                groups[group_id] = [vote]
        
        return groups
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calcula similaridade entre dois textos"""
        
        # Simplificado - seria embedding similarity
        # Por enquanto usa Jaccard similarity
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if not union:
            return 0.0
        
        return len(intersection) / len(union)
    
    def _calculate_agreement_score(self, votes: List[AIVote]) -> float:
        """Calcula score de concordância entre votos"""
        
        if len(votes) < 2:
            return 1.0
        
        # Calcula similaridade média entre todos os pares
        similarities = []
        
        for i in range(len(votes)):
            for j in range(i + 1, len(votes)):
                sim = self._calculate_similarity(
                    votes[i].content,
                    votes[j].content
                )
                similarities.append(sim)
        
        return np.mean(similarities) if similarities else 0.0
    
    def _calculate_final_confidence(
        self,
        result: ConsensusResult,
        votes: List[AIVote]
    ) -> float:
        """Calcula confiança final do resultado"""
        
        # Fatores que influenciam confiança
        factors = []
        
        # 1. Confiança média dos votos
        avg_confidence = np.mean([v.confidence for v in votes])
        factors.append(avg_confidence)
        
        # 2. Score de concordância
        factors.append(result.agreement_score)
        
        # 3. Número de votos (normalizado)
        vote_factor = min(len(votes) / self.max_votes, 1.0)
        factors.append(vote_factor)
        
        # 4. Boost por estratégia
        strategy_boosts = {
            ConsensusStrategy.ARBITER: 1.1,
            ConsensusStrategy.ENSEMBLE: 1.05,
            ConsensusStrategy.SYNTHESIS: 1.0,
            ConsensusStrategy.WEIGHTED_VOTE: 0.95,
            ConsensusStrategy.MAJORITY_VOTE: 0.9
        }
        boost = strategy_boosts.get(result.strategy_used, 1.0)
        
        # Confiança final é média ponderada
        base_confidence = np.mean(factors)
        final_confidence = min(base_confidence * boost, 1.0)
        
        return final_confidence
    
    def _identify_dissenting_opinions(
        self,
        votes: List[AIVote],
        result: ConsensusResult
    ) -> List[Dict]:
        """Identifica opiniões divergentes"""
        
        dissenting = []
        
        for vote in votes:
            # Considera divergente se muito diferente da resposta final
            similarity = self._calculate_similarity(vote.content, result.final_answer)
            
            if similarity < 0.3:  # Muito diferente
                dissenting.append({
                    'provider': vote.provider,
                    'opinion': vote.content[:200] + '...' if len(vote.content) > 200 else vote.content,
                    'confidence': vote.confidence,
                    'reasoning': vote.reasoning,
                    'similarity_to_consensus': similarity
                })
        
        return dissenting
    
    def _hash_response(self, text: str) -> str:
        """Cria hash de resposta para agrupamento"""
        # Normaliza texto
        normalized = ' '.join(text.lower().split()[:20])  # Primeiras 20 palavras
        return hashlib.md5(normalized.encode()).hexdigest()[:8]
    
    def _single_vote_result(self, vote: Optional[AIVote]) -> ConsensusResult:
        """Cria resultado para voto único"""
        
        if not vote:
            return ConsensusResult(
                final_answer="No votes available",
                strategy_used=ConsensusStrategy.MAJORITY_VOTE,
                votes=[],
                confidence=0.0,
                agreement_score=0.0
            )
        
        return ConsensusResult(
            final_answer=vote.content,
            strategy_used=ConsensusStrategy.MAJORITY_VOTE,
            votes=[vote],
            confidence=vote.confidence,
            agreement_score=1.0,
            metadata={'single_vote': True}
        )
    
    def _update_history(self, result: ConsensusResult):
        """Atualiza histórico de consensos"""
        
        self.consensus_history.append({
            'timestamp': time.time(),
            'strategy': result.strategy_used.value,
            'confidence': result.confidence,
            'agreement': result.agreement_score,
            'vote_count': len(result.votes)
        })
        
        # Limita histórico
        if len(self.consensus_history) > 1000:
            self.consensus_history = self.consensus_history[-1000:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Retorna estatísticas do engine"""
        
        if not self.consensus_history:
            return {'total_consensus': 0}
        
        return {
            'total_consensus': len(self.consensus_history),
            'avg_confidence': np.mean([h['confidence'] for h in self.consensus_history]),
            'avg_agreement': np.mean([h['agreement'] for h in self.consensus_history]),
            'strategy_usage': Counter(h['strategy'] for h in self.consensus_history),
            'avg_vote_count': np.mean([h['vote_count'] for h in self.consensus_history])
        }

# ============================================================================
# EXEMPLO DE USO
# ============================================================================

async def example_usage():
    """Demonstra uso do Consensus Engine"""
    
    # Cria engine
    engine = ConsensusEngine()
    
    print("🤝 Testando Consensus Engine\n")
    
    # Simula votos de diferentes IAs
    votes = [
        AIVote(
            provider="claude",
            content="A melhor abordagem é usar microserviços para escalabilidade e manutenibilidade",
            confidence=0.85,
            reasoning="Microserviços permitem desenvolvimento independente e escala granular"
        ),
        AIVote(
            provider="gpt-4",
            content="Recomendo arquitetura em microserviços com containers Docker e Kubernetes",
            confidence=0.80,
            reasoning="Containers facilitam deployment e Kubernetes gerencia orquestração"
        ),
        AIVote(
            provider="gemini",
            content="Para uma startup, sugiro começar com monolito modular e evoluir para microserviços",
            confidence=0.75,
            reasoning="Monolito é mais simples inicialmente e pode ser refatorado depois"
        ),
        AIVote(
            provider="perplexity",
            content="Baseado em pesquisas recentes, serverless é mais custo-efetivo para startups",
            confidence=0.70,
            reasoning="Serverless reduz custos operacionais e escala automaticamente"
        )
    ]
    
    # Testa diferentes estratégias
    strategies = [
        ConsensusStrategy.MAJORITY_VOTE,
        ConsensusStrategy.WEIGHTED_VOTE,
        ConsensusStrategy.SYNTHESIS,
        ConsensusStrategy.ENSEMBLE
    ]
    
    for strategy in strategies:
        print(f"\n📊 Estratégia: {strategy.value}")
        print("=" * 60)
        
        result = await engine.reach_consensus(
            votes=votes,
            strategy=strategy,
            context={'task_type': 'architecture_decision', 'priority': 'high'}
        )
        
        print(f"Resposta Final: {result.final_answer[:200]}...")
        print(f"Confiança: {result.confidence:.2%}")
        print(f"Concordância: {result.agreement_score:.2%}")
        print(f"Tempo: {result.processing_time:.3f}s")
        
        if result.dissenting_opinions:
            print(f"Opiniões Divergentes: {len(result.dissenting_opinions)}")
    
    # Estatísticas
    print("\n📈 Estatísticas do Engine:")
    stats = engine.get_statistics()
    print(json.dumps(stats, indent=2, default=str))

if __name__ == "__main__":
    asyncio.run(example_usage())
