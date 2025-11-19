"""
Browser Executor - Executa ações de automação web
PRINCÍPIOS:
- Apenas ações seguras e auditadas
- Tudo é logado
- Baseado no BrowserController existente
- Sempre com fallback
"""

import os
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import sys

# Importa BrowserController existente
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from prometheus_v3.browser_controller import BrowserController, BrowserAction, ActionType

class BrowserExecutor:
    """Executor de ações de automação web"""

    BROWSER_ACTIONS = [
        'navigate',           # Navegar para URL
        'click_element',      # Clicar em elemento
        'fill_input',         # Preencher campo de input
        'extract_text',       # Extrair texto de elemento
        'screenshot',         # Tirar screenshot
        'wait_for_element',   # Aguardar elemento
        'execute_script',     # Executar JavaScript
        'get_page_info'       # Obter informações da página
    ]

    def __init__(self, config: Dict[str, Any] = None):
        """
        Inicializa BrowserExecutor

        Args:
            config: Configuração do navegador
                    {
                        'browser': 'chromium|firefox|webkit',
                        'headless': bool,
                        'stealth_mode': bool
                    }
        """
        self.config = config or {
            'browser': 'chromium',
            'headless': False,
            'stealth_mode': True
        }

        self.browser_controller: Optional[BrowserController] = None
        self.is_initialized = False
        self.execution_history = []

    async def initialize(self) -> Dict[str, Any]:
        """Inicializa o navegador"""
        try:
            self.browser_controller = BrowserController(self.config)
            success = await self.browser_controller.initialize()

            if success:
                self.is_initialized = True
                return {
                    'success': True,
                    'message': f'Browser initialized with {self.browser_controller.current_method}',
                    'method': self.browser_controller.current_method
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to initialize any browser method'
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'Initialization error: {str(e)}'
            }

    async def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa uma ação de browser de forma segura

        Args:
            action: Nome da ação a executar
            params: Parâmetros da ação

        Returns:
            Dict com resultado da execução
        """
        # Validar ação
        if action not in self.BROWSER_ACTIONS:
            return {
                'success': False,
                'error': f'Ação "{action}" não está na lista de ações seguras',
                'browser_actions': self.BROWSER_ACTIONS
            }

        # Verificar se browser está inicializado
        if not self.is_initialized:
            init_result = await self.initialize()
            if not init_result['success']:
                return init_result

        # Registrar início
        start_time = datetime.now()

        try:
            # Mapear ação para método
            if action == 'navigate':
                result = await self._navigate(params)

            elif action == 'click_element':
                result = await self._click_element(params)

            elif action == 'fill_input':
                result = await self._fill_input(params)

            elif action == 'extract_text':
                result = await self._extract_text(params)

            elif action == 'screenshot':
                result = await self._screenshot(params)

            elif action == 'wait_for_element':
                result = await self._wait_for_element(params)

            elif action == 'execute_script':
                result = await self._execute_script(params)

            elif action == 'get_page_info':
                result = await self._get_page_info(params)

            else:
                result = {
                    'success': False,
                    'error': f'Ação "{action}" não implementada'
                }

            # Registrar execução
            execution_record = {
                'action': action,
                'params': params,
                'result': result,
                'timestamp': start_time.isoformat(),
                'duration_ms': (datetime.now() - start_time).total_seconds() * 1000
            }

            self.execution_history.append(execution_record)

            return result

        except Exception as e:
            error_result = {
                'success': False,
                'error': f'Erro na execução de {action}: {str(e)}'
            }

            self.execution_history.append({
                'action': action,
                'params': params,
                'result': error_result,
                'timestamp': start_time.isoformat(),
                'duration_ms': (datetime.now() - start_time).total_seconds() * 1000
            })

            return error_result

    # ==================== IMPLEMENTAÇÃO DAS AÇÕES ====================

    async def _navigate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Navega para URL"""
        url = params.get('url')

        if not url:
            return {'success': False, 'error': 'URL é obrigatória'}

        action = BrowserAction(
            action_type=ActionType.NAVIGATE,
            value=url
        )

        result = await self.browser_controller.execute_action(action)

        if result['success']:
            return {
                'success': True,
                'data': {
                    'url': url,
                    'method': result['method']
                }
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Navigation failed')
            }

    async def _click_element(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Clica em elemento"""
        selector = params.get('selector')

        if not selector:
            return {'success': False, 'error': 'Selector é obrigatório'}

        action = BrowserAction(
            action_type=ActionType.CLICK,
            selector=selector,
            options=params.get('options', {})
        )

        result = await self.browser_controller.execute_action(action)

        if result['success']:
            return {
                'success': True,
                'data': {
                    'selector': selector,
                    'clicked': True
                }
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Click failed')
            }

    async def _fill_input(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Preenche campo de input"""
        selector = params.get('selector')
        text = params.get('text', '')

        if not selector:
            return {'success': False, 'error': 'Selector é obrigatório'}

        action = BrowserAction(
            action_type=ActionType.TYPE,
            selector=selector,
            value=text,
            options=params.get('options', {})
        )

        result = await self.browser_controller.execute_action(action)

        if result['success']:
            return {
                'success': True,
                'data': {
                    'selector': selector,
                    'text_length': len(text),
                    'filled': True
                }
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Fill failed')
            }

    async def _extract_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Extrai texto de elemento"""
        selector = params.get('selector')

        if not selector:
            return {'success': False, 'error': 'Selector é obrigatório'}

        action = BrowserAction(
            action_type=ActionType.EXTRACT,
            selector=selector
        )

        result = await self.browser_controller.execute_action(action)

        if result['success']:
            return {
                'success': True,
                'data': {
                    'selector': selector,
                    'text': result.get('data', '')
                }
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Extract failed')
            }

    async def _screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Tira screenshot"""
        path = params.get('path', None)
        full_page = params.get('full_page', False)

        # Se não especificou path, criar um automático
        if not path:
            screenshots_dir = Path('data/executor/screenshots')
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            path = str(screenshots_dir / f'screenshot_{timestamp}.png')

        action = BrowserAction(
            action_type=ActionType.SCREENSHOT,
            value=path
        )

        result = await self.browser_controller.execute_action(action)

        if result['success']:
            return {
                'success': True,
                'data': {
                    'path': path,
                    'full_page': full_page,
                    'saved': True
                }
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Screenshot failed')
            }

    async def _wait_for_element(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Aguarda elemento aparecer"""
        selector = params.get('selector')
        timeout = params.get('timeout', 30000)  # ms

        if not selector:
            return {'success': False, 'error': 'Selector é obrigatório'}

        # Usa o método wait_for_selector do playwright_ctrl diretamente
        if self.browser_controller.playwright_ctrl:
            success = await self.browser_controller.playwright_ctrl.wait_for_selector(
                selector, timeout
            )

            if success:
                return {
                    'success': True,
                    'data': {
                        'selector': selector,
                        'found': True,
                        'timeout': timeout
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f'Element {selector} not found within {timeout}ms'
                }
        else:
            return {
                'success': False,
                'error': 'Wait not supported with current browser method'
            }

    async def _execute_script(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Executa JavaScript"""
        script = params.get('script')

        if not script:
            return {'success': False, 'error': 'Script é obrigatório'}

        action = BrowserAction(
            action_type=ActionType.EXECUTE_JS,
            value=script
        )

        result = await self.browser_controller.execute_action(action)

        if result['success']:
            return {
                'success': True,
                'data': {
                    'result': result.get('data')
                }
            }
        else:
            return {
                'success': False,
                'error': result.get('error', 'Script execution failed')
            }

    async def _get_page_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Obtém informações da página atual"""
        try:
            # Executa JavaScript para obter info da página
            script = """
            ({
                title: document.title,
                url: window.location.href,
                html_length: document.documentElement.innerHTML.length,
                forms_count: document.forms.length,
                inputs_count: document.querySelectorAll('input').length,
                buttons_count: document.querySelectorAll('button').length,
                links_count: document.querySelectorAll('a').length
            })
            """

            action = BrowserAction(
                action_type=ActionType.EXECUTE_JS,
                value=script
            )

            result = await self.browser_controller.execute_action(action)

            if result['success']:
                return {
                    'success': True,
                    'data': result.get('data', {})
                }
            else:
                return {
                    'success': False,
                    'error': 'Failed to get page info'
                }

        except Exception as e:
            return {
                'success': False,
                'error': f'Error getting page info: {str(e)}'
            }

    # ==================== MÉTODOS AUXILIARES ====================

    def get_available_actions(self) -> List[str]:
        """Retorna lista de ações disponíveis"""
        return self.BROWSER_ACTIONS

    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna histórico de execuções"""
        return self.execution_history[-limit:]

    async def close(self):
        """Fecha o navegador"""
        if self.browser_controller:
            await self.browser_controller.close()
            self.is_initialized = False

    def get_status(self) -> Dict[str, Any]:
        """Retorna status do executor"""
        return {
            'initialized': self.is_initialized,
            'browser_method': self.browser_controller.current_method if self.browser_controller else None,
            'config': self.config,
            'total_executions': len(self.execution_history)
        }
