"""
GPT-4 PROVIDER - Integração com OpenAI GPT-4
Provider especializado em criatividade, código e Aurora (árbitro)
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator, Union
from dataclasses import dataclass
from enum import Enum
import openai
from openai import AsyncOpenAI

logger = logging.getLogger('GPTProvider')

@dataclass
class GPTConfig:
    """Configuração do GPT"""
    api_key: str
    model: str = "gpt-4-turbo-preview"
    max_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout: int = 30
    max_retries: int = 3
    rate_limit: int = 60  # requests por minuto

@dataclass
class GPTResponse:
    """Resposta do GPT"""
    content: str
    model: str
    tokens_input: int
    tokens_output: int
    latency: float
    cost: float
    function_calls: Optional[List[Dict]] = None
    metadata: Dict[str, Any] = None

class GPTProvider:
    """
    Provider para OpenAI GPT-4
    Especializado em criatividade, código e arbitragem (Aurora)
    """
    
    CAPABILITIES = [
        'creativity',
        'code_generation',
        'function_calling',
        'vision',
        'arbitration',
        'translation',
        'summarization',
        'conversation'
    ]
    
    # Custos por modelo
    PRICING = {
        'gpt-4-turbo-preview': {'input': 0.01, 'output': 0.03},
        'gpt-4': {'input': 0.03, 'output': 0.06},
        'gpt-4-vision-preview': {'input': 0.01, 'output': 0.03},
        'gpt-3.5-turbo': {'input': 0.001, 'output': 0.002}
    }
    
    def __init__(self, config: GPTConfig):
        self.config = config
        self.client = AsyncOpenAI(api_key=config.api_key)
        
        # Rate limiting
        self.request_times: List[float] = []
        self.rate_limit = config.rate_limit
        
        # Aurora mode para arbitragem
        self.aurora_mode = False
        
        # Functions disponíveis
        self.functions = self._load_functions()
        
        logger.info(f"✅ GPT Provider initialized with model {config.model}")
    
    def _load_functions(self) -> List[Dict]:
        """Carrega definições de funções para function calling"""
        return [
            {
                "name": "execute_code",
                "description": "Executa código Python e retorna resultado",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "code": {
                            "type": "string",
                            "description": "Código Python para executar"
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Timeout em segundos",
                            "default": 10
                        }
                    },
                    "required": ["code"]
                }
            },
            {
                "name": "search_web",
                "description": "Busca informações na web",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Query de busca"
                        },
                        "num_results": {
                            "type": "integer",
                            "description": "Número de resultados",
                            "default": 5
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "create_file",
                "description": "Cria arquivo com conteúdo",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "filename": {
                            "type": "string",
                            "description": "Nome do arquivo"
                        },
                        "content": {
                            "type": "string",
                            "description": "Conteúdo do arquivo"
                        },
                        "file_type": {
                            "type": "string",
                            "description": "Tipo do arquivo",
                            "enum": ["text", "json", "python", "javascript", "html", "css"]
                        }
                    },
                    "required": ["filename", "content"]
                }
            }
        ]
    
    def enable_aurora_mode(self):
        """Ativa modo Aurora para arbitragem"""
        self.aurora_mode = True
        logger.info("🌟 Aurora mode activated - GPT as arbiter")
    
    async def complete(
        self,
        prompt: str,
        system_prompt: str = None,
        context: List[Dict[str, str]] = None,
        stream: bool = False,
        functions_enabled: bool = False,
        **kwargs
    ) -> GPTResponse:
        """Gera completion com GPT"""
        
        # Rate limiting
        await self._check_rate_limit()
        
        # Prepara mensagens
        messages = self._prepare_messages(prompt, system_prompt, context)
        
        # Parâmetros
        params = {
            'model': self.config.model,
            'messages': messages,
            'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
            'temperature': kwargs.get('temperature', self.config.temperature),
            'top_p': kwargs.get('top_p', self.config.top_p),
            'frequency_penalty': kwargs.get('frequency_penalty', self.config.frequency_penalty),
            'presence_penalty': kwargs.get('presence_penalty', self.config.presence_penalty)
        }
        
        # Adiciona functions se habilitado
        if functions_enabled and self.functions:
            params['functions'] = self.functions
            params['function_call'] = 'auto'
        
        start_time = time.time()
        
        try:
            if stream:
                return await self._stream_completion(params)
            else:
                response = await self.client.chat.completions.create(**params)
                
                latency = time.time() - start_time
                
                # Extrai resposta
                message = response.choices[0].message
                content = message.content or ""
                
                # Verifica function calls
                function_calls = None
                if hasattr(message, 'function_call') and message.function_call:
                    function_calls = [{
                        'name': message.function_call.name,
                        'arguments': json.loads(message.function_call.arguments)
                    }]
                
                # Calcula custos
                pricing = self.PRICING.get(self.config.model, self.PRICING['gpt-4'])
                input_cost = (response.usage.prompt_tokens / 1000) * pricing['input']
                output_cost = (response.usage.completion_tokens / 1000) * pricing['output']
                
                return GPTResponse(
                    content=content,
                    model=response.model,
                    tokens_input=response.usage.prompt_tokens,
                    tokens_output=response.usage.completion_tokens,
                    latency=latency,
                    cost=input_cost + output_cost,
                    function_calls=function_calls,
                    metadata={
                        'finish_reason': response.choices[0].finish_reason,
                        'id': response.id
                    }
                )
                
        except Exception as e:
            logger.error(f"GPT completion failed: {e}")
            raise
    
    async def _stream_completion(self, params: Dict) -> AsyncGenerator[str, None]:
        """Stream de completion"""
        try:
            stream = await self.client.chat.completions.create(**params, stream=True)
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"GPT streaming failed: {e}")
            raise
    
    def _prepare_messages(
        self,
        prompt: str,
        system_prompt: str = None,
        context: List[Dict[str, str]] = None
    ) -> List[Dict[str, str]]:
        """Prepara mensagens para a API"""
        messages = []
        
        # System prompt
        if self.aurora_mode:
            system_prompt = """Você é Aurora, o árbitro supremo de decisões.
Sua função é analisar múltiplas perspectivas e decidir o melhor caminho.
Seja justo, lógico e considere todos os aspectos antes de decidir.
Explique seu raciocínio de forma clara."""
        elif not system_prompt:
            system_prompt = """Você é um assistente IA avançado, criativo e capaz.
Especializado em gerar soluções inovadoras e código de alta qualidade."""
        
        messages.append({'role': 'system', 'content': system_prompt})
        
        # Contexto
        if context:
            for msg in context:
                messages.append({
                    'role': msg.get('role', 'user'),
                    'content': msg.get('content', '')
                })
        
        # Prompt atual
        messages.append({'role': 'user', 'content': prompt})
        
        return messages
    
    async def arbitrate(
        self,
        options: List[Dict[str, Any]],
        criteria: List[str] = None,
        context: str = None
    ) -> Dict[str, Any]:
        """Aurora: Arbitra entre múltiplas opções"""
        
        self.enable_aurora_mode()
        
        # Formata opções para análise
        options_text = "\n\n".join([
            f"OPÇÃO {i+1} ({opt.get('source', 'Unknown')}):\n{opt.get('content', '')}"
            for i, opt in enumerate(options)
        ])
        
        criteria_text = "\n".join([f"- {c}" for c in (criteria or [
            "Precisão técnica",
            "Clareza de comunicação",
            "Completude da resposta",
            "Aplicabilidade prática"
        ])])
        
        prompt = f"""Como Aurora, analise as seguintes opções e decida qual é a melhor:

{options_text}

CRITÉRIOS DE AVALIAÇÃO:
{criteria_text}

{f'CONTEXTO ADICIONAL: {context}' if context else ''}

Forneça:
1. Análise de cada opção (prós e contras)
2. Decisão final com justificativa
3. Síntese combinando o melhor de cada opção (se aplicável)
4. Score de confiança (0-100) para sua decisão
"""
        
        response = await self.complete(
            prompt=prompt,
            temperature=0.5  # Mais determinístico para arbitragem
        )
        
        # Parse resposta
        return {
            'decision': response.content,
            'chosen_option': self._extract_chosen_option(response.content, len(options)),
            'confidence': self._extract_confidence(response.content),
            'synthesis': self._extract_synthesis(response.content),
            'tokens_used': response.tokens_input + response.tokens_output,
            'cost': response.cost
        }
    
    def _extract_chosen_option(self, text: str, num_options: int) -> int:
        """Extrai opção escolhida do texto"""
        import re
        
        # Procura padrões como "Opção 1", "OPÇÃO 2", etc
        pattern = r'(?:opção|escolho|decido pela?|melhor é a?)\s*(\d+)'
        matches = re.findall(pattern, text.lower())
        
        if matches:
            option = int(matches[0])
            if 1 <= option <= num_options:
                return option - 1  # Zero-indexed
        
        return 0  # Default primeira opção
    
    def _extract_confidence(self, text: str) -> float:
        """Extrai score de confiança"""
        import re
        
        # Procura padrões de porcentagem ou score
        patterns = [
            r'confiança[:\s]+(\d+)%?',
            r'score[:\s]+(\d+)',
            r'(\d+)%?\s*(?:de confiança|confiante)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                score = float(matches[0])
                return min(100, max(0, score))
        
        return 75.0  # Default
    
    def _extract_synthesis(self, text: str) -> Optional[str]:
        """Extrai síntese da resposta"""
        import re
        
        # Procura seção de síntese
        pattern = r'(?:síntese|combinando|melhor de cada)[:\s]+(.*?)(?:\n\n|\Z)'
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        
        if match:
            return match.group(1).strip()
        
        return None
    
    async def generate_code(
        self,
        task: str,
        language: str = 'python',
        framework: str = None,
        style_guide: str = None,
        include_tests: bool = True
    ) -> Dict[str, Any]:
        """Gera código otimizado"""
        
        prompt = f"""Gere código {language} {'usando ' + framework if framework else ''} para:

TAREFA: {task}

REQUISITOS:
- Código limpo e bem estruturado
- Documentação completa (docstrings)
- Type hints (quando aplicável)
- Tratamento de erros robusto
- Padrões de design apropriados
{f'- Seguir style guide: {style_guide}' if style_guide else ''}
{f'- Incluir testes unitários' if include_tests else ''}

Organize o código em:
1. Imports
2. Constantes/Configuração
3. Classes/Funções principais
4. Funções auxiliares
5. Exemplo de uso
{f'6. Testes' if include_tests else ''}
"""
        
        response = await self.complete(
            prompt=prompt,
            temperature=0.3,  # Mais determinístico para código
            max_tokens=3000
        )
        
        # Extrai blocos de código
        code_blocks = self._extract_code_blocks(response.content)
        
        # Separa código principal e testes
        main_code = []
        test_code = []
        
        for block in code_blocks:
            if 'test' in block.get('filename', '').lower():
                test_code.append(block)
            else:
                main_code.append(block)
        
        return {
            'main_code': main_code,
            'test_code': test_code if include_tests else [],
            'documentation': self._extract_documentation(response.content),
            'tokens_used': response.tokens_input + response.tokens_output,
            'cost': response.cost
        }
    
    def _extract_code_blocks(self, text: str) -> List[Dict[str, str]]:
        """Extrai blocos de código"""
        import re
        
        blocks = []
        
        # Pattern para código com linguagem
        pattern = r'```(\w+)\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        for i, (lang, code) in enumerate(matches):
            # Tenta extrair filename de comentários
            filename = None
            first_line = code.split('\n')[0]
            if '#' in first_line or '//' in first_line:
                filename_match = re.search(r'(?:filename:|file:)\s*(\S+)', first_line)
                if filename_match:
                    filename = filename_match.group(1)
            
            blocks.append({
                'language': lang,
                'code': code.strip(),
                'filename': filename or f"code_{i}.{self._get_extension(lang)}"
            })
        
        return blocks
    
    def _get_extension(self, language: str) -> str:
        """Retorna extensão para linguagem"""
        extensions = {
            'python': 'py',
            'javascript': 'js',
            'typescript': 'ts',
            'java': 'java',
            'cpp': 'cpp',
            'c': 'c',
            'html': 'html',
            'css': 'css',
            'sql': 'sql',
            'bash': 'sh'
        }
        return extensions.get(language.lower(), 'txt')
    
    def _extract_documentation(self, text: str) -> str:
        """Extrai documentação do código"""
        import re
        
        # Remove blocos de código
        text_without_code = re.sub(r'```[\s\S]*?```', '', text)
        
        # Procura seções de documentação
        doc_sections = []
        
        patterns = [
            r'(?:documentação|documentation)[:\s]+(.*?)(?:\n\n|\Z)',
            r'(?:descrição|description)[:\s]+(.*?)(?:\n\n|\Z)',
            r'(?:como usar|usage)[:\s]+(.*?)(?:\n\n|\Z)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text_without_code, re.IGNORECASE | re.DOTALL)
            doc_sections.extend(matches)
        
        return '\n\n'.join(doc_sections) if doc_sections else text_without_code
    
    async def create_content(
        self,
        content_type: str,
        topic: str,
        tone: str = 'professional',
        length: str = 'medium',
        audience: str = 'general'
    ) -> Dict[str, Any]:
        """Cria conteúdo criativo"""
        
        content_prompts = {
            'article': f"Escreva um artigo {tone} sobre {topic}",
            'story': f"Crie uma história {tone} sobre {topic}",
            'script': f"Escreva um script {tone} sobre {topic}",
            'presentation': f"Crie uma apresentação {tone} sobre {topic}",
            'email': f"Escreva um email {tone} sobre {topic}",
            'social_media': f"Crie posts para redes sociais sobre {topic}"
        }
        
        length_guides = {
            'short': '200-300 palavras',
            'medium': '500-700 palavras',
            'long': '1000-1500 palavras'
        }
        
        prompt = f"""{content_prompts.get(content_type, f'Crie conteúdo sobre {topic}')}

ESPECIFICAÇÕES:
- Tom: {tone}
- Tamanho: {length_guides.get(length, '500 palavras')}
- Público: {audience}

Estruture o conteúdo com:
- Título impactante
- Introdução envolvente
- Desenvolvimento claro
- Conclusão memorável
"""
        
        response = await self.complete(
            prompt=prompt,
            temperature=0.8  # Mais criativo
        )
        
        return {
            'content': response.content,
            'word_count': len(response.content.split()),
            'tokens_used': response.tokens_input + response.tokens_output,
            'cost': response.cost
        }
    
    async def analyze_image(
        self,
        image_path: str,
        questions: List[str] = None
    ) -> Dict[str, Any]:
        """Analisa imagem com GPT-4 Vision"""
        
        if 'vision' not in self.config.model:
            logger.warning("Model doesn't support vision, switching to gpt-4-vision-preview")
            self.config.model = 'gpt-4-vision-preview'
        
        # Codifica imagem
        import base64
        
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        default_questions = [
            "O que você vê nesta imagem?",
            "Descreva os elementos principais",
            "Qual o contexto ou cenário?",
            "Há texto visível? Se sim, transcreva"
        ]
        
        questions = questions or default_questions
        questions_text = "\n".join([f"{i+1}. {q}" for i, q in enumerate(questions)])
        
        prompt = f"""Analise esta imagem e responda:

{questions_text}

Seja detalhado e preciso em suas observações."""
        
        messages = [
            {
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': prompt},
                    {
                        'type': 'image_url',
                        'image_url': {
                            'url': f"data:image/jpeg;base64,{image_data}"
                        }
                    }
                ]
            }
        ]
        
        response = await self.client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            max_tokens=1000
        )
        
        return {
            'analysis': response.choices[0].message.content,
            'model': response.model,
            'tokens_used': response.usage.total_tokens
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
        pricing = self.PRICING.get(self.config.model, self.PRICING['gpt-4'])
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        return input_cost + output_cost
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do provider"""
        try:
            response = await self.complete(
                prompt="Reply with 'OK' if functioning",
                max_tokens=10
            )
            
            return {
                'status': 'healthy' if 'OK' in response.content else 'degraded',
                'model': self.config.model,
                'latency': response.latency,
                'aurora_mode': self.aurora_mode,
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
    """Demonstra uso do GPT Provider"""
    
    # Configuração
    config = GPTConfig(
        api_key="sua-api-key-aqui",
        model="gpt-4-turbo-preview"
    )
    
    # Cria provider
    gpt = GPTProvider(config)
    
    print("🤖 Testando GPT Provider\n")
    
    # 1. Completion simples
    print("1. Completion simples:")
    response = await gpt.complete(
        prompt="Crie um haiku sobre programação"
    )
    print(f"Resposta: {response.content}\n")
    
    # 2. Geração de código
    print("2. Geração de código:")
    code = await gpt.generate_code(
        task="API REST para gerenciar tarefas",
        language="python",
        framework="FastAPI",
        include_tests=True
    )
    if code['main_code']:
        print(f"Código gerado: {code['main_code'][0]['code'][:300]}...\n")
    
    # 3. Aurora - Arbitragem
    print("3. Aurora Arbitragem:")
    options = [
        {'source': 'Claude', 'content': 'Use arquitetura em camadas para escalabilidade'},
        {'source': 'Gemini', 'content': 'Use microserviços para flexibilidade'},
        {'source': 'GPT-3.5', 'content': 'Use monolito para simplicidade'}
    ]
    
    decision = await gpt.arbitrate(
        options=options,
        criteria=['Escalabilidade', 'Manutenibilidade', 'Custo'],
        context='Startup com 3 desenvolvedores'
    )
    print(f"Decisão: {decision['decision'][:300]}...")
    print(f"Opção escolhida: {decision['chosen_option'] + 1}")
    print(f"Confiança: {decision['confidence']}%\n")
    
    # 4. Criação de conteúdo
    print("4. Criação de conteúdo:")
    content = await gpt.create_content(
        content_type='article',
        topic='Inteligência Artificial no Marketing',
        tone='persuasivo',
        length='short',
        audience='empresários'
    )
    print(f"Conteúdo: {content['content'][:300]}...\n")

if __name__ == "__main__":
    asyncio.run(example_usage())
