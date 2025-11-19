"""
Code Reviewer - Revisa código usando IA
PRINCÍPIOS:
- Detecta bugs, vulnerabilidades e code smells
- Sugere melhorias
- Verifica boas práticas
- Sempre com explicação clara
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import os
import json

class CodeReviewer:
    """Revisor de código com IA"""

    REVIEW_ASPECTS = [
        'security',        # Vulnerabilidades de segurança
        'bugs',           # Bugs potenciais
        'performance',    # Problemas de performance
        'maintainability', # Manutenibilidade
        'best_practices'  # Boas práticas
    ]

    SEVERITY_LEVELS = ['critical', 'high', 'medium', 'low', 'info']

    def __init__(self, openai_api_key: Optional[str] = None):
        """
        Inicializa CodeReviewer

        Args:
            openai_api_key: API key da OpenAI (opcional, usa env se não fornecida)
        """
        self.api_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        self.review_history = []

    def review_code(
        self,
        code: str,
        language: str = "python",
        context: Optional[Dict[str, Any]] = None,
        aspects: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Revisa código usando IA

        Args:
            code: Código a ser revisado
            language: Linguagem do código (python, javascript, etc)
            context: Contexto adicional (descrição, propósito, etc)
            aspects: Aspectos específicos a revisar (security, bugs, etc)

        Returns:
            Dict com resultado da revisão:
            {
                'review_id': str,
                'timestamp': str,
                'language': str,
                'overall_score': int (0-100),
                'issues': List[Dict],
                'suggestions': List[Dict],
                'summary': str,
                'approved': bool
            }
        """
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)

        # Aspectos a revisar (usa todos se não especificado)
        review_aspects = aspects or self.REVIEW_ASPECTS

        # Construir prompt
        prompt = self._build_review_prompt(code, language, context, review_aspects)

        # Chamar IA
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """Você é um revisor de código experiente.
Analise o código fornecido e identifique:
- Vulnerabilidades de segurança (SQL injection, XSS, etc)
- Bugs potenciais
- Problemas de performance
- Violações de boas práticas
- Sugestões de melhoria

Retorne sempre em formato JSON estruturado."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,  # Mais determinístico para revisões
                max_tokens=2000
            )

            review_text = response.choices[0].message.content

            # Parsear resultado
            review_result = self._parse_review(review_text, code, language)

            # Salvar no histórico
            self.review_history.append(review_result)

            return review_result

        except Exception as e:
            print(f"Erro ao revisar código: {e}")

            # Fallback: revisão básica
            return self._basic_review(code, language)

    def _build_review_prompt(
        self,
        code: str,
        language: str,
        context: Optional[Dict[str, Any]],
        aspects: List[str]
    ) -> str:
        """Constrói o prompt para revisão"""

        context_text = ""
        if context:
            context_text = f"""
CONTEXTO:
Descrição: {context.get('description', 'N/A')}
Propósito: {context.get('purpose', 'N/A')}
"""

        aspects_text = "\n".join([f"- {aspect}" for aspect in aspects])

        prompt = f"""
CÓDIGO A REVISAR ({language.upper()}):
```{language}
{code}
```

{context_text}

ASPECTOS A REVISAR:
{aspects_text}

TAREFA:
Analise o código acima e retorne um JSON com esta estrutura:

{{
  "overall_score": <número de 0 a 100>,
  "issues": [
    {{
      "severity": "critical|high|medium|low|info",
      "type": "security|bug|performance|maintainability|best_practice",
      "line": <número da linha ou null>,
      "message": "Descrição clara do problema",
      "suggestion": "Como corrigir"
    }}
  ],
  "suggestions": [
    {{
      "priority": "high|medium|low",
      "message": "Sugestão de melhoria",
      "example": "Código exemplo se aplicável"
    }}
  ],
  "summary": "Resumo geral da revisão",
  "approved": true/false
}}

IMPORTANTE:
- Seja específico e construtivo
- Indique a linha quando possível
- Priorize issues de segurança
- Use approved=false se houver issues críticos
- Se o código estiver bom, retorne issues vazio

Retorne APENAS o JSON, sem explicações adicionais.
"""

        return prompt

    def _parse_review(self, review_text: str, code: str, language: str) -> Dict[str, Any]:
        """Parseia o resultado da revisão"""
        try:
            # Limpar markdown se houver
            if "```json" in review_text:
                review_text = review_text.split("```json")[1].split("```")[0]
            elif "```" in review_text:
                review_text = review_text.split("```")[1].split("```")[0]

            review_data = json.loads(review_text.strip())

            # Adicionar metadados
            review_id = f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            return {
                'review_id': review_id,
                'timestamp': datetime.now().isoformat(),
                'language': language,
                'code_length': len(code),
                'overall_score': review_data.get('overall_score', 0),
                'issues': review_data.get('issues', []),
                'suggestions': review_data.get('suggestions', []),
                'summary': review_data.get('summary', 'Revisão concluída'),
                'approved': review_data.get('approved', True)
            }

        except Exception as e:
            print(f"Erro ao parsear revisão: {e}")

            # Fallback: revisão básica
            return self._basic_review(code, language)

    def _basic_review(self, code: str, language: str) -> Dict[str, Any]:
        """Revisão básica sem IA (fallback)"""

        issues = []

        # Checagens básicas de segurança (Python)
        if language == "python":
            if "eval(" in code:
                issues.append({
                    "severity": "critical",
                    "type": "security",
                    "line": None,
                    "message": "Uso de eval() detectado - vulnerabilidade de segurança",
                    "suggestion": "Evite eval(). Use ast.literal_eval() ou json.loads()"
                })

            if "exec(" in code:
                issues.append({
                    "severity": "critical",
                    "type": "security",
                    "line": None,
                    "message": "Uso de exec() detectado - vulnerabilidade de segurança",
                    "suggestion": "Evite exec(). Refatore o código para não precisar de execução dinâmica"
                })

            if "input(" in code and "int(" not in code and "float(" not in code:
                issues.append({
                    "severity": "medium",
                    "type": "security",
                    "line": None,
                    "message": "Input sem validação detectado",
                    "suggestion": "Sempre valide e sanitize inputs do usuário"
                })

        # JavaScript
        elif language == "javascript":
            if "eval(" in code:
                issues.append({
                    "severity": "critical",
                    "type": "security",
                    "line": None,
                    "message": "Uso de eval() detectado - vulnerabilidade de segurança",
                    "suggestion": "Evite eval(). Use JSON.parse() ou funções específicas"
                })

            if "innerHTML" in code:
                issues.append({
                    "severity": "high",
                    "type": "security",
                    "line": None,
                    "message": "Uso de innerHTML - possível XSS",
                    "suggestion": "Use textContent ou sanitize o HTML com DOMPurify"
                })

        review_id = f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        approved = len([i for i in issues if i['severity'] in ['critical', 'high']]) == 0

        return {
            'review_id': review_id,
            'timestamp': datetime.now().isoformat(),
            'language': language,
            'code_length': len(code),
            'overall_score': 100 if approved else 60,
            'issues': issues,
            'suggestions': [],
            'summary': f"Revisão básica concluída. {len(issues)} issues encontrados." if issues else "Nenhum issue detectado na revisão básica.",
            'approved': approved
        }

    def get_review_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna histórico de revisões"""
        return self.review_history[-limit:]

    def get_review_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de revisões"""
        if not self.review_history:
            return {
                'total_reviews': 0,
                'approved': 0,
                'rejected': 0,
                'avg_score': 0,
                'critical_issues': 0
            }

        total = len(self.review_history)
        approved = len([r for r in self.review_history if r['approved']])
        rejected = total - approved

        scores = [r['overall_score'] for r in self.review_history]
        avg_score = sum(scores) / len(scores) if scores else 0

        critical_issues = sum(
            len([i for i in r['issues'] if i['severity'] == 'critical'])
            for r in self.review_history
        )

        return {
            'total_reviews': total,
            'approved': approved,
            'rejected': rejected,
            'avg_score': round(avg_score, 2),
            'critical_issues': critical_issues
        }
