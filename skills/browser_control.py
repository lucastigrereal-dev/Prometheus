"""
PROMETHEUS BROWSER CONTROL - Automação de Navegador Web
Controla navegador para automação de sites, pesquisas e extração de dados
"""

import os
import re
import time
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

# Browser automation
try:
    from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️ Playwright não instalado.")
    print("Instale com: pip install playwright && playwright install chromium")

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PrometheusBrowserControl:
    """
    Sistema de controle de navegador com Playwright
    """

    def __init__(self, headless: bool = False):
        """
        Inicializa o controlador de navegador

        Args:
            headless: Se True, naveg sem interface gráfica
        """
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright não está instalado")

        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.default_timeout = 30000  # 30 segundos

        logger.info("PrometheusBrowserControl inicializado")

    def start_browser(self) -> Dict[str, Any]:
        """
        Inicia o navegador

        Returns:
            Resultado da operação
        """
        try:
            if self.browser:
                logger.info("Navegador já está aberto")
                return {"success": True, "message": "Navegador já ativo"}

            logger.info("Iniciando navegador...")
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=self.headless)
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            self.page = self.context.new_page()
            self.page.set_default_timeout(self.default_timeout)

            logger.info("Navegador iniciado com sucesso")
            return {"success": True, "message": "Navegador iniciado"}

        except Exception as e:
            logger.error(f"Erro ao iniciar navegador: {e}")
            return {"success": False, "error": str(e)}

    def stop_browser(self) -> Dict[str, Any]:
        """
        Fecha o navegador

        Returns:
            Resultado da operação
        """
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()

            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None

            logger.info("Navegador fechado")
            return {"success": True, "message": "Navegador fechado"}

        except Exception as e:
            logger.error(f"Erro ao fechar navegador: {e}")
            return {"success": False, "error": str(e)}

    def navigate_to(self, url: str) -> Dict[str, Any]:
        """
        Navega para uma URL

        Args:
            url: URL do site

        Returns:
            Resultado da navegação
        """
        try:
            if not self.page:
                self.start_browser()

            # Adicionar https:// se não tiver protocolo
            if not url.startswith(('http://', 'https://')):
                url = f'https://{url}'

            logger.info(f"Navegando para: {url}")
            self.page.goto(url, wait_until='domcontentloaded')

            title = self.page.title()
            current_url = self.page.url

            return {
                "success": True,
                "url": current_url,
                "title": title
            }

        except PlaywrightTimeoutError:
            logger.error(f"Timeout ao acessar {url}")
            return {"success": False, "error": "Timeout ao carregar página"}

        except Exception as e:
            logger.error(f"Erro ao navegar para {url}: {e}")
            return {"success": False, "error": str(e)}

    def click_element(self, selector: str) -> Dict[str, Any]:
        """
        Clica em um elemento

        Args:
            selector: Seletor CSS do elemento

        Returns:
            Resultado do click
        """
        try:
            if not self.page:
                return {"success": False, "error": "Navegador não está aberto"}

            logger.info(f"Clicando em: {selector}")
            self.page.click(selector)

            return {"success": True, "message": f"Clicado em {selector}"}

        except PlaywrightTimeoutError:
            logger.error(f"Elemento não encontrado: {selector}")
            return {"success": False, "error": f"Elemento {selector} não encontrado"}

        except Exception as e:
            logger.error(f"Erro ao clicar em {selector}: {e}")
            return {"success": False, "error": str(e)}

    def fill_field(self, selector: str, value: str) -> Dict[str, Any]:
        """
        Preenche um campo de formulário

        Args:
            selector: Seletor CSS do campo
            value: Valor a preencher

        Returns:
            Resultado da operação
        """
        try:
            if not self.page:
                return {"success": False, "error": "Navegador não está aberto"}

            logger.info(f"Preenchendo campo {selector} com: {value}")
            self.page.fill(selector, value)

            return {"success": True, "message": f"Campo {selector} preenchido"}

        except PlaywrightTimeoutError:
            logger.error(f"Campo não encontrado: {selector}")
            return {"success": False, "error": f"Campo {selector} não encontrado"}

        except Exception as e:
            logger.error(f"Erro ao preencher {selector}: {e}")
            return {"success": False, "error": str(e)}

    def extract_text(self, selector: str) -> Dict[str, Any]:
        """
        Extrai texto de um elemento

        Args:
            selector: Seletor CSS do elemento

        Returns:
            Texto extraído
        """
        try:
            if not self.page:
                return {"success": False, "error": "Navegador não está aberto"}

            logger.info(f"Extraindo texto de: {selector}")
            text = self.page.text_content(selector)

            return {"success": True, "text": text}

        except PlaywrightTimeoutError:
            logger.error(f"Elemento não encontrado: {selector}")
            return {"success": False, "error": f"Elemento {selector} não encontrado"}

        except Exception as e:
            logger.error(f"Erro ao extrair texto de {selector}: {e}")
            return {"success": False, "error": str(e)}

    def screenshot(self, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Tira screenshot da página

        Args:
            filename: Nome do arquivo (opcional)

        Returns:
            Caminho do screenshot
        """
        try:
            if not self.page:
                return {"success": False, "error": "Navegador não está aberto"}

            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.png"

            # Criar diretório screenshots se não existir
            screenshots_dir = Path("screenshots")
            screenshots_dir.mkdir(exist_ok=True)

            filepath = screenshots_dir / filename

            logger.info(f"Tirando screenshot: {filepath}")
            self.page.screenshot(path=str(filepath), full_page=True)

            return {
                "success": True,
                "path": str(filepath),
                "message": f"Screenshot salvo em {filepath}"
            }

        except Exception as e:
            logger.error(f"Erro ao tirar screenshot: {e}")
            return {"success": False, "error": str(e)}

    def search_google(self, query: str) -> Dict[str, Any]:
        """
        Pesquisa no Google

        Args:
            query: Termo de busca

        Returns:
            Resultado da pesquisa
        """
        try:
            # Navegar para Google
            self.navigate_to("https://google.com")

            # Aceitar cookies se aparecer
            try:
                self.page.click('button:has-text("Aceitar tudo")', timeout=3000)
            except:
                pass

            # Digitar na barra de pesquisa
            self.page.fill('textarea[name="q"]', query)
            self.page.press('textarea[name="q"]', 'Enter')

            # Aguardar resultados
            self.page.wait_for_selector('#search', timeout=10000)

            title = self.page.title()

            return {
                "success": True,
                "query": query,
                "title": title,
                "message": f"Pesquisado: {query}"
            }

        except Exception as e:
            logger.error(f"Erro ao pesquisar no Google: {e}")
            return {"success": False, "error": str(e)}

    def execute_javascript(self, script: str) -> Dict[str, Any]:
        """
        Executa JavaScript na página

        Args:
            script: Código JavaScript

        Returns:
            Resultado da execução
        """
        try:
            if not self.page:
                return {"success": False, "error": "Navegador não está aberto"}

            logger.info(f"Executando JavaScript: {script[:50]}...")
            result = self.page.evaluate(script)

            return {"success": True, "result": result}

        except Exception as e:
            logger.error(f"Erro ao executar JavaScript: {e}")
            return {"success": False, "error": str(e)}

    def get_page_info(self) -> Dict[str, Any]:
        """
        Obtém informações da página atual

        Returns:
            Informações da página
        """
        try:
            if not self.page:
                return {"success": False, "error": "Navegador não está aberto"}

            info = {
                "url": self.page.url,
                "title": self.page.title(),
                "success": True
            }

            return info

        except Exception as e:
            logger.error(f"Erro ao obter info da página: {e}")
            return {"success": False, "error": str(e)}


class PrometheusBrowserInterface:
    """
    Interface simplificada para integração com Prometheus Brain
    """

    def __init__(self):
        """Inicializa a interface do Browser Control"""
        self.controller = None
        if PLAYWRIGHT_AVAILABLE:
            self.controller = PrometheusBrowserControl(headless=False)
        logger.info("PrometheusBrowserInterface inicializada")

    def process_command(self, command: str) -> Dict[str, Any]:
        """
        Processa comando em linguagem natural

        Args:
            command: Comando em linguagem natural

        Returns:
            Resultado da execução
        """
        if not self.controller:
            return {"success": False, "error": "Playwright não disponível"}

        command_lower = command.lower().strip()

        try:
            # Abrir site
            if "abrir" in command_lower or "navegar" in command_lower or "acessar" in command_lower:
                url = self._extract_url(command)
                return self.controller.navigate_to(url)

            # Pesquisar no Google
            elif "pesquisar" in command_lower or "buscar" in command_lower:
                if "google" in command_lower:
                    query = self._extract_search_query(command)
                    return self.controller.search_google(query)

            # Clicar
            elif "clicar" in command_lower or "click" in command_lower:
                selector = self._extract_selector(command)
                return self.controller.click_element(selector)

            # Preencher
            elif "preencher" in command_lower or "digitar" in command_lower or "escrever" in command_lower:
                selector, value = self._extract_fill_data(command)
                return self.controller.fill_field(selector, value)

            # Screenshot
            elif "screenshot" in command_lower or "print" in command_lower or "captura" in command_lower:
                return self.controller.screenshot()

            # Fechar
            elif "fechar" in command_lower or "sair" in command_lower:
                return self.controller.stop_browser()

            # Info
            elif "info" in command_lower or "pagina" in command_lower or "onde" in command_lower:
                return self.controller.get_page_info()

            else:
                return {
                    "success": False,
                    "error": "Comando não reconhecido",
                    "suggestion": "Tente: 'abrir google.com', 'pesquisar Python', 'screenshot'"
                }

        except Exception as e:
            logger.error(f"Erro ao processar comando: {e}")
            return {"success": False, "error": str(e)}

    def _extract_url(self, command: str) -> str:
        """Extrai URL do comando"""
        # Procurar por padrão de URL
        url_pattern = r'(https?://[^\s]+|www\.[^\s]+|[a-zA-Z0-9-]+\.(com|br|org|net|io|dev|co)[^\s]*)'
        match = re.search(url_pattern, command)

        if match:
            return match.group(0)

        # Se não encontrar, pegar palavra depois de "abrir", "navegar", etc
        words = command.split()
        keywords = ["abrir", "navegar", "acessar", "site"]
        for i, word in enumerate(words):
            if word.lower() in keywords and i + 1 < len(words):
                return words[i + 1]

        return "google.com"  # Padrão

    def _extract_search_query(self, command: str) -> str:
        """Extrai query de pesquisa do comando"""
        # Remover palavras-chave
        query = command
        keywords = ["pesquisar", "buscar", "google", "sobre", "no", "na", "em"]
        for keyword in keywords:
            query = re.sub(rf'\b{keyword}\b', '', query, flags=re.IGNORECASE)

        return query.strip()

    def _extract_selector(self, command: str) -> str:
        """Extrai seletor CSS do comando"""
        # Procurar por seletor entre aspas
        match = re.search(r'["\']([^"\']+)["\']', command)
        if match:
            return match.group(1)

        # Procurar por "em X" ou "no X"
        match = re.search(r'\b(?:em|no|na)\s+(.+)', command, re.IGNORECASE)
        if match:
            return match.group(1).strip()

        return "body"  # Padrão

    def _extract_fill_data(self, command: str) -> tuple:
        """Extrai seletor e valor para preencher"""
        # Padrão: "preencher CAMPO com VALOR"
        match = re.search(r'(?:preencher|digitar)\s+(.+?)\s+(?:com|:)\s+(.+)', command, re.IGNORECASE)
        if match:
            return match.group(1).strip(), match.group(2).strip()

        return "input", ""  # Padrão


# Teste básico
if __name__ == "__main__":
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright não instalado!")
        print("Instale com: pip install playwright && playwright install chromium")
    else:
        print("✅ Testando Browser Control...")

        interface = PrometheusBrowserInterface()

        # Teste 1: Abrir Google
        print("\n🌐 Teste 1: Abrir Google")
        result = interface.process_command("abrir google.com")
        print(f"Resultado: {result}")

        time.sleep(2)

        # Teste 2: Pesquisar
        print("\n🔍 Teste 2: Pesquisar")
        result = interface.process_command("pesquisar no google sobre Python")
        print(f"Resultado: {result}")

        time.sleep(2)

        # Teste 3: Screenshot
        print("\n📸 Teste 3: Screenshot")
        result = interface.process_command("tirar screenshot")
        print(f"Resultado: {result}")

        time.sleep(1)

        # Teste 4: Fechar
        print("\n🚪 Teste 4: Fechar navegador")
        result = interface.process_command("fechar navegador")
        print(f"Resultado: {result}")

        print("\n✅ Todos os testes concluídos!")
