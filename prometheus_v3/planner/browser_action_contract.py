"""
BROWSER ACTION CONTRACT
Contrato de comunicação entre Planner e BrowserExecutor

Define formato padrão para ações de automação web que o Planner pode gerar
e que o BrowserExecutor pode executar.
"""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# DEFINIÇÃO DE AÇÕES
# ============================================================================

class BrowserActionType(Enum):
    """Tipos de ação de browser que o Planner pode gerar"""

    # Navegação
    NAVIGATE = "navigate"                    # Navegar para URL

    # Interação com elementos
    CLICK_ELEMENT = "click_element"          # Clicar em elemento
    FILL_INPUT = "fill_input"                # Preencher campo

    # Extração de dados
    EXTRACT_TEXT = "extract_text"            # Extrair texto
    GET_PAGE_INFO = "get_page_info"          # Info da página

    # Utilities
    SCREENSHOT = "screenshot"                # Screenshot
    WAIT_FOR_ELEMENT = "wait_for_element"    # Aguardar elemento
    EXECUTE_SCRIPT = "execute_script"        # Executar JS

# ============================================================================
# ESPECIFICAÇÃO DE PARÂMETROS POR AÇÃO
# ============================================================================

BROWSER_ACTION_PARAMS = {
    "navigate": {
        "required": ["url"],
        "optional": [],
        "description": "Navega para uma URL específica",
        "example": {
            "url": "https://www.google.com"
        }
    },

    "click_element": {
        "required": ["selector"],
        "optional": ["options"],
        "description": "Clica em um elemento usando CSS selector",
        "example": {
            "selector": "button.login-btn",
            "options": {"force": False}
        }
    },

    "fill_input": {
        "required": ["selector", "text"],
        "optional": ["options"],
        "description": "Preenche um campo de input",
        "example": {
            "selector": "input#email",
            "text": "usuario@exemplo.com",
            "options": {}
        }
    },

    "extract_text": {
        "required": ["selector"],
        "optional": [],
        "description": "Extrai texto de um elemento",
        "example": {
            "selector": "h1.title"
        }
    },

    "screenshot": {
        "required": [],
        "optional": ["path", "full_page"],
        "description": "Tira screenshot da página",
        "example": {
            "path": "screenshot.png",
            "full_page": True
        }
    },

    "wait_for_element": {
        "required": ["selector"],
        "optional": ["timeout"],
        "description": "Aguarda elemento aparecer na página",
        "example": {
            "selector": "div.content",
            "timeout": 30000
        }
    },

    "execute_script": {
        "required": ["script"],
        "optional": [],
        "description": "Executa JavaScript na página",
        "example": {
            "script": "return document.title;"
        }
    },

    "get_page_info": {
        "required": [],
        "optional": [],
        "description": "Obtém informações sobre a página atual",
        "example": {}
    }
}

# ============================================================================
# MAPEAMENTO LINGUAGEM NATURAL → AÇÃO
# ============================================================================

NATURAL_LANGUAGE_MAPPING = {
    # Navegação
    "abrir": "navigate",
    "acessar": "navigate",
    "ir para": "navigate",
    "navegar": "navigate",

    # Clique
    "clicar": "click_element",
    "apertar": "click_element",
    "selecionar": "click_element",

    # Preenchimento
    "preencher": "fill_input",
    "digitar": "fill_input",
    "inserir": "fill_input",
    "escrever": "fill_input",
    "completar": "fill_input",

    # Extração
    "extrair": "extract_text",
    "obter texto": "extract_text",
    "copiar": "extract_text",
    "ler": "extract_text",

    # Screenshot
    "screenshot": "screenshot",
    "capturar": "screenshot",
    "printar": "screenshot",

    # Aguardar
    "aguardar": "wait_for_element",
    "esperar": "wait_for_element",

    # Script
    "executar script": "execute_script",
    "rodar javascript": "execute_script",

    # Info
    "info da página": "get_page_info",
    "informações": "get_page_info"
}

# ============================================================================
# FORMATO DE STEP PARA BROWSER AUTOMATION
# ============================================================================

@dataclass
class BrowserStep:
    """
    Representa um step de browser automation gerado pelo Planner

    Formato esperado pelo BrowserExecutor:
    {
        "order": 1,
        "action": "navigate",
        "description": "Navegar para Google",
        "params": {
            "url": "https://www.google.com"
        },
        "critical": false,
        "timeout": 30
    }
    """
    order: int
    action: str  # Deve ser um dos BrowserActionType
    description: str
    params: Dict[str, Any]
    critical: bool = False
    timeout: int = 30  # segundos

# ============================================================================
# VALIDAÇÃO DE STEPS
# ============================================================================

def validate_browser_step(step: Dict[str, Any]) -> Dict[str, Any]:
    """
    Valida se um step de browser está no formato correto

    Args:
        step: Step gerado pelo Planner

    Returns:
        {"valid": bool, "errors": List[str]}
    """
    errors = []

    # Verificar campos obrigatórios
    required_fields = ["action", "params"]
    for field in required_fields:
        if field not in step:
            errors.append(f"Campo obrigatório '{field}' ausente")

    if not errors and step["action"] in BROWSER_ACTION_PARAMS:
        # Verificar parâmetros da ação
        action_spec = BROWSER_ACTION_PARAMS[step["action"]]
        params = step["params"]

        # Verificar parâmetros obrigatórios
        for required_param in action_spec["required"]:
            if required_param not in params:
                errors.append(
                    f"Parâmetro obrigatório '{required_param}' ausente para ação '{step['action']}'"
                )

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

# ============================================================================
# HELPER PARA PLANNER
# ============================================================================

def get_browser_actions_for_prompt() -> str:
    """
    Retorna descrição formatada das ações de browser para o prompt do Planner

    Usado no PlanGenerator para informar a IA sobre ações disponíveis
    """
    actions_text = "AÇÕES DE BROWSER DISPONÍVEIS:\n\n"

    for action, spec in BROWSER_ACTION_PARAMS.items():
        actions_text += f"{action}:\n"
        actions_text += f"  Descrição: {spec['description']}\n"
        actions_text += f"  Parâmetros obrigatórios: {', '.join(spec['required']) if spec['required'] else 'nenhum'}\n"
        actions_text += f"  Exemplo: {spec['example']}\n\n"

    return actions_text

def map_natural_language_to_action(text: str) -> str:
    """
    Mapeia linguagem natural para ação de browser

    Args:
        text: Texto em linguagem natural

    Returns:
        Nome da ação mapeada ou None
    """
    text_lower = text.lower()

    for keyword, action in NATURAL_LANGUAGE_MAPPING.items():
        if keyword in text_lower:
            return action

    return None

# ============================================================================
# EXEMPLOS DE USO
# ============================================================================

EXAMPLE_BROWSER_PLANS = [
    {
        "description": "Login no RD Station",
        "steps": [
            {
                "order": 1,
                "action": "navigate",
                "description": "Acessar página de login do RD Station",
                "params": {
                    "url": "https://app.rdstation.com.br/login"
                },
                "critical": False
            },
            {
                "order": 2,
                "action": "wait_for_element",
                "description": "Aguardar formulário de login carregar",
                "params": {
                    "selector": "input#email",
                    "timeout": 10000
                },
                "critical": False
            },
            {
                "order": 3,
                "action": "fill_input",
                "description": "Preencher campo de email",
                "params": {
                    "selector": "input#email",
                    "text": "usuario@email.com"
                },
                "critical": True
            },
            {
                "order": 4,
                "action": "fill_input",
                "description": "Preencher campo de senha",
                "params": {
                    "selector": "input#password",
                    "text": "senha123"
                },
                "critical": True
            },
            {
                "order": 5,
                "action": "click_element",
                "description": "Clicar no botão de login",
                "params": {
                    "selector": "button[type='submit']"
                },
                "critical": True
            },
            {
                "order": 6,
                "action": "wait_for_element",
                "description": "Aguardar dashboard carregar",
                "params": {
                    "selector": "div.dashboard",
                    "timeout": 15000
                },
                "critical": False
            },
            {
                "order": 7,
                "action": "screenshot",
                "description": "Tirar screenshot do dashboard",
                "params": {
                    "path": "dashboard_rdstation.png",
                    "full_page": False
                },
                "critical": False
            }
        ]
    },

    {
        "description": "Busca no Google",
        "steps": [
            {
                "order": 1,
                "action": "navigate",
                "description": "Acessar Google",
                "params": {
                    "url": "https://www.google.com"
                },
                "critical": False
            },
            {
                "order": 2,
                "action": "fill_input",
                "description": "Preencher campo de busca",
                "params": {
                    "selector": "input[name='q']",
                    "text": "Prometheus AI"
                },
                "critical": False
            },
            {
                "order": 3,
                "action": "click_element",
                "description": "Clicar em buscar",
                "params": {
                    "selector": "input[name='btnK']"
                },
                "critical": False
            },
            {
                "order": 4,
                "action": "wait_for_element",
                "description": "Aguardar resultados",
                "params": {
                    "selector": "#search",
                    "timeout": 5000
                },
                "critical": False
            },
            {
                "order": 5,
                "action": "extract_text",
                "description": "Extrair primeiro resultado",
                "params": {
                    "selector": "h3"
                },
                "critical": False
            }
        ]
    }
]

# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    'BrowserActionType',
    'BROWSER_ACTION_PARAMS',
    'NATURAL_LANGUAGE_MAPPING',
    'BrowserStep',
    'validate_browser_step',
    'get_browser_actions_for_prompt',
    'map_natural_language_to_action',
    'EXAMPLE_BROWSER_PLANS'
]
