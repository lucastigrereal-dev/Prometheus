"""
Browser Executor - Contratos para Comet
Sistema de contratos de automação de navegador
"""

from .comet_contract import CometContract, CometAction, CometFlow
from .browser_action_schema import ActionSchema, ActionType
from .flow_templates import FlowTemplates

__version__ = "3.5.0"

__all__ = [
    "CometContract",
    "CometAction",
    "CometFlow",
    "ActionSchema",
    "ActionType",
    "FlowTemplates",
]
