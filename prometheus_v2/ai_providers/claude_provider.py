"""
CLAUDE PROVIDER - Integração com Anthropic Claude
Provider especializado em raciocínio complexo e análise
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import anthropic
from anthropic import AsyncAnthropic

logger = logging.getLogger('ClaudeProvider')

@dataclass
class ClaudeConfig:
    """Configuração do Claude"""
    api_key: str
    model: str = "claude-3-opus-20240229"
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 1.0
    top_k: int = 40
    timeout: int = 30
    max_retries: int = 3
    rate_limit: int = 100  # requests por minuto

@dataclass
class ClaudeResponse:
    """Resposta do Claude"""
    content: str
    model: str
    tokens_input: int
    tokens_output: int
    latency: float
    cost: float
    metadata: Dict[str, Any]

class ClaudeProvider:
    """
    Provider para Anthropic Claude
    Especializado em raciocínio complexo, análise e planejamento
    """
    
    CAPABILITIES = [
        'complex_reasoning',
        'analysis',
        'planning',
        'coding',
        'mathematics',
        'creative_writing',
        'ethical_reasoning',
        'multi_turn_dialogue'
    ]
    
    COST_PER_1K_INPUT = 0.015
    COST_PER_1K_OUTPUT = 0.075
    
    def __init__(self, config: ClaudeConfig):
        self.config = config
        self.client = AsyncAnthropic(api_key=config.api_key)
        self.sync_client = anthropic.Anthropic(api_key=config.api_key)
        
        # Rate limiting
        self.request_times: List[float] = []
        self.rate_limit = config.rate_limit
        
        # Cache de system prompts
        self.system_prompts = self._load_system_prompts()
        
        logger.info(f"✅ Claude Provider initialized with model {config.model}")
    
    def _load_system_prompts(self) -> Dict[str, str]:
        """Carrega system prompts otimizados para diferentes tarefas"""
        return {
            'default': """Você é Claude, um assistente IA avançado criado pela Anthropic.
Você é especializado em raciocínio complexo, análise profunda e resolução de problemas.
Sempre forneça respostas precisas, bem estruturadas e úteis.""",
            
            'analysis': """Você é um analista especializado. 
Analise profundamente os dados fornecidos, identifique padrões, insights e conclusões.
Use raciocínio estruturado e apresente suas descobertas de forma clara e organizada.""",
            
            'coding': """Você é um programador expert em múltiplas linguagens.
Escreva código limpo, eficiente e bem documentado.
Sempre inclua tratamento de erros e considere edge cases.""",
            
            'planning': """Você é um planejador estratégico especializado.
Crie planos detalhados, considerando dependências, riscos e alternativas.
Organize as tarefas em ordem lógica e estime tempos realistas.""",
            
            'creative': """Você é um escritor criativo e storyteller.
Crie conteúdo original, envolvente e bem escrito.
Mantenha consistência de tom e estilo ao longo do texto."""
        }
    
    async def complete(
        self,
        prompt: str,
        system_prompt: str = None,
        context: List[Dict[str, str]] = None,
        stream: bool = False,
        **kwargs
    ) -> ClaudeResponse:
        """Gera completion com Claude"""
        
        # Rate limiting
        await self._check_rate_limit()
        
        # Prepara mensagens
        messages = self._prepare_messages(prompt, context)
        
        # System prompt
        if not system_prompt:
            system_prompt = self.system_prompts['default']
        
        # Parâmetros
        params = {
            'model': self.config.model,
            'messages': messages,
            'system': system_prompt,
            'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
            'temperature': kwargs.get('temperature', self.config.temperature),
            'top_p': kwargs.get('top_p', self.config.top_p),
            'top_k': kwargs.get('top_k', self.config.top_k)
        }
        
        start_time = time.time()
        
        try:
            if stream:
                return await self._stream_completion(params)
            else:
                response = await self.client.messages.create(**params)
                
                latency = time.time() - start_time
                
                # Calcula custos
                input_cost = (response.usage.input_tokens / 1000) * self.COST_PER_1K_INPUT
                output_cost = (response.usage.output_tokens / 1000) * self.COST_PER_1K_OUTPUT
                
                return ClaudeResponse(
                    content=response.content[0].text,
                    model=response.model,
                    tokens_input=response.usage.input_tokens,
                    tokens_output=response.usage.output_tokens,
                    latency=latency,
                    cost=input_cost + output_cost,
                    metadata={
                        'stop_reason': response.stop_reason,
                        'id': response.id
                    }
                )
                
        except Exception as e:
            logger.error(f"Claude completion failed: {e}")
            raise
    
    async def _stream_completion(self, params: Dict) -> AsyncGenerator[str, None]:
        """Stream de completion"""
        try:
            async with self.client.messages.stream(**params) as stream:
                async for chunk in stream:
                    if chunk.type == 'content_block_delta':
                        yield chunk.delta.text
        except Exception as e:
            logger.error(f"Claude streaming failed: {e}")
            raise
    
    def _prepare_messages(
        self,
        prompt: str,
        context: List[Dict[str, str]] = None
    ) -> List[Dict[str, str]]:
        """Prepara mensagens para a API"""
        messages = []
        
        # Adiciona contexto se existir
        if context:
            for msg in context:
                messages.append({
                    'role': msg.get('role', 'user'),
                    'content': msg.get('content', '')
                })
        
        # Adiciona prompt atual
        messages.append({
            'role': 'user',
            'content': prompt
        })
        
        return messages
    
    async def analyze(
        self,
        data: Any,
        analysis_type: str = 'general',
        format: str = 'markdown'
    ) -> Dict[str, Any]:
        """Realiza análise especializada"""
        
        analysis_prompts = {
            'general': "Analise os seguintes dados e forneça insights detalhados:",
            'statistical': "Realize análise estatística dos dados, identificando médias, tendências e outliers:",
            'sentiment': "Analise o sentimento e tom emocional do seguinte conteúdo:",
            'comparative': "Compare e contraste os seguintes elementos, destacando diferenças e semelhanças:",
            'swot': "Realize análise SWOT (Forças, Fraquezas, Oportunidades, Ameaças) para:",
            'root_cause': "Identifique as causas raiz e fatores contribuintes para:"
        }
        
        prompt = f"{analysis_prompts.get(analysis_type, analysis_prompts['general'])}\n\n{json.dumps(data, indent=2)}"
        
        if format == 'json':
            prompt += "\n\nFormate a resposta como JSON estruturado."
        elif format == 'bullet_points':
            prompt += "\n\nFormate a resposta em bullet points organizados."
        
        response = await self.complete(
            prompt=prompt,
            system_prompt=self.system_prompts['analysis'],
            temperature=0.5  # Mais determinístico para análise
        )
        
        # Parse se JSON
        if format == 'json':
            try:
                return json.loads(response.content)
            except:
                return {'analysis': response.content}
        
        return {
            'analysis': response.content,
            'tokens_used': response.tokens_input + response.tokens_output,
            'cost': response.cost
        }
    
    async def plan(
        self,
        objective: str,
        constraints: List[str] = None,
        resources: List[str] = None
    ) -> Dict[str, Any]:
        """Cria plano de execução detalhado"""
        
        prompt = f"""Crie um plano detalhado para alcançar o seguinte objetivo:

OBJETIVO: {objective}

RESTRIÇÕES:
{chr(10).join(f'- {c}' for c in (constraints or ['Nenhuma restrição específica']))}

RECURSOS DISPONÍVEIS:
{chr(10).join(f'- {r}' for r in (resources or ['Recursos padrão']))}

Formate o plano com:
1. Visão geral
2. Fases principais
3. Tarefas específicas por fase
4. Dependências entre tarefas
5. Estimativa de tempo
6. Riscos e mitigações
7. Critérios de sucesso
"""
        
        response = await self.complete(
            prompt=prompt,
            system_prompt=self.system_prompts['planning'],
            temperature=0.6,
            max_tokens=2000
        )
        
        return {
            'plan': response.content,
            'tokens_used': response.tokens_input + response.tokens_output,
            'cost': response.cost,
            'model': response.model
        }
    
    async def code(
        self,
        task: str,
        language: str = 'python',
        context: str = None,
        requirements: List[str] = None
    ) -> Dict[str, Any]:
        """Gera código"""
        
        prompt = f"""Escreva código {language} para: {task}

REQUISITOS:
{chr(10).join(f'- {r}' for r in (requirements or ['Código limpo e eficiente']))}

{f'CONTEXTO ADICIONAL: {context}' if context else ''}

Inclua:
- Documentação completa
- Tratamento de erros
- Type hints (se aplicável)
- Testes unitários básicos
"""
        
        response = await self.complete(
            prompt=prompt,
            system_prompt=self.system_prompts['coding'],
            temperature=0.3,  # Mais determinístico para código
            max_tokens=3000
        )
        
        # Extrai código da resposta
        code_blocks = self._extract_code_blocks(response.content)
        
        return {
            'code': code_blocks,
            'explanation': response.content,
            'tokens_used': response.tokens_input + response.tokens_output,
            'cost': response.cost
        }
    
    def _extract_code_blocks(self, text: str) -> List[Dict[str, str]]:
        """Extrai blocos de código da resposta"""
        import re
        
        blocks = []
        pattern = r'```(\w+)?\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        for lang, code in matches:
            blocks.append({
                'language': lang or 'text',
                'code': code.strip()
            })
        
        return blocks
    
    async def reason(
        self,
        problem: str,
        approach: str = 'step_by_step'
    ) -> Dict[str, Any]:
        """Raciocínio complexo sobre problema"""
        
        approaches = {
            'step_by_step': """Resolva este problema passo a passo:
1. Entenda o problema completamente
2. Identifique informações chave
3. Desenvolva uma abordagem
4. Execute cada passo
5. Verifique a solução""",
            
            'first_principles': """Use raciocínio de primeiros princípios:
1. Identifique as suposições fundamentais
2. Questione cada suposição
3. Reconstrua do zero com fatos básicos
4. Derive a solução dos fundamentos""",
            
            'dialectical': """Use raciocínio dialético:
1. Apresente a tese
2. Explore a antítese
3. Sintetize uma solução superior
4. Considere implicações""",
            
            'systems_thinking': """Use pensamento sistêmico:
1. Identifique todos os componentes
2. Mapeie as interações
3. Encontre loops de feedback
4. Considere efeitos de segunda ordem
5. Proponha intervenções"""
        }
        
        prompt = f"{approaches.get(approach, approaches['step_by_step'])}\n\nPROBLEMA: {problem}"
        
        response = await self.complete(
            prompt=prompt,
            temperature=0.7,
            max_tokens=2500
        )
        
        return {
            'reasoning': response.content,
            'approach': approach,
            'tokens_used': response.tokens_input + response.tokens_output,
            'cost': response.cost
        }
    
    async def _check_rate_limit(self):
        """Verifica e aplica rate limiting"""
        current_time = time.time()
        
        # Remove requests antigas
        self.request_times = [
            t for t in self.request_times 
            if current_time - t < 60
        ]
        
        # Verifica limite
        if len(self.request_times) >= self.rate_limit:
            sleep_time = 60 - (current_time - self.request_times[0])
            if sleep_time > 0:
                logger.info(f"Rate limit reached, sleeping {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
        
        self.request_times.append(current_time)
    
    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estima custo da requisição"""
        input_cost = (input_tokens / 1000) * self.COST_PER_1K_INPUT
        output_cost = (output_tokens / 1000) * self.COST_PER_1K_OUTPUT
        return input_cost + output_cost
    
    def get_capabilities(self) -> List[str]:
        """Retorna capacidades do provider"""
        return self.CAPABILITIES
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do provider"""
        try:
            response = await self.complete(
                prompt="Responda apenas 'OK' se está funcionando",
                max_tokens=10
            )
            
            return {
                'status': 'healthy' if 'OK' in response.content else 'degraded',
                'model': self.config.model,
                'latency': response.latency,
                'timestamp': time.time()
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': time.time()
            }

# ============================================================================
# EXEMPLO DE USO
# ============================================================================

async def example_usage():
    """Demonstra uso do Claude Provider"""
    
    # Configuração
    config = ClaudeConfig(
        api_key="sua-api-key-aqui",
        model="claude-3-opus-20240229",
        max_tokens=1000
    )
    
    # Cria provider
    claude = ClaudeProvider(config)
    
    # Testa diferentes capacidades
    print("🧠 Testando Claude Provider\n")
    
    # 1. Completion simples
    print("1. Completion simples:")
    response = await claude.complete(
        prompt="Explique a diferença entre CPU e GPU em 3 frases"
    )
    print(f"Resposta: {response.content}")
    print(f"Tokens: {response.tokens_input} + {response.tokens_output}")
    print(f"Custo: ${response.cost:.4f}\n")
    
    # 2. Análise de dados
    print("2. Análise de dados:")
    analysis = await claude.analyze(
        data={
            'vendas': [100, 150, 120, 180, 200, 190, 220],
            'meses': ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul']
        },
        analysis_type='statistical'
    )
    print(f"Análise: {analysis['analysis'][:200]}...\n")
    
    # 3. Planejamento
    print("3. Planejamento:")
    plan = await claude.plan(
        objective="Criar um site e-commerce em 30 dias",
        constraints=["Orçamento de R$10.000", "Equipe de 2 pessoas"],
        resources=["React", "Node.js", "PostgreSQL"]
    )
    print(f"Plano: {plan['plan'][:300]}...\n")
    
    # 4. Geração de código
    print("4. Geração de código:")
    code = await claude.code(
        task="Função para validar CPF brasileiro",
        language="python",
        requirements=["Deve aceitar com ou sem formatação", "Retornar True/False"]
    )
    if code['code']:
        print(f"Código gerado: {code['code'][0]['code'][:200]}...\n")
    
    # 5. Health check
    print("5. Health check:")
    health = await claude.health_check()
    print(f"Status: {health}\n")

if __name__ == "__main__":
    # Para testar, adicione sua API key
    asyncio.run(example_usage())
