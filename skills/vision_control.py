"""
PROMETHEUS VISION CONTROL - Sistema de Visão e Controle Total do PC
Implementa controle visual completo do computador usando PyAutoGUI, OCR e Vision AI
"""

import io
import os
import re
import sys
import time
import json
import base64
import logging
import requests
import threading
from enum import Enum
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor

# Imports para controle do PC
try:
    import pyautogui
    import pygetwindow as gw
    PYAUTOGUI_AVAILABLE = True
    pyautogui.PAUSE = 0.5  # Pausa entre ações
    pyautogui.FAILSAFE = True  # Canto superior esquerdo para parar
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("⚠️ PyAutoGUI não instalado. Instale com: pip install pyautogui pygetwindow")

# OCR
try:
    import pytesseract
    from PIL import Image, ImageDraw, ImageFont
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️ Tesseract OCR não instalado. Instale com: pip install pytesseract pillow")

# Vision AI
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("⚠️ OpenCV não instalado. Instale com: pip install opencv-python")

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Tipos de ações disponíveis"""
    CLICK = "click"
    DOUBLE_CLICK = "double_click"
    RIGHT_CLICK = "right_click"
    TYPE = "type"
    HOTKEY = "hotkey"
    SCROLL = "scroll"
    DRAG = "drag"
    SCREENSHOT = "screenshot"
    FIND_ELEMENT = "find_element"
    WAIT = "wait"
    MOVE = "move"


@dataclass
class ScreenElement:
    """Elemento detectado na tela"""
    name: str
    type: str  # button, textbox, window, icon, menu, etc
    position: Tuple[int, int]
    size: Tuple[int, int]
    text: Optional[str] = None
    confidence: float = 0.0
    screenshot: Optional[Any] = None
    
    @property
    def center(self) -> Tuple[int, int]:
        """Retorna o centro do elemento"""
        x = self.position[0] + self.size[0] // 2
        y = self.position[1] + self.size[1] // 2
        return (x, y)
    
    @property
    def bounds(self) -> Tuple[int, int, int, int]:
        """Retorna os limites do elemento (x1, y1, x2, y2)"""
        x1, y1 = self.position
        x2 = x1 + self.size[0]
        y2 = y1 + self.size[1]
        return (x1, y1, x2, y2)


class VisionAnalyzer:
    """Analisador de visão usando OCR e AI"""
    
    def __init__(self, gpt4_vision_key: Optional[str] = None):
        """
        Inicializa o analisador de visão
        
        Args:
            gpt4_vision_key: Chave API para GPT-4 Vision (opcional)
        """
        self.gpt4_vision_key = gpt4_vision_key
        self.cache = {}  # Cache de análises recentes
        
        # Configuração do Tesseract (Windows)
        if sys.platform == "win32" and OCR_AVAILABLE:
            # Caminho padrão do Tesseract no Windows
            tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
            if os.path.exists(tesseract_path):
                pytesseract.pytesseract.tesseract_cmd = tesseract_path
    
    def capture_screen(self, region: Optional[Tuple[int, int, int, int]] = None) -> Image.Image:
        """
        Captura screenshot da tela
        
        Args:
            region: Região específica (x, y, width, height)
            
        Returns:
            Imagem PIL
        """
        if not PYAUTOGUI_AVAILABLE:
            raise Exception("PyAutoGUI não disponível")
        
        screenshot = pyautogui.screenshot(region=region)
        return screenshot
    
    def find_text_on_screen(self, text: str, 
                           confidence: float = 0.8) -> List[ScreenElement]:
        """
        Encontra texto na tela usando OCR
        
        Args:
            text: Texto a procurar
            confidence: Confiança mínima
            
        Returns:
            Lista de elementos encontrados
        """
        if not OCR_AVAILABLE:
            logger.warning("OCR não disponível")
            return []
        
        elements = []
        screenshot = self.capture_screen()
        
        # OCR na imagem
        ocr_data = pytesseract.image_to_data(screenshot, output_type=pytesseract.Output.DICT)
        
        # Procura pelo texto
        for i, word in enumerate(ocr_data['text']):
            if word and text.lower() in word.lower():
                conf = ocr_data['conf'][i] / 100.0
                if conf >= confidence:
                    x = ocr_data['left'][i]
                    y = ocr_data['top'][i]
                    w = ocr_data['width'][i]
                    h = ocr_data['height'][i]
                    
                    element = ScreenElement(
                        name=f"text_{text}",
                        type="text",
                        position=(x, y),
                        size=(w, h),
                        text=word,
                        confidence=conf
                    )
                    elements.append(element)
        
        return elements
    
    def find_buttons(self) -> List[ScreenElement]:
        """Detecta botões na tela usando heurísticas visuais"""
        if not CV2_AVAILABLE:
            return []
        
        elements = []
        screenshot = self.capture_screen()
        img_array = np.array(screenshot)
        
        # Converte para escala de cinza
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        
        # Detecção de bordas
        edges = cv2.Canny(gray, 50, 150)
        
        # Encontra contornos
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            # Calcula retângulo envolvente
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filtra por tamanho típico de botão
            if 50 < w < 300 and 20 < h < 100:
                # Verifica se parece um botão (retangular)
                aspect_ratio = w / h
                if 1.5 < aspect_ratio < 6:
                    # Extrai região para OCR
                    button_region = screenshot.crop((x, y, x+w, y+h))
                    
                    text = ""
                    if OCR_AVAILABLE:
                        try:
                            text = pytesseract.image_to_string(button_region).strip()
                        except:
                            pass
                    
                    element = ScreenElement(
                        name=f"button_{text or 'unknown'}",
                        type="button",
                        position=(x, y),
                        size=(w, h),
                        text=text,
                        confidence=0.7
                    )
                    elements.append(element)
        
        return elements
    
    def analyze_with_vision_ai(self, prompt: str, 
                              screenshot: Optional[Image.Image] = None) -> Dict[str, Any]:
        """
        Analisa tela usando GPT-4 Vision ou similar
        
        Args:
            prompt: Pergunta sobre a tela
            screenshot: Screenshot específico ou captura atual
            
        Returns:
            Análise da AI
        """
        if not self.gpt4_vision_key:
            return {"error": "GPT-4 Vision API key não configurada"}
        
        if screenshot is None:
            screenshot = self.capture_screen()
        
        # Converte imagem para base64
        buffered = io.BytesIO()
        screenshot.save(buffered, format="PNG")
        img_base64 = base64.b64encode(buffered.getvalue()).decode()
        
        # Chamada para GPT-4 Vision (exemplo)
        # NOTA: Substituir com implementação real da API
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.gpt4_vision_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4-vision-preview",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{img_base64}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 300
                }
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"API error: {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Erro ao chamar Vision AI: {e}")
            return {"error": str(e)}
    
    def find_window(self, title: str) -> Optional[ScreenElement]:
        """Encontra janela por título"""
        if not PYAUTOGUI_AVAILABLE:
            return None
        
        try:
            windows = gw.getWindowsWithTitle(title)
            if windows:
                window = windows[0]
                return ScreenElement(
                    name=f"window_{title}",
                    type="window",
                    position=(window.left, window.top),
                    size=(window.width, window.height),
                    text=title,
                    confidence=1.0
                )
        except Exception as e:
            logger.error(f"Erro ao buscar janela: {e}")
        
        return None


class PCController:
    """Controlador principal do PC"""
    
    def __init__(self, vision_analyzer: Optional[VisionAnalyzer] = None):
        """
        Inicializa o controlador
        
        Args:
            vision_analyzer: Analisador de visão (opcional)
        """
        self.vision = vision_analyzer or VisionAnalyzer()
        self.action_history = []
        self.recording = False
        self.recorded_actions = []
        
        if PYAUTOGUI_AVAILABLE:
            # Configurações de segurança
            self.screen_width, self.screen_height = pyautogui.size()
            logger.info(f"Tela detectada: {self.screen_width}x{self.screen_height}")
    
    def execute_action(self, action: ActionType, 
                       params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa uma ação no PC
        
        Args:
            action: Tipo de ação
            params: Parâmetros da ação
            
        Returns:
            Resultado da execução
        """
        if not PYAUTOGUI_AVAILABLE:
            return {"success": False, "error": "PyAutoGUI não disponível"}
        
        result = {"success": False, "action": action.value}
        
        try:
            if action == ActionType.CLICK:
                x = params.get('x')
                y = params.get('y')
                button = params.get('button', 'left')
                clicks = params.get('clicks', 1)
                
                if x is not None and y is not None:
                    pyautogui.click(x, y, button=button, clicks=clicks)
                    result["success"] = True
                    result["position"] = (x, y)
                    
            elif action == ActionType.DOUBLE_CLICK:
                x = params.get('x')
                y = params.get('y')
                
                if x is not None and y is not None:
                    pyautogui.doubleClick(x, y)
                    result["success"] = True
                    result["position"] = (x, y)
                    
            elif action == ActionType.RIGHT_CLICK:
                x = params.get('x')
                y = params.get('y')
                
                if x is not None and y is not None:
                    pyautogui.rightClick(x, y)
                    result["success"] = True
                    result["position"] = (x, y)
                    
            elif action == ActionType.TYPE:
                text = params.get('text', '')
                interval = params.get('interval', 0.05)
                
                pyautogui.typewrite(text, interval=interval)
                result["success"] = True
                result["text"] = text
                
            elif action == ActionType.HOTKEY:
                keys = params.get('keys', [])
                
                if keys:
                    pyautogui.hotkey(*keys)
                    result["success"] = True
                    result["keys"] = keys
                    
            elif action == ActionType.SCROLL:
                clicks = params.get('clicks', 1)
                x = params.get('x')
                y = params.get('y')
                
                if x and y:
                    pyautogui.moveTo(x, y)
                pyautogui.scroll(clicks)
                result["success"] = True
                result["scrolled"] = clicks
                
            elif action == ActionType.DRAG:
                start_x = params.get('start_x')
                start_y = params.get('start_y')
                end_x = params.get('end_x')
                end_y = params.get('end_y')
                duration = params.get('duration', 1.0)
                
                if all([start_x, start_y, end_x, end_y]):
                    pyautogui.dragTo(end_x, end_y, duration=duration, button='left')
                    result["success"] = True
                    result["dragged"] = f"({start_x},{start_y}) to ({end_x},{end_y})"
                    
            elif action == ActionType.SCREENSHOT:
                region = params.get('region')
                save_path = params.get('save_path')
                
                screenshot = pyautogui.screenshot(region=region)
                
                if save_path:
                    screenshot.save(save_path)
                    result["saved_to"] = save_path
                
                result["success"] = True
                result["screenshot"] = screenshot
                
            elif action == ActionType.MOVE:
                x = params.get('x')
                y = params.get('y')
                duration = params.get('duration', 0.5)
                
                if x is not None and y is not None:
                    pyautogui.moveTo(x, y, duration=duration)
                    result["success"] = True
                    result["position"] = (x, y)
                    
            elif action == ActionType.WAIT:
                seconds = params.get('seconds', 1)
                time.sleep(seconds)
                result["success"] = True
                result["waited"] = seconds
                
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Erro ao executar {action.value}: {e}")
        
        # Registra ação no histórico
        self.action_history.append({
            "timestamp": datetime.now().isoformat(),
            "action": action.value,
            "params": params,
            "result": result
        })
        
        # Se estiver gravando, adiciona à lista
        if self.recording:
            self.recorded_actions.append({
                "action": action,
                "params": params
            })
        
        return result
    
    def click_on_text(self, text: str) -> Dict[str, Any]:
        """Clica em texto visível na tela"""
        elements = self.vision.find_text_on_screen(text)
        
        if elements:
            # Clica no primeiro elemento encontrado
            element = elements[0]
            return self.execute_action(
                ActionType.CLICK,
                {'x': element.center[0], 'y': element.center[1]}
            )
        
        return {"success": False, "error": f"Texto '{text}' não encontrado"}
    
    def fill_form_field(self, field_label: str, value: str) -> Dict[str, Any]:
        """Preenche campo de formulário"""
        # Procura o label
        labels = self.vision.find_text_on_screen(field_label)
        
        if labels:
            label = labels[0]
            # Clica à direita do label (onde geralmente fica o campo)
            click_x = label.position[0] + label.size[0] + 20
            click_y = label.center[1]
            
            # Clica no campo
            self.execute_action(ActionType.CLICK, {'x': click_x, 'y': click_y})
            
            # Limpa campo (Ctrl+A, Delete)
            self.execute_action(ActionType.HOTKEY, {'keys': ['ctrl', 'a']})
            self.execute_action(ActionType.HOTKEY, {'keys': ['delete']})
            
            # Digita o valor
            return self.execute_action(ActionType.TYPE, {'text': value})
        
        return {"success": False, "error": f"Campo '{field_label}' não encontrado"}
    
    def automate_task(self, description: str) -> Dict[str, Any]:
        """
        Automatiza tarefa complexa usando AI para entender o que fazer
        
        Args:
            description: Descrição em linguagem natural da tarefa
            
        Returns:
            Resultado da automação
        """
        logger.info(f"Automatizando: {description}")
        
        # Analisa a tela atual
        analysis = self.vision.analyze_with_vision_ai(
            f"Como executar a seguinte tarefa: {description}? "
            "Liste os passos específicos com coordenadas ou elementos a clicar."
        )
        
        if "error" in analysis:
            return analysis
        
        # Parseia resposta e executa ações
        # (Implementação simplificada - expandir conforme necessário)
        steps_executed = []
        
        # Exemplo de interpretação de comandos comuns
        if "abrir" in description.lower():
            if "chrome" in description.lower():
                self.open_application("chrome")
                steps_executed.append("Abriu Chrome")
                
        elif "preencher" in description.lower() and "formulário" in description.lower():
            # Extrai campos do formulário da descrição
            # (implementação específica necessária)
            pass
        
        return {
            "success": True,
            "description": description,
            "steps_executed": steps_executed,
            "ai_analysis": analysis
        }
    
    def open_application(self, app_name: str) -> Dict[str, Any]:
        """Abre aplicação pelo nome"""
        # Windows
        if sys.platform == "win32":
            # Abre menu iniciar
            self.execute_action(ActionType.HOTKEY, {'keys': ['win']})
            time.sleep(0.5)
            
            # Digita nome do app
            self.execute_action(ActionType.TYPE, {'text': app_name})
            time.sleep(0.5)
            
            # Pressiona Enter
            self.execute_action(ActionType.HOTKEY, {'keys': ['enter']})
            
            return {"success": True, "opened": app_name}
        
        return {"success": False, "error": "Sistema não suportado"}
    
    def start_recording(self):
        """Inicia gravação de ações"""
        self.recording = True
        self.recorded_actions = []
        logger.info("Gravação iniciada")
    
    def stop_recording(self) -> List[Dict]:
        """Para gravação e retorna ações gravadas"""
        self.recording = False
        logger.info(f"Gravação parada. {len(self.recorded_actions)} ações gravadas")
        return self.recorded_actions
    
    def replay_recording(self, actions: List[Dict], speed: float = 1.0):
        """
        Reproduz ações gravadas
        
        Args:
            actions: Lista de ações gravadas
            speed: Velocidade de reprodução (1.0 = normal)
        """
        logger.info(f"Reproduzindo {len(actions)} ações...")
        
        for action_data in actions:
            action = action_data['action']
            params = action_data['params']
            
            # Executa ação
            self.execute_action(action, params)
            
            # Delay entre ações
            time.sleep(0.5 / speed)
        
        logger.info("Reprodução concluída")
    
    def smart_click(self, description: str) -> Dict[str, Any]:
        """
        Clique inteligente baseado em descrição
        
        Args:
            description: Ex: "botão verde de confirmar", "X para fechar"
        """
        # Usa AI para encontrar elemento
        analysis = self.vision.analyze_with_vision_ai(
            f"Onde está o seguinte elemento na tela: {description}? "
            "Retorne as coordenadas X,Y do centro do elemento."
        )
        
        # Extrai coordenadas da resposta
        # (Implementação depende do formato da resposta da AI)
        
        return {"success": False, "error": "Implementação pendente"}


class PrometheusVisionInterface:
    """Interface para integração com Prometheus"""
    
    def __init__(self, gpt4_vision_key: Optional[str] = None):
        """
        Inicializa interface de visão
        
        Args:
            gpt4_vision_key: Chave API para GPT-4 Vision
        """
        self.vision = VisionAnalyzer(gpt4_vision_key)
        self.controller = PCController(self.vision)
        
        # Comandos mapeados
        self.commands = {
            "click": self._handle_click,
            "type": self._handle_type,
            "screenshot": self._handle_screenshot,
            "find": self._handle_find,
            "open": self._handle_open,
            "fill": self._handle_fill,
            "automate": self._handle_automate,
            "record": self._handle_record,
            "replay": self._handle_replay
        }
        
        logger.info("Interface de visão inicializada")
    
    def process_visual_command(self, command: str) -> Dict[str, Any]:
        """
        Processa comando visual em linguagem natural
        
        Args:
            command: Comando em português
            
        Returns:
            Resultado da execução
        """
        command_lower = command.lower()
        
        # Identifica tipo de comando
        for cmd_type, handler in self.commands.items():
            if cmd_type in command_lower:
                return handler(command)
        
        # Se não identificou, tenta usar AI
        return self.controller.automate_task(command)
    
    def _handle_click(self, command: str) -> Dict[str, Any]:
        """Processa comando de clique"""
        # Extrai o que clicar
        patterns = [
            r"clicar? (?:em |no |na |o |a )?(.+)",
            r"clique (?:em |no |na |o |a )?(.+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, command.lower())
            if match:
                target = match.group(1).strip()
                
                # Tenta clicar em texto
                result = self.controller.click_on_text(target)
                
                if result["success"]:
                    return result
                
                # Se falhou, tenta descrição inteligente
                return self.controller.smart_click(target)
        
        return {"success": False, "error": "Não entendi onde clicar"}
    
    def _handle_type(self, command: str) -> Dict[str, Any]:
        """Processa comando de digitação"""
        # Extrai texto entre aspas ou após "digitar"
        patterns = [
            r'digitar? ["\'](.+)["\']',
            r'escrever? ["\'](.+)["\']',
            r'digitar? (.+)',
            r'escrever? (.+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, command.lower())
            if match:
                text = match.group(1).strip()
                return self.controller.execute_action(
                    ActionType.TYPE,
                    {'text': text}
                )
        
        return {"success": False, "error": "Não entendi o que digitar"}
    
    def _handle_screenshot(self, command: str) -> Dict[str, Any]:
        """Processa comando de screenshot"""
        save_path = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        # Verifica se tem região específica
        if "tela toda" in command.lower() or "tela inteira" in command.lower():
            region = None
        else:
            region = None  # Por padrão captura tudo
        
        result = self.controller.execute_action(
            ActionType.SCREENSHOT,
            {'region': region, 'save_path': save_path}
        )
        
        if result["success"]:
            result["message"] = f"Screenshot salvo em {save_path}"
        
        return result
    
    def _handle_find(self, command: str) -> Dict[str, Any]:
        """Processa comando de busca"""
        # Extrai o que procurar
        patterns = [
            r"encontrar? (.+)",
            r"procurar? (.+)",
            r"buscar? (.+)",
            r"localizar? (.+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, command.lower())
            if match:
                target = match.group(1).strip()
                elements = self.vision.find_text_on_screen(target)
                
                return {
                    "success": len(elements) > 0,
                    "found": len(elements),
                    "elements": [
                        {
                            "text": e.text,
                            "position": e.position,
                            "confidence": e.confidence
                        }
                        for e in elements[:5]  # Limita a 5 resultados
                    ]
                }
        
        return {"success": False, "error": "Não entendi o que procurar"}
    
    def _handle_open(self, command: str) -> Dict[str, Any]:
        """Processa comando de abrir aplicação"""
        # Extrai nome da aplicação
        patterns = [
            r"abrir? (.+)",
            r"iniciar? (.+)",
            r"executar? (.+)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, command.lower())
            if match:
                app = match.group(1).strip()
                
                # Remove artigos
                app = re.sub(r'^(o |a |um |uma )', '', app)
                
                return self.controller.open_application(app)
        
        return {"success": False, "error": "Não entendi qual aplicação abrir"}
    
    def _handle_fill(self, command: str) -> Dict[str, Any]:
        """Processa comando de preencher formulário"""
        # Extrai campo e valor
        pattern = r"preencher? (?:o |a )?campo ['\"]?(.+?)['\"]? com ['\"]?(.+)['\"]?"
        match = re.search(pattern, command.lower())
        
        if match:
            field = match.group(1).strip()
            value = match.group(2).strip()
            
            return self.controller.fill_form_field(field, value)
        
        return {"success": False, "error": "Não entendi o campo e valor"}
    
    def _handle_automate(self, command: str) -> Dict[str, Any]:
        """Processa comando de automação complexa"""
        # Remove palavra "automatizar"
        task = re.sub(r'automatizar? ', '', command.lower()).strip()
        
        return self.controller.automate_task(task)
    
    def _handle_record(self, command: str) -> Dict[str, Any]:
        """Processa comando de gravação"""
        if "parar" in command.lower() or "stop" in command.lower():
            actions = self.controller.stop_recording()
            return {
                "success": True,
                "message": f"Gravação parada. {len(actions)} ações gravadas",
                "actions": actions
            }
        else:
            self.controller.start_recording()
            return {
                "success": True,
                "message": "Gravação iniciada. Execute as ações e depois diga 'parar gravação'"
            }
    
    def _handle_replay(self, command: str) -> Dict[str, Any]:
        """Processa comando de replay"""
        if self.controller.recorded_actions:
            self.controller.replay_recording(self.controller.recorded_actions)
            return {
                "success": True,
                "message": f"Reproduzidas {len(self.controller.recorded_actions)} ações"
            }
        else:
            return {
                "success": False,
                "error": "Nenhuma gravação disponível"
            }
    
    def describe_screen(self) -> str:
        """Descreve o que está na tela usando AI"""
        analysis = self.vision.analyze_with_vision_ai(
            "Descreva o que está visível na tela de forma concisa. "
            "Identifique aplicações abertas, janelas, botões importantes."
        )
        
        if "error" in analysis:
            return f"Erro ao analisar tela: {analysis['error']}"
        
        # Extrai descrição da resposta
        # (Formato depende da API)
        return "Análise da tela disponível"


if __name__ == "__main__":
    print("👁️ Testando Sistema de Visão e Controle Prometheus...")
    
    # Inicializa interface
    vision_interface = PrometheusVisionInterface()
    
    # Testes básicos
    print("\n📸 Capturando screenshot...")
    result = vision_interface.process_visual_command("tirar screenshot da tela toda")
    print(f"  Resultado: {result}")
    
    if PYAUTOGUI_AVAILABLE:
        print("\n🖱️ Posição atual do mouse:")
        x, y = pyautogui.position()
        print(f"  X: {x}, Y: {y}")
        
        print("\n📊 Tamanho da tela:")
        width, height = pyautogui.size()
        print(f"  {width} x {height} pixels")
    
    print("\n🔍 Comandos disponíveis:")
    print("  - clicar em [texto/elemento]")
    print("  - digitar [texto]")
    print("  - tirar screenshot")
    print("  - encontrar [texto]")
    print("  - abrir [aplicação]")
    print("  - preencher campo [nome] com [valor]")
    print("  - automatizar [descrição da tarefa]")
    print("  - iniciar gravação / parar gravação")
    print("  - reproduzir gravação")
    
    print("\n✅ Sistema de Visão e Controle pronto!")
