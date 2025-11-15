"""
GEMINI PROVIDER - Integração com Google Gemini
Provider para Google Gemini Pro - custo-efetivo e multimodal
"""

import asyncio
import json
import time
import logging
from typing import Dict, List, Optional, Any, AsyncGenerator, Union
from dataclasses import dataclass
from enum import Enum
import google.generativeai as genai
from PIL import Image
import base64
import io

logger = logging.getLogger(__name__)

@dataclass
class GeminiConfig:
    """Configuração do Gemini"""
    api_key: str
    model: str = "gemini-pro"
    max_output_tokens: int = 4096
    temperature: float = 0.7
    top_p: float = 1.0
    top_k: int = 40
    timeout: int = 30
    max_retries: int = 3
    rate_limit: int = 60  # requests por minuto

@dataclass
class GeminiResponse:
    """Resposta do Gemini"""
    content: str
    model: str
    tokens_input: int
    tokens_output: int
    latency: float
    cost: float
    metadata: Dict[str, Any]

class GeminiProvider:
    """
    Provider para Google Gemini
    Especializado em análise multimodal e custo-efetividade
    """
    
    CAPABILITIES = [
        'text_generation',
        'vision_analysis',
        'multimodal',
        'translation',
        'summarization',
        'question_answering',
        'code_generation',
        'creative_writing',
        'data_analysis'
    ]
    
    # Custos por modelo (por 1K tokens)
    PRICING = {
        'gemini-pro': {'input': 0.00025, 'output': 0.0005},  # Muito mais barato!
        'gemini-pro-vision': {'input': 0.00025, 'output': 0.0005}
    }
    
    def __init__(self, config: GeminiConfig):
        self.config = config
        
        # Configura API
        genai.configure(api_key=config.api_key)
        
        # Modelos disponíveis
        self.text_model = genai.GenerativeModel('gemini-pro')
        self.vision_model = genai.GenerativeModel('gemini-pro-vision')
        
        # Rate limiting
        self.request_times: List[float] = []
        self.rate_limit = config.rate_limit
        
        # Safety settings
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        logger.info(f"✅ Gemini Provider initialized with model {config.model}")
    
    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
        stream: bool = False,
        **kwargs
    ) -> GeminiResponse:
        """Gera completion com Gemini"""
        
        # Rate limiting
        await self._check_rate_limit()
        
        # Prepara prompt com system prompt se houver
        full_prompt = self._prepare_prompt(prompt, system_prompt, context)
        
        # Configurações de geração
        generation_config = genai.types.GenerationConfig(
            candidate_count=1,
            max_output_tokens=kwargs.get('max_output_tokens', self.config.max_output_tokens),
            temperature=kwargs.get('temperature', self.config.temperature),
            top_p=kwargs.get('top_p', self.config.top_p),
            top_k=kwargs.get('top_k', self.config.top_k)
        )
        
        start_time = time.time()
        
        try:
            if stream:
                return await self._stream_completion(full_prompt, generation_config)
            else:
                # Gera resposta
                response = await asyncio.to_thread(
                    self.text_model.generate_content,
                    full_prompt,
                    generation_config=generation_config,
                    safety_settings=self.safety_settings
                )
                
                latency = time.time() - start_time
                
                # Extrai texto da resposta
                text = response.text if hasattr(response, 'text') else str(response)
                
                # Estima tokens (Gemini não retorna contagem exata)
                input_tokens = self._estimate_tokens(full_prompt)
                output_tokens = self._estimate_tokens(text)
                
                # Calcula custos
                pricing = self.PRICING.get(self.config.model, self.PRICING['gemini-pro'])
                input_cost = (input_tokens / 1000) * pricing['input']
                output_cost = (output_tokens / 1000) * pricing['output']
                
                return GeminiResponse(
                    content=text,
                    model=self.config.model,
                    tokens_input=input_tokens,
                    tokens_output=output_tokens,
                    latency=latency,
                    cost=input_cost + output_cost,
                    metadata={
                        'safety_ratings': response.prompt_feedback if hasattr(response, 'prompt_feedback') else None
                    }
                )
                
        except Exception as e:
            logger.error(f"Gemini completion failed: {e}")
            raise
    
    async def _stream_completion(
        self,
        prompt: str,
        generation_config: genai.types.GenerationConfig
    ) -> AsyncGenerator[str, None]:
        """Stream de completion"""
        try:
            response = await asyncio.to_thread(
                self.text_model.generate_content,
                prompt,
                generation_config=generation_config,
                safety_settings=self.safety_settings,
                stream=True
            )
            
            for chunk in response:
                if hasattr(chunk, 'text'):
                    yield chunk.text
                    
        except Exception as e:
            logger.error(f"Gemini streaming failed: {e}")
            raise
    
    def _prepare_prompt(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Prepara prompt completo"""
        
        parts = []
        
        # System prompt
        if system_prompt:
            parts.append(f"Instructions: {system_prompt}\n")
        
        # Context
        if context:
            parts.append("Context:\n")
            for msg in context:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                parts.append(f"{role.capitalize()}: {content}\n")
            parts.append("\n")
        
        # Prompt atual
        parts.append(f"Request: {prompt}")
        
        return "\n".join(parts)
    
    async def analyze_image(
        self,
        image_path: str,
        prompt: str = "Describe this image in detail",
        **kwargs
    ) -> GeminiResponse:
        """Analisa imagem com Gemini Vision"""
        
        # Rate limiting
        await self._check_rate_limit()
        
        start_time = time.time()
        
        try:
            # Carrega imagem
            image = Image.open(image_path)
            
            # Gera resposta
            response = await asyncio.to_thread(
                self.vision_model.generate_content,
                [prompt, image],
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=kwargs.get('max_output_tokens', 1000),
                    temperature=kwargs.get('temperature', 0.5)
                ),
                safety_settings=self.safety_settings
            )
            
            latency = time.time() - start_time
            
            # Extrai texto
            text = response.text if hasattr(response, 'text') else str(response)
            
            # Estima tokens
            input_tokens = self._estimate_tokens(prompt) + 258  # ~258 tokens per image
            output_tokens = self._estimate_tokens(text)
            
            # Calcula custos
            pricing = self.PRICING['gemini-pro-vision']
            cost = ((input_tokens + output_tokens) / 1000) * pricing['output']
            
            return GeminiResponse(
                content=text,
                model='gemini-pro-vision',
                tokens_input=input_tokens,
                tokens_output=output_tokens,
                latency=latency,
                cost=cost,
                metadata={'image_path': image_path}
            )
            
        except Exception as e:
            logger.error(f"Gemini vision analysis failed: {e}")
            raise
    
    async def analyze_multimodal(
        self,
        inputs: List[Union[str, Image.Image, Dict]],
        **kwargs
    ) -> GeminiResponse:
        """Analisa múltiplas modalidades (texto + imagem)"""
        
        # Rate limiting
        await self._check_rate_limit()
        
        start_time = time.time()
        
        try:
            # Processa inputs
            processed_inputs = []
            total_input_tokens = 0
            
            for input_item in inputs:
                if isinstance(input_item, str):
                    processed_inputs.append(input_item)
                    total_input_tokens += self._estimate_tokens(input_item)
                    
                elif isinstance(input_item, Image.Image):
                    processed_inputs.append(input_item)
                    total_input_tokens += 258  # Tokens por imagem
                    
                elif isinstance(input_item, dict):
                    if input_item.get('type') == 'image_path':
                        img = Image.open(input_item['path'])
                        processed_inputs.append(img)
                        total_input_tokens += 258
                    elif input_item.get('type') == 'text':
                        processed_inputs.append(input_item['content'])
                        total_input_tokens += self._estimate_tokens(input_item['content'])
            
            # Gera resposta
            response = await asyncio.to_thread(
                self.vision_model.generate_content,
                processed_inputs,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=kwargs.get('max_output_tokens', 2000),
                    temperature=kwargs.get('temperature', 0.7)
                ),
                safety_settings=self.safety_settings
            )
            
            latency = time.time() - start_time
            
            # Extrai texto
            text = response.text if hasattr(response, 'text') else str(response)
            output_tokens = self._estimate_tokens(text)
            
            # Calcula custos
            pricing = self.PRICING['gemini-pro-vision']
            cost = ((total_input_tokens + output_tokens) / 1000) * pricing['output']
            
            return GeminiResponse(
                content=text,
                model='gemini-pro-vision',
                tokens_input=total_input_tokens,
                tokens_output=output_tokens,
                latency=latency,
                cost=cost,
                metadata={'input_count': len(inputs)}
            )
            
        except Exception as e:
            logger.error(f"Gemini multimodal analysis failed: {e}")
            raise
    
    async def generate_code(
        self,
        task: str,
        language: str = "python",
        context: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Gera código"""
        
        prompt = f"""Generate {language} code for the following task:

Task: {task}

Requirements:
- Write clean, well-commented code
- Include error handling
- Follow best practices for {language}
- Add type hints where applicable

{f'Additional context: {context}' if context else ''}

Please provide the complete code solution:"""
        
        response = await self.complete(prompt, temperature=0.3)
        
        # Extrai código da resposta
        code = self._extract_code(response.content)
        
        return {
            'code': code,
            'explanation': response.content,
            'language': language,
            'tokens_used': response.tokens_input + response.tokens_output,
            'cost': response.cost
        }
    
    def _extract_code(self, text: str) -> str:
        """Extrai código da resposta"""
        import re
        
        # Procura por blocos de código
        code_pattern = r'```(?:\w+)?\n(.*?)```'
        matches = re.findall(code_pattern, text, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # Se não encontrar blocos, retorna texto todo
        return text.strip()
    
    async def summarize(
        self,
        text: str,
        max_length: int = 500,
        style: str = "concise"
    ) -> Dict[str, Any]:
        """Resumo de texto"""
        
        styles = {
            'concise': "Create a concise summary highlighting key points",
            'detailed': "Create a detailed summary preserving important information",
            'bullet': "Create a bullet-point summary of main ideas",
            'executive': "Create an executive summary for business context"
        }
        
        prompt = f"""{styles.get(style, styles['concise'])}:

Text to summarize:
{text}

Maximum length: {max_length} words"""
        
        response = await self.complete(prompt, temperature=0.5)
        
        return {
            'summary': response.content,
            'original_length': len(text.split()),
            'summary_length': len(response.content.split()),
            'compression_ratio': len(response.content) / len(text),
            'tokens_used': response.tokens_input + response.tokens_output,
            'cost': response.cost
        }
    
    async def translate(
        self,
        text: str,
        target_language: str,
        source_language: str = "auto"
    ) -> Dict[str, Any]:
        """Traduz texto"""
        
        prompt = f"""Translate the following text to {target_language}:

{text}

Provide only the translation, maintaining the original tone and style."""
        
        response = await self.complete(prompt, temperature=0.3)
        
        return {
            'original': text,
            'translation': response.content,
            'source_language': source_language,
            'target_language': target_language,
            'tokens_used': response.tokens_input + response.tokens_output,
            'cost': response.cost
        }
    
    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Análise de sentimento"""
        
        prompt = f"""Analyze the sentiment of the following text:

{text}

Provide:
1. Overall sentiment (positive/negative/neutral)
2. Confidence score (0-100)
3. Key emotions detected
4. Brief explanation

Format as JSON."""
        
        response = await self.complete(prompt, temperature=0.3)
        
        # Tenta fazer parse do JSON
        try:
            import json
            result = json.loads(response.content)
        except:
            # Fallback se não for JSON válido
            result = {
                'raw_response': response.content,
                'sentiment': 'unknown'
            }
        
        result.update({
            'tokens_used': response.tokens_input + response.tokens_output,
            'cost': response.cost
        })
        
        return result
    
    def _estimate_tokens(self, text: str) -> int:
        """Estima número de tokens (aproximação)"""
        # Estimativa simples: ~0.75 tokens por palavra
        words = len(text.split())
        return int(words * 0.75)
    
    async def _check_rate_limit(self):
        """Verifica e aplica rate limiting"""
        current_time = time.time()
        
        # Remove requests antigas (> 60 segundos)
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
        pricing = self.PRICING.get(self.config.model, self.PRICING['gemini-pro'])
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        return input_cost + output_cost
    
    def get_capabilities(self) -> List[str]:
        """Retorna capacidades do provider"""
        return self.CAPABILITIES
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do provider"""
        try:
            response = await self.complete(
                prompt="Reply with 'OK' if functioning",
                max_output_tokens=10
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
    """Demonstra uso do Gemini Provider"""
    
    # Configuração
    config = GeminiConfig(
        api_key="sua-api-key-aqui",  # Substitua com sua key
        model="gemini-pro"
    )
    
    # Cria provider
    gemini = GeminiProvider(config)
    
    print("🔷 Testando Gemini Provider\n")
    
    # 1. Completion simples
    print("1. Completion simples:")
    response = await gemini.complete(
        prompt="Explique a diferença entre IA e Machine Learning em 2 frases"
    )
    print(f"Resposta: {response.content}")
    print(f"Custo: ${response.cost:.6f} (muito mais barato!)\n")
    
    # 2. Geração de código
    print("2. Geração de código:")
    code = await gemini.generate_code(
        task="Função para validar email",
        language="python"
    )
    print(f"Código gerado:\n{code['code'][:200]}...\n")
    
    # 3. Resumo
    print("3. Resumo de texto:")
    long_text = """
    Inteligência Artificial é um campo da ciência da computação dedicado a criar 
    sistemas capazes de realizar tarefas que normalmente requerem inteligência humana.
    Isso inclui aprendizado, raciocínio, percepção, compreensão de linguagem natural,
    e até mesmo criatividade. O Machine Learning, por sua vez, é um subconjunto da IA
    que se concentra em algoritmos que podem aprender e melhorar com a experiência,
    sem serem explicitamente programados para cada tarefa específica.
    """
    
    summary = await gemini.summarize(text=long_text, style='bullet')
    print(f"Resumo: {summary['summary']}\n")
    
    # 4. Tradução
    print("4. Tradução:")
    translation = await gemini.translate(
        text="Prometheus is an advanced AI system",
        target_language="Portuguese"
    )
    print(f"Tradução: {translation['translation']}\n")
    
    # 5. Health check
    print("5. Health check:")
    health = await gemini.health_check()
    print(f"Status: {health}\n")
    
    # Mostra economia de custo
    print("💰 COMPARAÇÃO DE CUSTOS:")
    print(f"Gemini: ${response.cost:.6f} por requisição")
    print(f"GPT-4: ~${response.cost * 40:.6f} (40x mais caro)")
    print(f"Claude: ~${response.cost * 30:.6f} (30x mais caro)")

if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())
