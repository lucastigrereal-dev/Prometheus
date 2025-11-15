"""
TASK ANALYZER - Analisador Avançado de Comandos
Parser NLP que entende qualquer comando e decompõe em ações atômicas
"""

import re
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import spacy
from collections import defaultdict

# Tenta carregar spaCy, se não tiver, usa regex
try:
    nlp = spacy.load("pt_core_news_sm")
    SPACY_AVAILABLE = True
except:
    SPACY_AVAILABLE = False
    print("SpaCy não disponível - usando análise por regex")

@dataclass
class Intent:
    """Representa uma intenção detectada"""
    name: str
    confidence: float
    entities: List[Dict[str, Any]]
    action_type: str  # create, read, update, delete, analyze, communicate

@dataclass
class Entity:
    """Representa uma entidade extraída"""
    text: str
    type: str  # person, org, product, date, email, url, number
    value: Any
    position: Tuple[int, int]  # start, end no texto

class AdvancedTaskAnalyzer:
    """
    Analisador avançado que entende comandos complexos
    e os decompõe em tarefas executáveis
    """
    
    def __init__(self):
        self.intent_patterns = self._load_intent_patterns()
        self.entity_patterns = self._load_entity_patterns()
        self.decomposition_rules = self._load_decomposition_rules()
        
    def _load_intent_patterns(self) -> Dict[str, Dict]:
        """Carrega padrões para detecção de intenção"""
        return {
            'create_website': {
                'patterns': [
                    r'(criar?|fazer?|desenvolver?|montar?|construir?).{0,10}(site|website|página|landing)',
                    r'(site|website|página).{0,10}(para|pro|pra)',
                    r'(preciso|quero|necessito).{0,10}(site|website)'
                ],
                'action_type': 'create',
                'confidence_base': 0.9
            },
            'send_communication': {
                'patterns': [
                    r'(enviar?|mandar?|disparar?).{0,10}(mensagem|email|whatsapp|sms)',
                    r'(comunicar?|avisar?|notificar?).{0,10}(cliente|equipe|todos)',
                    r'(mensagem|email|whatsapp).{0,10}(para|pro|pra)'
                ],
                'action_type': 'communicate',
                'confidence_base': 0.85
            },
            'analyze_data': {
                'patterns': [
                    r'(analisar?|análise|verificar?|checar?).{0,10}(dados|métricas|resultados)',
                    r'(relatório|dashboard|gráfico).{0,10}(de|sobre|com)',
                    r'(como está|como estão|qual).{0,10}(vendas|tráfego|conversão)'
                ],
                'action_type': 'analyze',
                'confidence_base': 0.88
            },
            'automate_process': {
                'patterns': [
                    r'(automatizar?|automação|criar?.{0,5}bot|rotina automática)',
                    r'(fazer?.{0,10}automático|processo.{0,10}automático)',
                    r'(sempre que|toda vez que|quando).{0,20}(fazer|executar|rodar)'
                ],
                'action_type': 'create',
                'confidence_base': 0.87
            },
            'manage_social': {
                'patterns': [
                    r'(postar?|publicar?|post).{0,10}(instagram|facebook|linkedin)',
                    r'(stories|feed|reels).{0,10}(criar|fazer|publicar)',
                    r'(conteúdo|posts?|publicação).{0,10}(rede social|social media)'
                ],
                'action_type': 'create',
                'confidence_base': 0.86
            },
            'configure_integration': {
                'patterns': [
                    r'(configurar?|integrar?|conectar?).{0,10}(api|sistema|ferramenta)',
                    r'(sincronizar?|sync).{0,10}(dados|informações)',
                    r'(webhook|zapier|n8n|make).{0,10}(configurar|criar|setup)'
                ],
                'action_type': 'update',
                'confidence_base': 0.84
            }
        }
    
    def _load_entity_patterns(self) -> Dict[str, Dict]:
        """Carrega padrões para extração de entidades"""
        return {
            'email': {
                'pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
                'type': 'contact'
            },
            'url': {
                'pattern': r'https?://[^\s]+|www\.[^\s]+',
                'type': 'resource'
            },
            'phone': {
                'pattern': r'(\+?55)?[\s-]?\(?[1-9]{2}\)?[\s-]?[9]?[0-9]{4}[\s-]?[0-9]{4}',
                'type': 'contact'
            },
            'date': {
                'pattern': r'\b(hoje|amanhã|ontem|segunda|terça|quarta|quinta|sexta|sábado|domingo)\b',
                'type': 'temporal'
            },
            'time': {
                'pattern': r'\b([0-1]?[0-9]|2[0-3]):[0-5][0-9]\b|\b([0-1]?[0-9]|2[0-3])h\b',
                'type': 'temporal'
            },
            'priority': {
                'pattern': r'\b(urgente|crítico|alta prioridade|importante|agora|imediato)\b',
                'type': 'modifier'
            },
            'client': {
                'pattern': r'cliente\s+([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)',
                'type': 'person'
            }
        }
    
    def _load_decomposition_rules(self) -> Dict[str, List[str]]:
        """Regras para decompor tarefas complexas em subtarefas"""
        return {
            'create_website': [
                "Analisar requisitos e objetivos do site",
                "Pesquisar referências e competitors",
                "Criar wireframe e estrutura de páginas",
                "Desenvolver design visual e identidade",
                "Implementar HTML/CSS responsivo",
                "Adicionar interatividade com JavaScript",
                "Configurar formulários de contato",
                "Otimizar para SEO on-page",
                "Testar em diferentes dispositivos",
                "Fazer deploy e configurar domínio"
            ],
            'send_communication': [
                "Identificar lista de destinatários",
                "Preparar template de mensagem",
                "Personalizar conteúdo por segmento",
                "Validar dados de contato",
                "Configurar canal de envio",
                "Executar disparo",
                "Monitorar entrega",
                "Coletar métricas de engajamento"
            ],
            'analyze_data': [
                "Conectar às fontes de dados",
                "Extrair dados do período",
                "Limpar e normalizar dados",
                "Calcular métricas principais",
                "Identificar tendências e padrões",
                "Criar visualizações",
                "Gerar insights acionáveis",
                "Preparar relatório executivo"
            ],
            'automate_process': [
                "Mapear processo atual",
                "Identificar pontos de automação",
                "Definir triggers e condições",
                "Criar fluxo de automação",
                "Configurar integrações necessárias",
                "Implementar tratamento de erros",
                "Testar em ambiente controlado",
                "Documentar processo",
                "Ativar e monitorar"
            ]
        }
    
    def analyze(self, command: str) -> Dict[str, Any]:
        """
        Analisa um comando e retorna estrutura completa
        com intenções, entidades e plano de ação
        """
        
        # Normaliza o comando
        command_normalized = self._normalize_text(command)
        
        # Detecta intenções
        intents = self._detect_intents(command_normalized)
        
        # Extrai entidades
        entities = self._extract_entities(command)
        
        # Gera contexto
        context = self._build_context(command, intents, entities)
        
        # Decompõe em subtarefas
        subtasks = self._decompose_task(intents, entities, context)
        
        # Calcula complexidade
        complexity = self._calculate_complexity(subtasks, entities)
        
        return {
            'original_command': command,
            'normalized_command': command_normalized,
            'intents': intents,
            'entities': entities,
            'context': context,
            'subtasks': subtasks,
            'complexity': complexity,
            'estimated_time': self._estimate_time(complexity, len(subtasks)),
            'confidence': self._calculate_confidence(intents),
            'suggested_ai': self._suggest_ai_provider(intents, complexity)
        }
    
    def _normalize_text(self, text: str) -> str:
        """Normaliza texto para análise"""
        # Remove pontuação excessiva
        text = re.sub(r'[!?]{2,}', '!', text)
        # Remove espaços extras
        text = re.sub(r'\s+', ' ', text)
        # Lowercase para comparação
        text = text.lower().strip()
        return text
    
    def _detect_intents(self, text: str) -> List[Intent]:
        """Detecta intenções no comando"""
        detected_intents = []
        
        for intent_name, intent_data in self.intent_patterns.items():
            for pattern in intent_data['patterns']:
                if re.search(pattern, text, re.IGNORECASE):
                    intent = Intent(
                        name=intent_name,
                        confidence=intent_data['confidence_base'],
                        entities=[],
                        action_type=intent_data['action_type']
                    )
                    detected_intents.append(intent)
                    break
        
        # Se não detectou nenhuma intenção específica, tenta genérica
        if not detected_intents:
            detected_intents.append(Intent(
                name='generic_task',
                confidence=0.5,
                entities=[],
                action_type='execute'
            ))
        
        return detected_intents
    
    def _extract_entities(self, text: str) -> List[Entity]:
        """Extrai entidades do texto"""
        entities = []
        
        # Usa SpaCy se disponível
        if SPACY_AVAILABLE:
            doc = nlp(text)
            for ent in doc.ents:
                entities.append(Entity(
                    text=ent.text,
                    type=ent.label_,
                    value=ent.text,
                    position=(ent.start_char, ent.end_char)
                ))
        
        # Adiciona entidades por regex
        for entity_type, entity_data in self.entity_patterns.items():
            pattern = entity_data['pattern']
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append(Entity(
                    text=match.group(),
                    type=entity_type,
                    value=match.group(),
                    position=(match.start(), match.end())
                ))
        
        # Remove duplicatas
        seen = set()
        unique_entities = []
        for entity in entities:
            key = (entity.text, entity.type)
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    def _build_context(
        self,
        command: str,
        intents: List[Intent],
        entities: List[Entity]
    ) -> Dict[str, Any]:
        """Constrói contexto da tarefa"""
        
        context = {
            'timestamp': datetime.now().isoformat(),
            'command_length': len(command),
            'word_count': len(command.split()),
            'has_urgency': any(e.type == 'priority' for e in entities),
            'has_contact': any(e.type in ['email', 'phone'] for e in entities),
            'has_temporal': any(e.type == 'temporal' for e in entities),
            'primary_action': intents[0].action_type if intents else 'unknown',
            'multi_intent': len(intents) > 1,
            'entities_count': len(entities),
            'intent_names': [i.name for i in intents]
        }
        
        # Adiciona informações específicas por intenção
        if 'create_website' in context['intent_names']:
            context['website_type'] = self._detect_website_type(command)
            context['has_deadline'] = context['has_temporal']
        
        if 'send_communication' in context['intent_names']:
            context['communication_channel'] = self._detect_channel(command)
            context['is_broadcast'] = 'todos' in command or 'all' in command
        
        return context
    
    def _detect_website_type(self, command: str) -> str:
        """Detecta tipo de site solicitado"""
        if any(word in command.lower() for word in ['landing', 'conversão', 'captura']):
            return 'landing_page'
        elif any(word in command.lower() for word in ['loja', 'ecommerce', 'vender']):
            return 'ecommerce'
        elif any(word in command.lower() for word in ['blog', 'artigos', 'posts']):
            return 'blog'
        else:
            return 'institutional'
    
    def _detect_channel(self, command: str) -> str:
        """Detecta canal de comunicação"""
        channels = {
            'whatsapp': ['whatsapp', 'whats', 'zap'],
            'email': ['email', 'e-mail', '@'],
            'sms': ['sms', 'mensagem de texto'],
            'slack': ['slack'],
            'teams': ['teams', 'microsoft teams']
        }
        
        command_lower = command.lower()
        for channel, keywords in channels.items():
            if any(kw in command_lower for kw in keywords):
                return channel
        
        return 'email'  # default
    
    def _decompose_task(
        self,
        intents: List[Intent],
        entities: List[Entity],
        context: Dict
    ) -> List[Dict[str, Any]]:
        """Decompõe tarefa em subtarefas executáveis"""
        
        subtasks = []
        
        for intent in intents:
            # Pega template de decomposição
            if intent.name in self.decomposition_rules:
                base_subtasks = self.decomposition_rules[intent.name]
                
                # Personaliza subtarefas baseado no contexto
                for i, subtask_description in enumerate(base_subtasks):
                    subtask = {
                        'id': f"subtask_{i+1}",
                        'description': subtask_description,
                        'intent': intent.name,
                        'priority': 'high' if context.get('has_urgency') else 'normal',
                        'dependencies': [f"subtask_{i}"] if i > 0 else [],
                        'estimated_minutes': 5 + (i * 2),  # Estimativa simples
                        'required_capabilities': self._identify_capabilities(subtask_description),
                        'entities': [e.__dict__ for e in entities if self._is_relevant_entity(e, subtask_description)]
                    }
                    subtasks.append(subtask)
        
        # Se não tem decomposição definida, cria genérica
        if not subtasks:
            subtasks.append({
                'id': 'subtask_1',
                'description': f"Executar: {intents[0].name if intents else 'tarefa'}",
                'intent': intents[0].name if intents else 'generic',
                'priority': 'normal',
                'dependencies': [],
                'estimated_minutes': 10,
                'required_capabilities': ['general'],
                'entities': [e.__dict__ for e in entities]
            })
        
        return subtasks
    
    def _identify_capabilities(self, task_description: str) -> List[str]:
        """Identifica capacidades necessárias para uma subtarefa"""
        capabilities = []
        
        capability_keywords = {
            'browser': ['site', 'página', 'navegar', 'web', 'html', 'css'],
            'api': ['api', 'integrar', 'webhook', 'endpoint'],
            'database': ['dados', 'banco', 'query', 'sql'],
            'file_system': ['arquivo', 'pasta', 'salvar', 'criar arquivo'],
            'communication': ['enviar', 'mensagem', 'email', 'whatsapp'],
            'ai': ['analisar', 'gerar', 'criar conteúdo', 'escrever']
        }
        
        task_lower = task_description.lower()
        for capability, keywords in capability_keywords.items():
            if any(kw in task_lower for kw in keywords):
                capabilities.append(capability)
        
        return capabilities if capabilities else ['general']
    
    def _is_relevant_entity(self, entity: Entity, subtask_description: str) -> bool:
        """Verifica se entidade é relevante para subtarefa"""
        # Simplificado - seria mais sofisticado
        return entity.text.lower() in subtask_description.lower()
    
    def _calculate_complexity(self, subtasks: List[Dict], entities: List[Entity]) -> str:
        """Calcula complexidade da tarefa"""
        
        points = 0
        
        # Pontos por subtarefas
        points += len(subtasks) * 2
        
        # Pontos por entidades
        points += len(entities)
        
        # Pontos por capabilities únicas
        unique_capabilities = set()
        for subtask in subtasks:
            unique_capabilities.update(subtask.get('required_capabilities', []))
        points += len(unique_capabilities) * 3
        
        # Classifica complexidade
        if points <= 5:
            return 'simple'
        elif points <= 15:
            return 'moderate'
        elif points <= 30:
            return 'complex'
        else:
            return 'very_complex'
    
    def _estimate_time(self, complexity: str, subtask_count: int) -> Dict[str, int]:
        """Estima tempo de execução"""
        
        base_times = {
            'simple': 5,
            'moderate': 15,
            'complex': 30,
            'very_complex': 60
        }
        
        base_time = base_times.get(complexity, 10)
        total_minutes = base_time + (subtask_count * 3)
        
        return {
            'minimum_minutes': int(total_minutes * 0.7),
            'expected_minutes': total_minutes,
            'maximum_minutes': int(total_minutes * 1.5)
        }
    
    def _calculate_confidence(self, intents: List[Intent]) -> float:
        """Calcula confiança geral da análise"""
        if not intents:
            return 0.0
        
        # Média ponderada das confianças
        total_confidence = sum(i.confidence for i in intents)
        return min(total_confidence / len(intents), 1.0)
    
    def _suggest_ai_provider(self, intents: List[Intent], complexity: str) -> str:
        """Sugere melhor provedor de IA para a tarefa"""
        
        # Mapeamento de intenção para melhor IA
        intent_to_ai = {
            'create_website': 'gpt-4',  # Melhor para código
            'analyze_data': 'claude',    # Melhor para análise
            'send_communication': 'gemini',  # Rápido e eficiente
            'automate_process': 'claude',    # Bom para lógica
            'manage_social': 'gpt-4',        # Criativo
            'configure_integration': 'claude' # Técnico
        }
        
        # Se tem intenção específica, usa mapeamento
        if intents and intents[0].name in intent_to_ai:
            return intent_to_ai[intents[0].name]
        
        # Senão, decide por complexidade
        if complexity in ['simple', 'moderate']:
            return 'gemini'  # Mais barato para tarefas simples
        else:
            return 'claude'   # Mais capaz para tarefas complexas

# ============================================================================
# Exemplo de uso
# ============================================================================

def example_usage():
    """Demonstra uso do analisador avançado"""
    
    analyzer = AdvancedTaskAnalyzer()
    
    # Comandos de teste
    test_commands = [
        "Criar um site urgente para o cliente João Silva com formulário de contato e integração com WhatsApp",
        "Analisar dados de vendas do último mês e enviar relatório para diretoria@empresa.com",
        "Automatizar postagem no Instagram sempre que publicar novo artigo no blog",
        "Enviar mensagem para todos os clientes sobre promoção de Black Friday até amanhã 18h"
    ]
    
    for command in test_commands:
        print(f"\n{'='*80}")
        print(f"COMANDO: {command}")
        print('='*80)
        
        result = analyzer.analyze(command)
        
        print(f"\n📊 ANÁLISE COMPLETA:")
        print(f"Intenções detectadas: {[i.name for i in result['intents']]}")
        print(f"Entidades encontradas: {len(result['entities'])}")
        print(f"Complexidade: {result['complexity']}")
        print(f"Tempo estimado: {result['estimated_time']['expected_minutes']} minutos")
        print(f"Confiança: {result['confidence']:.2%}")
        print(f"IA sugerida: {result['suggested_ai']}")
        
        print(f"\n📝 SUBTAREFAS ({len(result['subtasks'])}):")
        for subtask in result['subtasks']:
            deps = subtask['dependencies']
            deps_str = f" (depende de: {', '.join(deps)})" if deps else ""
            print(f"  [{subtask['id']}] {subtask['description']}{deps_str}")
            print(f"       Capacidades: {', '.join(subtask['required_capabilities'])}")
        
        if result['entities']:
            print(f"\n🏷️ ENTIDADES:")
            for entity in result['entities']:
                print(f"  - {entity.text} ({entity.type})")

if __name__ == "__main__":
    example_usage()
