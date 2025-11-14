"""
PROMETHEUS AI MASTER ROUTER
Sistema inteligente que roteia prompts para o melhor modelo de IA
Suporta Claude (Anthropic), GPT (OpenAI) e Gemini (Google)
"""

import os
import re
import logging
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

# AI SDKs
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TaskType(Enum):
    """Tipos de tarefas para roteamento"""
    CODE = "code"              # Programação, debug, code review
    CREATIVE = "creative"      # Escrita criativa, storytelling
    ANALYSIS = "analysis"      # Análise de dados, raciocínio lógico
    SEARCH = "search"          # Pesquisa, fatos, informações atuais
    GENERAL = "general"        # Conversação geral
    TECHNICAL = "technical"    # Documentação técnica, explicações
    MATH = "math"             # Matemática, cálculos


class AIModel(Enum):
    """Modelos de IA disponíveis"""
    CLAUDE_SONNET = "claude-3-5-sonnet-20241022"
    CLAUDE_OPUS = "claude-3-opus-20240229"
    CLAUDE_HAIKU = "claude-3-haiku-20240307"
    GPT4_TURBO = "gpt-4-turbo-preview"
    GPT4 = "gpt-4"
    GPT35_TURBO = "gpt-3.5-turbo"
    GEMINI_PRO = "gemini-1.5-pro"
    GEMINI_FLASH = "gemini-1.5-flash"


@dataclass
class ModelCapabilities:
    """Capacidades de cada modelo"""
    name: str
    strength: List[TaskType]
    max_tokens: int
    cost_per_1k: float  # Custo aproximado por 1K tokens
    speed: str  # fast, medium, slow


# Mapeamento de capacidades
MODEL_CAPABILITIES = {
    AIModel.CLAUDE_SONNET: ModelCapabilities(
        name="Claude 3.5 Sonnet",
        strength=[TaskType.CODE, TaskType.ANALYSIS, TaskType.TECHNICAL],
        max_tokens=4096,
        cost_per_1k=0.003,
        speed="medium"
    ),
    AIModel.GPT4_TURBO: ModelCapabilities(
        name="GPT-4 Turbo",
        strength=[TaskType.GENERAL, TaskType.CREATIVE, TaskType.ANALYSIS],
        max_tokens=4096,
        cost_per_1k=0.01,
        speed="medium"
    ),
    AIModel.GEMINI_PRO: ModelCapabilities(
        name="Gemini 1.5 Pro",
        strength=[TaskType.SEARCH, TaskType.GENERAL, TaskType.MATH],
        max_tokens=8192,
        cost_per_1k=0.00125,
        speed="fast"
    ),
    AIModel.GPT35_TURBO: ModelCapabilities(
        name="GPT-3.5 Turbo",
        strength=[TaskType.GENERAL, TaskType.CREATIVE],
        max_tokens=4096,
        cost_per_1k=0.0005,
        speed="fast"
    ),
    AIModel.GEMINI_FLASH: ModelCapabilities(
        name="Gemini 1.5 Flash",
        strength=[TaskType.GENERAL, TaskType.SEARCH],
        max_tokens=8192,
        cost_per_1k=0.00025,
        speed="fast"
    )
}


class AIRouter:
    """
    Sistema de roteamento inteligente para múltiplas IAs
    """

    def __init__(self):
        """Inicializa o roteador de IA"""
        self.anthropic_client = None
        self.openai_client = None
        self.gemini_model = None

        # Configurar Anthropic (Claude)
        if ANTHROPIC_AVAILABLE:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if api_key:
                try:
                    self.anthropic_client = anthropic.Anthropic(api_key=api_key)
                    logger.info("Claude (Anthropic) configurado")
                except Exception as e:
                    logger.error(f"Erro ao configurar Claude: {e}")

        # Configurar OpenAI (GPT)
        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                try:
                    self.openai_client = openai.OpenAI(api_key=api_key)
                    logger.info("GPT (OpenAI) configurado")
                except Exception as e:
                    logger.error(f"Erro ao configurar GPT: {e}")

        # Configurar Google (Gemini)
        if GOOGLE_AVAILABLE:
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key:
                try:
                    genai.configure(api_key=api_key)
                    self.gemini_model = genai.GenerativeModel('gemini-1.5-pro')
                    logger.info("Gemini (Google) configurado")
                except Exception as e:
                    logger.error(f"Erro ao configurar Gemini: {e}")

        logger.info("AIRouter inicializado")

    def detect_task_type(self, prompt: str) -> TaskType:
        """
        Detecta o tipo de tarefa baseado no prompt

        Args:
            prompt: Texto do usuário

        Returns:
            Tipo de tarefa detectado
        """
        prompt_lower = prompt.lower()

        # Palavras-chave por tipo
        keywords = {
            TaskType.CODE: [
                "codigo", "code", "programar", "program", "bug", "debug",
                "function", "funcao", "classe", "class", "script", "python",
                "javascript", "java", "c++", "rust", "go", "typescript",
                "implementar", "implement", "refatorar", "refactor"
            ],
            TaskType.CREATIVE: [
                "escrever", "write", "historia", "story", "poema", "poem",
                "criativo", "creative", "narrativa", "narrative", "conto",
                "roteiro", "script", "artigo", "article", "blog"
            ],
            TaskType.ANALYSIS: [
                "analisar", "analyze", "analise", "analysis", "comparar",
                "compare", "avaliar", "evaluate", "dados", "data",
                "estatistica", "statistics", "tendencia", "trend"
            ],
            TaskType.SEARCH: [
                "buscar", "search", "pesquisar", "procurar", "find",
                "informacao", "information", "quando", "when", "onde", "where",
                "quem", "who", "o que", "what"
            ],
            TaskType.MATH: [
                "calcular", "calculate", "matematica", "math", "equacao",
                "equation", "resolver", "solve", "integral", "derivada",
                "algebra", "geometria", "trigonometria"
            ],
            TaskType.TECHNICAL: [
                "explicar", "explain", "como funciona", "how works",
                "documentacao", "documentation", "tutorial", "guia",
                "passo a passo", "step by step"
            ]
        }

        # Contar matches por tipo
        scores = {}
        for task_type, words in keywords.items():
            score = sum(1 for word in words if word in prompt_lower)
            scores[task_type] = score

        # Retornar tipo com maior score
        if scores:
            max_score = max(scores.values())
            if max_score > 0:
                return max(scores, key=scores.get)

        return TaskType.GENERAL

    def select_best_model(self, task_type: TaskType, prefer_fast: bool = False) -> AIModel:
        """
        Seleciona o melhor modelo para a tarefa

        Args:
            task_type: Tipo de tarefa
            prefer_fast: Se True, prefere modelos mais rápidos

        Returns:
            Modelo selecionado
        """
        # Modelos ideais por tipo de tarefa
        best_models = {
            TaskType.CODE: AIModel.CLAUDE_SONNET,
            TaskType.CREATIVE: AIModel.GPT4_TURBO,
            TaskType.ANALYSIS: AIModel.CLAUDE_SONNET,
            TaskType.SEARCH: AIModel.GEMINI_PRO,
            TaskType.GENERAL: AIModel.GPT35_TURBO if prefer_fast else AIModel.GPT4_TURBO,
            TaskType.TECHNICAL: AIModel.CLAUDE_SONNET,
            TaskType.MATH: AIModel.GEMINI_PRO
        }

        preferred = best_models.get(task_type, AIModel.GPT35_TURBO)

        # Verificar disponibilidade
        if preferred in [AIModel.CLAUDE_SONNET, AIModel.CLAUDE_OPUS, AIModel.CLAUDE_HAIKU]:
            if self.anthropic_client:
                return preferred
            elif self.openai_client:
                return AIModel.GPT4_TURBO
            elif self.gemini_model:
                return AIModel.GEMINI_PRO

        elif preferred in [AIModel.GPT4_TURBO, AIModel.GPT4, AIModel.GPT35_TURBO]:
            if self.openai_client:
                return preferred
            elif self.anthropic_client:
                return AIModel.CLAUDE_SONNET
            elif self.gemini_model:
                return AIModel.GEMINI_PRO

        elif preferred in [AIModel.GEMINI_PRO, AIModel.GEMINI_FLASH]:
            if self.gemini_model:
                return preferred
            elif self.anthropic_client:
                return AIModel.CLAUDE_SONNET
            elif self.openai_client:
                return AIModel.GPT4_TURBO

        # Fallback
        return AIModel.GPT35_TURBO

    def query_claude(self, prompt: str, model: AIModel, max_tokens: int = 4096) -> Dict[str, Any]:
        """Consulta Claude (Anthropic)"""
        try:
            if not self.anthropic_client:
                return {"success": False, "error": "Claude não configurado"}

            message = self.anthropic_client.messages.create(
                model=model.value,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = message.content[0].text

            return {
                "success": True,
                "response": response_text,
                "model": model.value,
                "provider": "Anthropic (Claude)"
            }

        except Exception as e:
            logger.error(f"Erro ao consultar Claude: {e}")
            return {"success": False, "error": str(e)}

    def query_gpt(self, prompt: str, model: AIModel, max_tokens: int = 4096) -> Dict[str, Any]:
        """Consulta GPT (OpenAI)"""
        try:
            if not self.openai_client:
                return {"success": False, "error": "GPT não configurado"}

            response = self.openai_client.chat.completions.create(
                model=model.value,
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            response_text = response.choices[0].message.content

            return {
                "success": True,
                "response": response_text,
                "model": model.value,
                "provider": "OpenAI (GPT)"
            }

        except Exception as e:
            logger.error(f"Erro ao consultar GPT: {e}")
            return {"success": False, "error": str(e)}

    def query_gemini(self, prompt: str, model: AIModel) -> Dict[str, Any]:
        """Consulta Gemini (Google)"""
        try:
            if not self.gemini_model:
                return {"success": False, "error": "Gemini não configurado"}

            response = self.gemini_model.generate_content(prompt)
            response_text = response.text

            return {
                "success": True,
                "response": response_text,
                "model": model.value,
                "provider": "Google (Gemini)"
            }

        except Exception as e:
            logger.error(f"Erro ao consultar Gemini: {e}")
            return {"success": False, "error": str(e)}

    def route_query(
        self,
        prompt: str,
        task_type: Optional[TaskType] = None,
        prefer_fast: bool = False,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Roteia query para o melhor modelo

        Args:
            prompt: Prompt do usuário
            task_type: Tipo de tarefa (detecta automaticamente se None)
            prefer_fast: Se True, prefere modelos rápidos
            max_tokens: Tokens máximos na resposta

        Returns:
            Resposta do modelo
        """
        try:
            # Detectar tipo se não fornecido
            if not task_type:
                task_type = self.detect_task_type(prompt)
                logger.info(f"Tipo de tarefa detectado: {task_type.value}")

            # Selecionar melhor modelo
            best_model = self.select_best_model(task_type, prefer_fast)
            logger.info(f"Modelo selecionado: {best_model.value}")

            # Rotear para o modelo apropriado
            if best_model in [AIModel.CLAUDE_SONNET, AIModel.CLAUDE_OPUS, AIModel.CLAUDE_HAIKU]:
                result = self.query_claude(prompt, best_model, max_tokens)

            elif best_model in [AIModel.GPT4_TURBO, AIModel.GPT4, AIModel.GPT35_TURBO]:
                result = self.query_gpt(prompt, best_model, max_tokens)

            elif best_model in [AIModel.GEMINI_PRO, AIModel.GEMINI_FLASH]:
                result = self.query_gemini(prompt, best_model)

            else:
                return {"success": False, "error": "Nenhum modelo disponível"}

            # Adicionar metadados
            if result.get("success"):
                result["task_type"] = task_type.value
                result["prompt_length"] = len(prompt)
                result["response_length"] = len(result.get("response", ""))

            return result

        except Exception as e:
            logger.error(f"Erro ao rotear query: {e}")
            return {"success": False, "error": str(e)}


class PrometheusAIInterface:
    """
    Interface simplificada para integração com Prometheus Brain
    """

    def __init__(self):
        """Inicializa interface de IA"""
        self.router = AIRouter()
        logger.info("PrometheusAIInterface inicializada")

    def process_command(self, command: str) -> Dict[str, Any]:
        """
        Processa comando de IA em linguagem natural

        Args:
            command: Comando do usuário

        Returns:
            Resposta da IA
        """
        try:
            # Remover prefixos comuns
            command = re.sub(r'^(perguntar|ai|ia|claude|gpt|gemini)\s+', '', command, flags=re.IGNORECASE)

            # Detectar preferências no comando
            prefer_fast = any(word in command.lower() for word in ["rapido", "fast", "quick"])

            # Rotear para melhor modelo
            result = self.router.route_query(command, prefer_fast=prefer_fast)

            return result

        except Exception as e:
            logger.error(f"Erro ao processar comando: {e}")
            return {"success": False, "error": str(e)}


# Teste básico
if __name__ == "__main__":
    print("🤖 Testando AI Master Router...\n")

    # Verificar SDKs disponíveis
    print("SDKs disponíveis:")
    print(f"  Anthropic (Claude): {ANTHROPIC_AVAILABLE}")
    print(f"  OpenAI (GPT): {OPENAI_AVAILABLE}")
    print(f"  Google (Gemini): {GOOGLE_AVAILABLE}")
    print()

    if not any([ANTHROPIC_AVAILABLE, OPENAI_AVAILABLE, GOOGLE_AVAILABLE]):
        print("❌ Nenhum SDK de IA instalado!")
        print("Instale com:")
        print("  pip install anthropic openai google-generativeai")
    else:
        interface = PrometheusAIInterface()

        # Teste 1: Detectar tipo de tarefa
        print("📝 Teste 1: Detectar tipo de tarefa")
        prompts = [
            "Escreva uma função Python que calcula fibonacci",
            "Conte uma história sobre um robô",
            "Analise os dados de vendas do último trimestre",
            "Quem foi Albert Einstein?"
        ]

        for prompt in prompts:
            task_type = interface.router.detect_task_type(prompt)
            model = interface.router.select_best_model(task_type)
            print(f"  '{prompt[:50]}...'")
            print(f"    → Tipo: {task_type.value}")
            print(f"    → Modelo: {model.value}")
            print()

        print("✅ Testes de detecção concluídos!")
