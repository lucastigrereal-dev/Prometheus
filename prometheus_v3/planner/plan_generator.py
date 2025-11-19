"""
Plan Generator - Usa IA para gerar planos estruturados
"""

from typing import Dict, List, Any, Optional
import os
import json

class PlanGenerator:
    """Gera planos de ação usando LLM"""

    def __init__(self, openai_api_key: Optional[str] = None):
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')

    def generate_plan(
        self,
        user_request: str,
        knowledge_context: List[Dict[str, Any]],
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Gera um plano estruturado usando IA

        Args:
            user_request: O que o usuário quer fazer
            knowledge_context: Resultados do Knowledge Brain
            additional_context: Contexto adicional

        Returns:
            Plano estruturado
        """
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)

        # Construir prompt
        prompt = self._build_prompt(user_request, knowledge_context, additional_context)

        # Chamar IA
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "Você é um planejador especializado. Analise o pedido do usuário e o conhecimento disponível, então crie um plano de ação estruturado e detalhado."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Mais determinístico
                max_tokens=1500
            )

            plan_text = response.choices[0].message.content

            # Tentar parsear como JSON
            plan = self._parse_plan(plan_text)

            return plan

        except Exception as e:
            print(f"Erro ao gerar plano: {e}")

            # Fallback: plano simples
            return {
                'summary': user_request,
                'steps': [
                    {
                        'order': 1,
                        'action': 'manual',
                        'description': user_request,
                        'params': {}
                    }
                ],
                'estimated_duration': 'unknown',
                'complexity': 'medium',
                'requires_approval': False
            }

    def _build_prompt(
        self,
        user_request: str,
        knowledge_context: List[Dict[str, Any]],
        additional_context: Optional[Dict[str, Any]]
    ) -> str:
        """Constrói o prompt para a IA"""

        # Contexto do conhecimento
        knowledge_text = ""
        if knowledge_context:
            knowledge_text = "CONHECIMENTO PRÉVIO RELEVANTE:\n\n"
            for i, ctx in enumerate(knowledge_context, 1):
                knowledge_text += f"{i}. [Similaridade: {ctx['similarity']:.0%}]\n"
                knowledge_text += f"{ctx['content'][:300]}...\n\n"

        # Ações disponíveis do Executor
        available_actions = """
AÇÕES DISPONÍVEIS NO EXECUTOR LOCAL:
1. list_files - Listar arquivos em um diretório
2. organize_downloads - Organizar Downloads por tipo de arquivo
3. get_system_info - Obter informações do sistema
4. read_file_info - Ler metadados de um arquivo
5. create_directory - Criar um novo diretório

AÇÕES DISPONÍVEIS NO BROWSER EXECUTOR (AUTOMAÇÃO WEB):
1. navigate - Navegar para uma URL
   Parâmetros: {"url": "https://..."}

2. click_element - Clicar em elemento da página
   Parâmetros: {"selector": "button.login", "options": {}}

3. fill_input - Preencher campo de input
   Parâmetros: {"selector": "input#email", "text": "valor"}

4. extract_text - Extrair texto de elemento
   Parâmetros: {"selector": "h1.title"}

5. screenshot - Tirar screenshot da página
   Parâmetros: {"path": "screenshot.png", "full_page": true}

6. wait_for_element - Aguardar elemento aparecer
   Parâmetros: {"selector": "div.content", "timeout": 30000}

7. execute_script - Executar JavaScript na página
   Parâmetros: {"script": "return document.title;"}

8. get_page_info - Obter informações da página
   Parâmetros: {}

NOTA: Para automação web, use ações do Browser Executor.
"""

        prompt = f"""
PEDIDO DO USUÁRIO:
{user_request}

{knowledge_text}

{available_actions}

TAREFA:
Analise o pedido do usuário e o conhecimento prévio disponível. Crie um plano de ação detalhado no formato JSON.

O plano deve ter esta estrutura:
{{
  "summary": "Resumo do que será feito",
  "steps": [
    {{
      "order": 1,
      "action": "nome_da_acao",
      "description": "Descrição clara do passo",
      "params": {{"param1": "value1"}},
      "critical": false
    }}
  ],
  "estimated_duration": "Estimativa de tempo (ex: 2-5 minutos)",
  "complexity": "low|medium|high",
  "requires_approval": false
}}

IMPORTANTE:
- Use APENAS as ações disponíveis acima
- Se precisar de algo que não está disponível, use action: "manual" e explique na descrição
- Marque como critical=true se for ação que mexe em arquivos/sistema
- Seja específico nos parâmetros

Retorne APENAS o JSON, sem explicações adicionais.
"""

        return prompt

    def _parse_plan(self, plan_text: str) -> Dict[str, Any]:
        """Tenta parsear o plano como JSON"""
        try:
            # Limpar markdown se houver
            if "```json" in plan_text:
                plan_text = plan_text.split("```json")[1].split("```")[0]
            elif "```" in plan_text:
                plan_text = plan_text.split("```")[1].split("```")[0]

            plan = json.loads(plan_text.strip())
            return plan

        except Exception as e:
            print(f"Erro ao parsear JSON: {e}")

            # Fallback: plano de texto
            return {
                'summary': 'Plano gerado (formato texto)',
                'steps': [
                    {
                        'order': 1,
                        'action': 'manual',
                        'description': plan_text,
                        'params': {}
                    }
                ],
                'estimated_duration': 'unknown',
                'complexity': 'medium',
                'requires_approval': False
            }
