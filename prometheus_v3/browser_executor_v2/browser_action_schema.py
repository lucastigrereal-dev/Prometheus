"""
Browser Action Schema
Esquema de ações de navegador para Comet
"""

from enum import Enum
from typing import Optional, Any, Literal
from dataclasses import dataclass, asdict
from datetime import datetime
import json


class ActionType(Enum):
    """Tipos de ações de navegador"""
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    WAIT = "wait"
    EXTRACT = "extract"
    SCROLL = "scroll"
    HOVER = "hover"
    SELECT = "select"
    UPLOAD = "upload"
    SCREENSHOT = "screenshot"
    EXECUTE_JS = "execute_js"
    WAIT_FOR_ELEMENT = "wait_for_element"
    WAIT_FOR_NAVIGATION = "wait_for_navigation"


@dataclass
class ActionSchema:
    """
    Esquema de ação de navegador

    Define estrutura padronizada para ações do Comet
    """
    action_type: ActionType
    selector: Optional[str] = None
    value: Optional[str] = None
    url: Optional[str] = None
    timeout: int = 30000  # milliseconds
    wait_after: int = 1000  # milliseconds
    screenshot: bool = False
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

        # Converter ActionType para enum se string
        if isinstance(self.action_type, str):
            self.action_type = ActionType(self.action_type)

    def to_dict(self) -> dict[str, Any]:
        """Converte para dicionário"""
        data = asdict(self)
        data['action_type'] = self.action_type.value
        return data

    def to_json(self) -> str:
        """Converte para JSON"""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def navigate(cls, url: str, wait_after: int = 2000, **kwargs) -> 'ActionSchema':
        """Cria ação de navegação"""
        return cls(
            action_type=ActionType.NAVIGATE,
            url=url,
            wait_after=wait_after,
            **kwargs
        )

    @classmethod
    def click(cls, selector: str, wait_after: int = 1000, **kwargs) -> 'ActionSchema':
        """Cria ação de click"""
        return cls(
            action_type=ActionType.CLICK,
            selector=selector,
            wait_after=wait_after,
            **kwargs
        )

    @classmethod
    def type_text(cls, selector: str, value: str, wait_after: int = 500, **kwargs) -> 'ActionSchema':
        """Cria ação de digitação"""
        return cls(
            action_type=ActionType.TYPE,
            selector=selector,
            value=value,
            wait_after=wait_after,
            **kwargs
        )

    @classmethod
    def extract(cls, selector: str, attribute: str = "textContent", **kwargs) -> 'ActionSchema':
        """Cria ação de extração"""
        return cls(
            action_type=ActionType.EXTRACT,
            selector=selector,
            metadata={"attribute": attribute, **kwargs.get("metadata", {})}
        )

    @classmethod
    def wait(cls, milliseconds: int, **kwargs) -> 'ActionSchema':
        """Cria ação de espera"""
        return cls(
            action_type=ActionType.WAIT,
            value=str(milliseconds),
            **kwargs
        )

    @classmethod
    def wait_for_element(cls, selector: str, timeout: int = 10000, **kwargs) -> 'ActionSchema':
        """Cria ação de espera por elemento"""
        return cls(
            action_type=ActionType.WAIT_FOR_ELEMENT,
            selector=selector,
            timeout=timeout,
            **kwargs
        )

    @classmethod
    def screenshot(cls, filename: str, **kwargs) -> 'ActionSchema':
        """Cria ação de screenshot"""
        return cls(
            action_type=ActionType.SCREENSHOT,
            value=filename,
            **kwargs
        )

    @classmethod
    def scroll(cls, direction: Literal["up", "down", "top", "bottom"] = "down", **kwargs) -> 'ActionSchema':
        """Cria ação de scroll"""
        return cls(
            action_type=ActionType.SCROLL,
            value=direction,
            **kwargs
        )

    @classmethod
    def execute_js(cls, script: str, **kwargs) -> 'ActionSchema':
        """Cria ação de execução JavaScript"""
        return cls(
            action_type=ActionType.EXECUTE_JS,
            value=script,
            **kwargs
        )

    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Valida ação

        Returns:
            Tupla (is_valid, error_message)
        """
        # Validar NAVIGATE
        if self.action_type == ActionType.NAVIGATE:
            if not self.url:
                return False, "NAVIGATE requires 'url'"

        # Validar CLICK
        if self.action_type == ActionType.CLICK:
            if not self.selector:
                return False, "CLICK requires 'selector'"

        # Validar TYPE
        if self.action_type == ActionType.TYPE:
            if not self.selector or not self.value:
                return False, "TYPE requires 'selector' and 'value'"

        # Validar EXTRACT
        if self.action_type == ActionType.EXTRACT:
            if not self.selector:
                return False, "EXTRACT requires 'selector'"

        # Validar WAIT_FOR_ELEMENT
        if self.action_type == ActionType.WAIT_FOR_ELEMENT:
            if not self.selector:
                return False, "WAIT_FOR_ELEMENT requires 'selector'"

        return True, None


class SelectorBuilder:
    """
    Builder para seletores CSS
    """

    @staticmethod
    def by_id(element_id: str) -> str:
        """Selector por ID"""
        return f"#{element_id}"

    @staticmethod
    def by_class(class_name: str) -> str:
        """Selector por classe"""
        return f".{class_name}"

    @staticmethod
    def by_attribute(tag: str, attribute: str, value: str) -> str:
        """Selector por atributo"""
        return f'{tag}[{attribute}="{value}"]'

    @staticmethod
    def by_text(tag: str, text: str) -> str:
        """Selector por texto (aproximado)"""
        # Nota: CSS não suporta :contains, usar XPath ou JS
        return f'{tag}:has-text("{text}")'  # Playwright syntax

    @staticmethod
    def by_placeholder(placeholder: str) -> str:
        """Selector por placeholder"""
        return f'[placeholder="{placeholder}"]'

    @staticmethod
    def by_name(name: str) -> str:
        """Selector por name"""
        return f'[name="{name}"]'

    @staticmethod
    def by_type(input_type: str) -> str:
        """Selector por type de input"""
        return f'input[type="{input_type}"]'

    @staticmethod
    def button_with_text(text: str) -> str:
        """Selector de botão por texto"""
        return f'button:has-text("{text}")'

    @staticmethod
    def link_with_text(text: str) -> str:
        """Selector de link por texto"""
        return f'a:has-text("{text}")'
