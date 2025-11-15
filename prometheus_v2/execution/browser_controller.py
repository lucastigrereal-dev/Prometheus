"""
BROWSER CONTROLLER - Controle Total de Navegador
Sistema de automação web com fallback em cascata e modo stealth
"""

import asyncio
import random
import time
import json
import logging
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import base64

# Importações condicionais
try:
    from playwright.async_api import async_playwright, Browser, Page, ElementHandle
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright não disponível - instale com: pip install playwright && playwright install")

try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.keys import Keys
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("Selenium não disponível - instale com: pip install selenium")

try:
    import pyautogui
    pyautogui.FAILSAFE = True
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("PyAutoGUI não disponível - instale com: pip install pyautogui")

try:
    import cv2
    import numpy as np
    from PIL import Image
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("OpenCV não disponível para detecção visual")

logger = logging.getLogger('BrowserController')

# ============================================================================
# ESTRUTURAS DE DADOS
# ============================================================================

class BrowserType(Enum):
    """Tipos de navegador suportados"""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"
    CHROME = "chrome"
    EDGE = "edge"

class ActionType(Enum):
    """Tipos de ação no navegador"""
    NAVIGATE = "navigate"
    CLICK = "click"
    TYPE = "type"
    SELECT = "select"
    SCREENSHOT = "screenshot"
    SCROLL = "scroll"
    WAIT = "wait"
    HOVER = "hover"
    DRAG_DROP = "drag_drop"
    UPLOAD = "upload"
    EXECUTE_JS = "execute_js"
    EXTRACT = "extract"

@dataclass
class BrowserAction:
    """Representa uma ação no navegador"""
    action_type: ActionType
    selector: Optional[str] = None
    value: Optional[Any] = None
    options: Dict[str, Any] = None
    timeout: int = 30
    retry_count: int = 3

@dataclass
class BrowserSession:
    """Sessão de navegador ativa"""
    id: str
    type: BrowserType
    browser: Any  # Browser instance
    page: Any  # Page instance
    context: Any  # Context instance
    created_at: float
    last_action: float
    cookies: List[Dict] = None
    local_storage: Dict[str, str] = None

# ============================================================================
# STEALTH CONFIG - Anti-Detecção
# ============================================================================

class StealthConfig:
    """Configurações para evitar detecção de bot"""
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    
    VIEWPORT_SIZES = [
        (1920, 1080),
        (1366, 768),
        (1440, 900),
        (1536, 864)
    ]
    
    @staticmethod
    def get_random_user_agent() -> str:
        """Retorna user agent aleatório"""
        return random.choice(StealthConfig.USER_AGENTS)
    
    @staticmethod
    def get_random_viewport() -> Tuple[int, int]:
        """Retorna viewport aleatório"""
        return random.choice(StealthConfig.VIEWPORT_SIZES)
    
    @staticmethod
    def humanize_delay() -> float:
        """Retorna delay humanizado em segundos"""
        return random.uniform(0.5, 2.0)
    
    @staticmethod
    def get_stealth_js() -> str:
        """JavaScript para mascarar automação"""
        return """
        // Remove webdriver flag
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        });
        
        // Mock plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [
                {name: 'Chrome PDF Plugin'},
                {name: 'Chrome PDF Viewer'},
                {name: 'Native Client'}
            ]
        });
        
        // Mock languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['pt-BR', 'pt', 'en-US', 'en']
        });
        
        // Mock permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
        );
        
        // Mock WebGL
        const getParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Intel Inc.';
            }
            if (parameter === 37446) {
                return 'Intel Iris OpenGL Engine';
            }
            return getParameter(parameter);
        };
        """

# ============================================================================
# PLAYWRIGHT CONTROLLER
# ============================================================================

class PlaywrightController:
    """Controlador usando Playwright (principal)"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.stealth_mode = config.get('stealth_mode', True)
        
    async def initialize(self) -> bool:
        """Inicializa o Playwright"""
        try:
            self.playwright = await async_playwright().start()
            
            # Configurações do navegador
            browser_type = self.config.get('browser', 'chromium')
            headless = self.config.get('headless', False)
            
            # Opções stealth
            if self.stealth_mode:
                viewport = StealthConfig.get_random_viewport()
                user_agent = StealthConfig.get_random_user_agent()
            else:
                viewport = {'width': 1920, 'height': 1080}
                user_agent = None
            
            # Lança navegador
            if browser_type == 'chromium':
                self.browser = await self.playwright.chromium.launch(
                    headless=headless,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox'
                    ]
                )
            elif browser_type == 'firefox':
                self.browser = await self.playwright.firefox.launch(headless=headless)
            else:
                self.browser = await self.playwright.webkit.launch(headless=headless)
            
            # Cria contexto com configurações
            self.context = await self.browser.new_context(
                viewport=viewport,
                user_agent=user_agent,
                locale='pt-BR',
                timezone_id='America/Sao_Paulo',
                permissions=['geolocation', 'notifications'],
                color_scheme='light'
            )
            
            # Adiciona scripts stealth
            if self.stealth_mode:
                await self.context.add_init_script(StealthConfig.get_stealth_js())
            
            # Cria página
            self.page = await self.context.new_page()
            
            logger.info(f"✅ Playwright initialized with {browser_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Playwright: {e}")
            return False
    
    async def navigate(self, url: str, wait_until: str = 'networkidle') -> bool:
        """Navega para URL"""
        try:
            await self.page.goto(url, wait_until=wait_until, timeout=30000)
            await asyncio.sleep(StealthConfig.humanize_delay() if self.stealth_mode else 0.5)
            return True
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False
    
    async def click(self, selector: str, options: Dict = None) -> bool:
        """Clica em elemento"""
        try:
            # Aguarda elemento
            await self.page.wait_for_selector(selector, timeout=10000)
            
            # Move mouse humanizado
            if self.stealth_mode:
                element = await self.page.query_selector(selector)
                box = await element.bounding_box()
                if box:
                    # Move para elemento com curva
                    await self.page.mouse.move(
                        box['x'] + box['width'] / 2,
                        box['y'] + box['height'] / 2,
                        steps=random.randint(10, 20)
                    )
                    await asyncio.sleep(random.uniform(0.1, 0.3))
            
            # Clica
            await self.page.click(selector, **(options or {}))
            await asyncio.sleep(StealthConfig.humanize_delay() if self.stealth_mode else 0.5)
            return True
            
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return False
    
    async def type_text(self, selector: str, text: str, options: Dict = None) -> bool:
        """Digite texto em elemento"""
        try:
            await self.page.wait_for_selector(selector, timeout=10000)
            
            # Limpa campo primeiro
            await self.page.click(selector, click_count=3)
            
            # Digite humanizado
            if self.stealth_mode:
                for char in text:
                    await self.page.type(selector, char, delay=random.randint(50, 150))
                    if random.random() < 0.1:  # 10% chance de pausa
                        await asyncio.sleep(random.uniform(0.5, 1.0))
            else:
                await self.page.type(selector, text)
            
            return True
            
        except Exception as e:
            logger.error(f"Type failed: {e}")
            return False
    
    async def extract_text(self, selector: str) -> Optional[str]:
        """Extrai texto de elemento"""
        try:
            await self.page.wait_for_selector(selector, timeout=10000)
            return await self.page.text_content(selector)
        except Exception as e:
            logger.error(f"Extract failed: {e}")
            return None
    
    async def screenshot(self, path: str = None, full_page: bool = False) -> Optional[bytes]:
        """Tira screenshot"""
        try:
            options = {'full_page': full_page}
            if path:
                options['path'] = path
            
            screenshot_bytes = await self.page.screenshot(**options)
            return screenshot_bytes
            
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return None
    
    async def execute_script(self, script: str) -> Any:
        """Executa JavaScript"""
        try:
            return await self.page.evaluate(script)
        except Exception as e:
            logger.error(f"Script execution failed: {e}")
            return None
    
    async def wait_for_selector(self, selector: str, timeout: int = 30000) -> bool:
        """Aguarda elemento aparecer"""
        try:
            await self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except:
            return False
    
    async def close(self):
        """Fecha navegador"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

# ============================================================================
# SELENIUM CONTROLLER (Fallback)
# ============================================================================

class SeleniumController:
    """Controlador usando Selenium (fallback)"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.driver = None
        self.stealth_mode = config.get('stealth_mode', True)
        
    def initialize(self) -> bool:
        """Inicializa o Selenium"""
        try:
            # Opções do Chrome
            options = webdriver.ChromeOptions()
            
            if self.config.get('headless', False):
                options.add_argument('--headless')
            
            # Opções stealth
            if self.stealth_mode:
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_experimental_option("excludeSwitches", ["enable-automation"])
                options.add_experimental_option('useAutomationExtension', False)
                options.add_argument(f'user-agent={StealthConfig.get_random_user_agent()}')
            
            # Outras opções
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
            
            # Cria driver
            self.driver = webdriver.Chrome(options=options)
            
            # Injeta JavaScript stealth
            if self.stealth_mode:
                self.driver.execute_script(StealthConfig.get_stealth_js())
            
            logger.info("✅ Selenium initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Selenium: {e}")
            return False
    
    def navigate(self, url: str) -> bool:
        """Navega para URL"""
        try:
            self.driver.get(url)
            if self.stealth_mode:
                time.sleep(StealthConfig.humanize_delay())
            return True
        except Exception as e:
            logger.error(f"Navigation failed: {e}")
            return False
    
    def click(self, selector: str) -> bool:
        """Clica em elemento"""
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
            )
            
            # Move para elemento se stealth
            if self.stealth_mode:
                ActionChains(self.driver).move_to_element(element).perform()
                time.sleep(random.uniform(0.1, 0.3))
            
            element.click()
            
            if self.stealth_mode:
                time.sleep(StealthConfig.humanize_delay())
            
            return True
            
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return False
    
    def type_text(self, selector: str, text: str) -> bool:
        """Digite texto"""
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector))
            )
            
            element.clear()
            
            # Digite humanizado
            if self.stealth_mode:
                for char in text:
                    element.send_keys(char)
                    time.sleep(random.uniform(0.05, 0.15))
            else:
                element.send_keys(text)
            
            return True
            
        except Exception as e:
            logger.error(f"Type failed: {e}")
            return False
    
    def extract_text(self, selector: str) -> Optional[str]:
        """Extrai texto"""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            return element.text
        except Exception as e:
            logger.error(f"Extract failed: {e}")
            return None
    
    def screenshot(self, path: str = None) -> Optional[bytes]:
        """Tira screenshot"""
        try:
            if path:
                self.driver.save_screenshot(path)
                with open(path, 'rb') as f:
                    return f.read()
            else:
                return self.driver.get_screenshot_as_png()
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return None
    
    def close(self):
        """Fecha navegador"""
        if self.driver:
            self.driver.quit()

# ============================================================================
# PYAUTOGUI CONTROLLER (Last Resort)
# ============================================================================

class PyAutoGUIController:
    """Controlador usando PyAutoGUI (último recurso)"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.confidence = 0.8  # Para reconhecimento de imagem
        
    def initialize(self) -> bool:
        """Inicializa PyAutoGUI"""
        if not PYAUTOGUI_AVAILABLE:
            return False
        
        # Configurações de segurança
        pyautogui.PAUSE = 0.5  # Pausa entre ações
        pyautogui.FAILSAFE = True  # Canto superior esquerdo para parar
        
        logger.info("✅ PyAutoGUI initialized")
        return True
    
    def find_element_by_image(self, image_path: str) -> Optional[Tuple[int, int]]:
        """Encontra elemento por imagem"""
        try:
            location = pyautogui.locateOnScreen(
                image_path,
                confidence=self.confidence
            )
            if location:
                return pyautogui.center(location)
            return None
        except Exception as e:
            logger.error(f"Image search failed: {e}")
            return None
    
    def click_at(self, x: int, y: int, humanize: bool = True) -> bool:
        """Clica em coordenada"""
        try:
            if humanize:
                # Move com curva bezier
                pyautogui.moveTo(
                    x, y,
                    duration=random.uniform(0.5, 1.5),
                    tween=pyautogui.easeInOutQuad
                )
                time.sleep(random.uniform(0.1, 0.3))
            
            pyautogui.click(x, y)
            return True
            
        except Exception as e:
            logger.error(f"Click failed: {e}")
            return False
    
    def type_text(self, text: str, humanize: bool = True) -> bool:
        """Digite texto"""
        try:
            if humanize:
                pyautogui.typewrite(
                    text,
                    interval=random.uniform(0.05, 0.15)
                )
            else:
                pyautogui.typewrite(text)
            
            return True
            
        except Exception as e:
            logger.error(f"Type failed: {e}")
            return False
    
    def screenshot(self) -> Optional[Any]:
        """Tira screenshot"""
        try:
            return pyautogui.screenshot()
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return None

# ============================================================================
# BROWSER CONTROLLER MASTER - Orquestrador
# ============================================================================

class BrowserController:
    """
    Controlador master que orquestra todos os métodos
    com fallback automático e detecção visual
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.sessions: Dict[str, BrowserSession] = {}
        self.active_session_id: Optional[str] = None
        
        # Controllers
        self.playwright_ctrl = None
        self.selenium_ctrl = None
        self.pyautogui_ctrl = None
        
        # Estado
        self.current_method = None
        self.fallback_chain = ['playwright', 'selenium', 'pyautogui']
        
    async def initialize(self) -> bool:
        """Inicializa o controlador"""
        logger.info("🚀 Initializing Browser Controller...")
        
        # Tenta inicializar Playwright
        if PLAYWRIGHT_AVAILABLE:
            self.playwright_ctrl = PlaywrightController(self.config)
            if await self.playwright_ctrl.initialize():
                self.current_method = 'playwright'
                logger.info("✅ Using Playwright as primary method")
                return True
        
        # Fallback para Selenium
        if SELENIUM_AVAILABLE:
            self.selenium_ctrl = SeleniumController(self.config)
            if self.selenium_ctrl.initialize():
                self.current_method = 'selenium'
                logger.info("⚠️ Using Selenium as fallback")
                return True
        
        # Último recurso - PyAutoGUI
        if PYAUTOGUI_AVAILABLE:
            self.pyautogui_ctrl = PyAutoGUIController(self.config)
            if self.pyautogui_ctrl.initialize():
                self.current_method = 'pyautogui'
                logger.info("⚠️ Using PyAutoGUI as last resort")
                return True
        
        logger.error("❌ No browser control method available!")
        return False
    
    async def execute_action(self, action: BrowserAction) -> Dict[str, Any]:
        """
        Executa ação com fallback automático
        """
        result = {
            'success': False,
            'method': self.current_method,
            'data': None,
            'error': None,
            'retries': 0
        }
        
        # Tenta com método atual
        for attempt in range(action.retry_count):
            try:
                if action.action_type == ActionType.NAVIGATE:
                    success = await self._navigate(action.value)
                    
                elif action.action_type == ActionType.CLICK:
                    success = await self._click(action.selector, action.options)
                    
                elif action.action_type == ActionType.TYPE:
                    success = await self._type(action.selector, action.value, action.options)
                    
                elif action.action_type == ActionType.EXTRACT:
                    data = await self._extract(action.selector)
                    success = data is not None
                    result['data'] = data
                    
                elif action.action_type == ActionType.SCREENSHOT:
                    data = await self._screenshot(action.value)
                    success = data is not None
                    result['data'] = data
                    
                elif action.action_type == ActionType.EXECUTE_JS:
                    data = await self._execute_js(action.value)
                    success = True
                    result['data'] = data
                    
                else:
                    success = False
                    result['error'] = f"Unknown action type: {action.action_type}"
                
                if success:
                    result['success'] = True
                    result['retries'] = attempt
                    return result
                    
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                result['error'] = str(e)
                
                # Tenta fallback
                if attempt == action.retry_count - 1:
                    if await self._try_fallback():
                        logger.info(f"Switched to {self.current_method}")
                        continue
        
        return result
    
    async def _navigate(self, url: str) -> bool:
        """Navega com método atual"""
        if self.current_method == 'playwright' and self.playwright_ctrl:
            return await self.playwright_ctrl.navigate(url)
        elif self.current_method == 'selenium' and self.selenium_ctrl:
            return self.selenium_ctrl.navigate(url)
        elif self.current_method == 'pyautogui' and self.pyautogui_ctrl:
            # PyAutoGUI precisa de abordagem diferente
            pyautogui.hotkey('ctrl', 'l')  # Seleciona barra de endereço
            time.sleep(0.5)
            pyautogui.typewrite(url)
            pyautogui.press('enter')
            return True
        return False
    
    async def _click(self, selector: str, options: Dict = None) -> bool:
        """Clica com método atual"""
        if self.current_method == 'playwright' and self.playwright_ctrl:
            return await self.playwright_ctrl.click(selector, options)
        elif self.current_method == 'selenium' and self.selenium_ctrl:
            return self.selenium_ctrl.click(selector)
        elif self.current_method == 'pyautogui' and self.pyautogui_ctrl:
            # Precisa de detecção visual
            return await self._click_visual(selector)
        return False
    
    async def _type(self, selector: str, text: str, options: Dict = None) -> bool:
        """Digite com método atual"""
        if self.current_method == 'playwright' and self.playwright_ctrl:
            return await self.playwright_ctrl.type_text(selector, text, options)
        elif self.current_method == 'selenium' and self.selenium_ctrl:
            return self.selenium_ctrl.type_text(selector, text)
        elif self.current_method == 'pyautogui' and self.pyautogui_ctrl:
            # Clica primeiro, depois digita
            if await self._click_visual(selector):
                return self.pyautogui_ctrl.type_text(text)
        return False
    
    async def _extract(self, selector: str) -> Optional[str]:
        """Extrai texto com método atual"""
        if self.current_method == 'playwright' and self.playwright_ctrl:
            return await self.playwright_ctrl.extract_text(selector)
        elif self.current_method == 'selenium' and self.selenium_ctrl:
            return self.selenium_ctrl.extract_text(selector)
        elif self.current_method == 'pyautogui':
            # PyAutoGUI não pode extrair texto diretamente
            logger.warning("Text extraction not available with PyAutoGUI")
            return None
        return None
    
    async def _screenshot(self, path: str = None) -> Optional[bytes]:
        """Tira screenshot com método atual"""
        if self.current_method == 'playwright' and self.playwright_ctrl:
            return await self.playwright_ctrl.screenshot(path)
        elif self.current_method == 'selenium' and self.selenium_ctrl:
            return self.selenium_ctrl.screenshot(path)
        elif self.current_method == 'pyautogui' and self.pyautogui_ctrl:
            screenshot = self.pyautogui_ctrl.screenshot()
            if screenshot and path:
                screenshot.save(path)
            return screenshot
        return None
    
    async def _execute_js(self, script: str) -> Any:
        """Executa JavaScript"""
        if self.current_method == 'playwright' and self.playwright_ctrl:
            return await self.playwright_ctrl.execute_script(script)
        elif self.current_method == 'selenium' and self.selenium_ctrl:
            return self.selenium_ctrl.driver.execute_script(script)
        else:
            logger.warning("JavaScript execution not available with PyAutoGUI")
            return None
    
    async def _click_visual(self, selector: str) -> bool:
        """Clica usando detecção visual (PyAutoGUI)"""
        if not self.pyautogui_ctrl:
            return False
        
        # Tira screenshot
        screenshot = await self._screenshot()
        if not screenshot:
            return False
        
        # TODO: Implementar detecção visual real com OCR/CV2
        # Por enquanto, usa coordenadas fixas ou imagem de referência
        
        # Exemplo simplificado:
        # 1. Salva screenshot
        # 2. Usa OCR para encontrar texto
        # 3. Clica na posição
        
        logger.warning("Visual click not fully implemented")
        return False
    
    async def _try_fallback(self) -> bool:
        """Tenta próximo método de fallback"""
        current_index = self.fallback_chain.index(self.current_method)
        
        if current_index < len(self.fallback_chain) - 1:
            next_method = self.fallback_chain[current_index + 1]
            
            if next_method == 'selenium' and SELENIUM_AVAILABLE:
                if not self.selenium_ctrl:
                    self.selenium_ctrl = SeleniumController(self.config)
                if self.selenium_ctrl.initialize():
                    self.current_method = 'selenium'
                    return True
                    
            elif next_method == 'pyautogui' and PYAUTOGUI_AVAILABLE:
                if not self.pyautogui_ctrl:
                    self.pyautogui_ctrl = PyAutoGUIController(self.config)
                if self.pyautogui_ctrl.initialize():
                    self.current_method = 'pyautogui'
                    return True
        
        return False
    
    async def create_session(self, session_id: str = None) -> str:
        """Cria nova sessão de navegador"""
        import uuid
        
        session_id = session_id or str(uuid.uuid4())
        
        session = BrowserSession(
            id=session_id,
            type=BrowserType.CHROMIUM,
            browser=None,
            page=None,
            context=None,
            created_at=time.time(),
            last_action=time.time()
        )
        
        self.sessions[session_id] = session
        self.active_session_id = session_id
        
        logger.info(f"Created session: {session_id}")
        return session_id
    
    async def close(self):
        """Fecha todos os navegadores"""
        if self.playwright_ctrl:
            await self.playwright_ctrl.close()
        if self.selenium_ctrl:
            self.selenium_ctrl.close()
        
        logger.info("Browser Controller closed")

# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

async def smart_wait(page: Any, selector: str, timeout: int = 30) -> bool:
    """Aguarda inteligente por elemento"""
    strategies = [
        lambda: page.wait_for_selector(selector, timeout=timeout),
        lambda: page.wait_for_selector(selector, state='visible', timeout=timeout),
        lambda: page.wait_for_selector(selector, state='attached', timeout=timeout),
    ]
    
    for strategy in strategies:
        try:
            await strategy()
            return True
        except:
            continue
    
    return False

def extract_form_fields(html: str) -> List[Dict[str, str]]:
    """Extrai campos de formulário do HTML"""
    from bs4 import BeautifulSoup
    
    soup = BeautifulSoup(html, 'html.parser')
    fields = []
    
    for input_elem in soup.find_all(['input', 'textarea', 'select']):
        field = {
            'type': input_elem.get('type', 'text'),
            'name': input_elem.get('name', ''),
            'id': input_elem.get('id', ''),
            'required': input_elem.has_attr('required'),
            'placeholder': input_elem.get('placeholder', '')
        }
        fields.append(field)
    
    return fields

# ============================================================================
# EXEMPLO DE USO
# ============================================================================

async def example_usage():
    """Demonstra uso do Browser Controller"""
    
    # Configuração
    config = {
        'browser': 'chromium',
        'headless': False,
        'stealth_mode': True
    }
    
    # Cria controller
    controller = BrowserController(config)
    
    # Inicializa
    if not await controller.initialize():
        print("Failed to initialize browser controller")
        return
    
    # Ações de exemplo
    actions = [
        BrowserAction(
            action_type=ActionType.NAVIGATE,
            value="https://www.google.com"
        ),
        BrowserAction(
            action_type=ActionType.TYPE,
            selector="input[name='q']",
            value="Prometheus AI assistant"
        ),
        BrowserAction(
            action_type=ActionType.CLICK,
            selector="input[type='submit']"
        ),
        BrowserAction(
            action_type=ActionType.SCREENSHOT,
            value="google_results.png"
        )
    ]
    
    # Executa ações
    for action in actions:
        print(f"Executing: {action.action_type.value}")
        result = await controller.execute_action(action)
        
        if result['success']:
            print(f"✅ Success using {result['method']}")
        else:
            print(f"❌ Failed: {result['error']}")
    
    # Fecha
    await controller.close()

if __name__ == "__main__":
    asyncio.run(example_usage())
