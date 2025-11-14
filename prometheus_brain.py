"""
Prometheus Brain - Core Intelligence System
Cérebro central que coordena todas as skills e processa comandos
"""

import os
import re
import importlib
import yaml
from typing import Dict, Any, Optional, List
from pathlib import Path
from skills.logs import setup_logger

logger = setup_logger(__name__, "./logs/prometheus.log")

# Try to import new skills interfaces
try:
    from skills.memory_system import PrometheusMemoryInterface
    MEMORY_AVAILABLE = True
except ImportError as e:
    MEMORY_AVAILABLE = False
    logger.warning(f"Memory System não disponível: {e}")

try:
    from skills.vision_control import PrometheusVisionInterface
    VISION_AVAILABLE = True
except ImportError as e:
    VISION_AVAILABLE = False
    logger.warning(f"Vision Control não disponível: {e}")

try:
    from skills.browser_control import PrometheusBrowserInterface
    BROWSER_AVAILABLE = True
except ImportError as e:
    BROWSER_AVAILABLE = False
    logger.warning(f"Browser Control não disponível: {e}")

try:
    from skills.ai_master_router import PrometheusAIInterface
    AI_MASTER_AVAILABLE = True
except ImportError as e:
    AI_MASTER_AVAILABLE = False
    logger.warning(f"AI Master Router não disponível: {e}")


class PrometheusCore:
    """
    Classe principal que coordena todas as skills do Prometheus
    """

    def __init__(self):
        """Inicializa o cérebro do Prometheus"""
        self.skills = {}
        self.running = False
        self.config = self._load_config()

        # Initialize memory interface
        self.memory = None
        if MEMORY_AVAILABLE:
            try:
                self.memory = PrometheusMemoryInterface()
                logger.info("Memory System interface inicializada")
            except Exception as e:
                logger.error(f"Erro ao inicializar Memory System: {e}")

        # Initialize vision interface
        self.vision = None
        if VISION_AVAILABLE:
            try:
                self.vision = PrometheusVisionInterface()
                logger.info("Vision Control interface inicializada")
            except Exception as e:
                logger.error(f"Erro ao inicializar Vision Control: {e}")

        # Initialize browser interface
        self.browser = None
        if BROWSER_AVAILABLE:
            try:
                self.browser = PrometheusBrowserInterface()
                logger.info("Browser Control interface inicializada")
            except Exception as e:
                logger.error(f"Erro ao inicializar Browser Control: {e}")

        # Initialize AI Master Router
        self.ai_master = None
        if AI_MASTER_AVAILABLE:
            try:
                self.ai_master = PrometheusAIInterface()
                logger.info("AI Master Router interface inicializada")
            except Exception as e:
                logger.error(f"Erro ao inicializar AI Master Router: {e}")

        logger.info("PrometheusCore inicializado")

    def start(self):
        """Inicia o sistema Prometheus"""
        try:
            logger.info("=" * 60)
            logger.info("PROMETHEUS MODO ABSOLUTO - INICIANDO")
            logger.info("=" * 60)

            # Carregar todas as skills
            self.load_skills()

            self.running = True
            logger.info("Prometheus está ONLINE e pronto para receber comandos")

            return {"success": True, "message": "Prometheus iniciado com sucesso"}

        except Exception as e:
            logger.error(f"Erro ao iniciar Prometheus: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def load_skills(self):
        """Carrega todos os módulos da pasta skills/"""
        try:
            logger.info("Carregando skills...")

            skills_to_load = [
                "system_control",
                "n8n_client",
                "whatsapp_api",
                "rdstation_client",
                "supabase_sync",
                "google_services",
                "ai_router",
                "vision_control",
                "always_on_voice",
                "memory_system",
                "browser_control",
                "ai_master_router"
            ]

            for skill_name in skills_to_load:
                try:
                    module = importlib.import_module(f"skills.{skill_name}")
                    self.skills[skill_name] = module
                    logger.info(f"✓ Skill '{skill_name}' carregada")
                except Exception as e:
                    logger.error(f"✗ Erro ao carregar skill '{skill_name}': {e}", exc_info=True)

            logger.info(f"Total de skills carregadas: {len(self.skills)}")

        except Exception as e:
            logger.error(f"Erro ao carregar skills: {e}", exc_info=True)

    def handle_text_command(self, command: str) -> Dict[str, Any]:
        """
        Processa comando de texto e roteia para a skill apropriada

        Args:
            command: Comando em linguagem natural

        Returns:
            Dict com resultado da execução
        """
        try:
            logger.info(f"Processando comando: {command}")

            command_lower = command.lower().strip()

            # Buscar contexto na memória (se disponível)
            memory_context = self._get_memory_context(command)
            if memory_context:
                logger.info(f"Contexto da memória: {len(memory_context)} memórias relevantes encontradas")

            # Detectar intenção e rotear para skill apropriada

            # Sistema e arquivos
            if any(word in command_lower for word in ["listar", "arquivos", "pasta", "diretorio"]):
                path = self._extract_path(command) or "."
                return self.route_to_skill("system_control", {
                    "action": "list_files",
                    "path": path
                })

            elif any(word in command_lower for word in ["abrir pasta", "open folder", "explorador"]):
                path = self._extract_path(command) or "."
                return self.route_to_skill("system_control", {
                    "action": "open_folder",
                    "path": path
                })

            elif any(word in command_lower for word in ["organizar downloads", "organize downloads"]):
                return self.route_to_skill("system_control", {
                    "action": "organize_downloads"
                })

            elif any(word in command_lower for word in ["executar", "rodar", "run command"]):
                cmd = self._extract_command(command)
                return self.route_to_skill("system_control", {
                    "action": "run_command",
                    "command": cmd
                })

            # n8n workflows
            elif any(word in command_lower for word in ["n8n", "workflow", "automation"]):
                if "status" in command_lower or "health" in command_lower:
                    return self.route_to_skill("n8n_client", {
                        "action": "check_health"
                    })
                elif "listar" in command_lower or "list" in command_lower:
                    return self.route_to_skill("n8n_client", {
                        "action": "list_workflows"
                    })
                else:
                    return self.route_to_skill("n8n_client", {
                        "action": "trigger_workflow",
                        "payload": {"command": command}
                    })

            # WhatsApp
            elif any(word in command_lower for word in ["whatsapp", "enviar mensagem", "send message"]):
                phone = self._extract_phone(command)
                message = self._extract_message(command)
                return self.route_to_skill("whatsapp_api", {
                    "action": "send_message",
                    "phone": phone,
                    "message": message
                })

            # RD Station
            elif any(word in command_lower for word in ["rdstation", "lead", "crm"]):
                if "criar" in command_lower or "create" in command_lower:
                    email = self._extract_email(command)
                    return self.route_to_skill("rdstation_client", {
                        "action": "create_lead",
                        "email": email
                    })
                elif "buscar" in command_lower or "get" in command_lower:
                    email = self._extract_email(command)
                    return self.route_to_skill("rdstation_client", {
                        "action": "get_lead",
                        "email": email
                    })

            # Supabase
            elif any(word in command_lower for word in ["supabase", "database", "banco"]):
                if "inserir" in command_lower or "insert" in command_lower:
                    return self.route_to_skill("supabase_sync", {
                        "action": "insert",
                        "table": "events",
                        "data": {"command": command}
                    })
                elif "consultar" in command_lower or "query" in command_lower:
                    return self.route_to_skill("supabase_sync", {
                        "action": "query",
                        "table": "events"
                    })

            # Google Services
            elif any(word in command_lower for word in ["google", "calendar", "gmail", "drive"]):
                if "calendario" in command_lower or "calendar" in command_lower:
                    return self.route_to_skill("google_services", {
                        "action": "create_event",
                        "summary": command
                    })
                elif "email" in command_lower or "gmail" in command_lower:
                    email = self._extract_email(command)
                    return self.route_to_skill("google_services", {
                        "action": "send_email",
                        "to": email,
                        "subject": "Prometheus",
                        "body": command
                    })

            # AI Master Router (novo sistema inteligente)
            elif any(word in command_lower for word in ["perguntar", "ai", "ia", "claude", "gpt", "gemini", "questao", "duvida"]):
                return self._handle_ai_command(command)

            # Vision Control
            elif any(word in command_lower for word in ["clicar", "click", "digitar", "type", "screenshot", "tela", "screen", "encontrar", "find", "botao", "button"]):
                return self._handle_vision_command(command)

            # Always-On Voice
            elif any(word in command_lower for word in ["voz", "voice", "escutar", "listen", "transcricao", "transcription", "reuniao", "meeting"]):
                return self.route_to_skill("always_on_voice", {
                    "action": "process_command",
                    "command": command
                })

            # Memory System
            elif any(word in command_lower for word in ["lembrar", "remember", "memoria", "memory", "aprender", "learn", "relembrar", "recall", "padroes", "patterns", "esquecer", "forget"]):
                result = self._handle_memory_command(command)

                # Save command/response pair to memory (if memory is available)
                if self.memory and result.get("success"):
                    try:
                        self.memory.process_command(f"lembrar comando '{command}' resultou em '{result}'")
                    except:
                        pass

                return result

            # Browser Control
            elif any(word in command_lower for word in ["abrir", "navegar", "acessar", "site", "pesquisar google", "buscar google", "browser", "navegador", "web"]):
                return self._handle_browser_command(command)

            # Status e testes
            elif command_lower in ["status", "test", "teste"]:
                return self.test_all_connections()

            else:
                logger.warning(f"Comando não reconhecido: {command}")
                return {
                    "success": False,
                    "error": "Comando não reconhecido",
                    "suggestion": "Tente comandos como: 'listar arquivos', 'status n8n', 'organizar downloads'"
                }

        except Exception as e:
            logger.error(f"Erro ao processar comando: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def route_to_skill(self, skill_name: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Roteia comando para a skill específica

        Args:
            skill_name: Nome da skill a ser executada
            payload: Dados para a skill

        Returns:
            Dict com resultado da skill
        """
        try:
            logger.info(f"Roteando para skill: {skill_name}")

            if skill_name not in self.skills:
                logger.error(f"Skill '{skill_name}' não encontrada")
                return {"success": False, "error": f"Skill '{skill_name}' não disponível"}

            skill = self.skills[skill_name]
            action = payload.get("action", "")

            # Rotear para função apropriada da skill
            if skill_name == "system_control":
                if action == "list_files":
                    return skill.list_files(payload.get("path", "."))
                elif action == "open_folder":
                    return skill.open_folder(payload.get("path", "."))
                elif action == "organize_downloads":
                    return skill.organize_downloads()
                elif action == "run_command":
                    return skill.run_command(payload.get("command", ""))

            elif skill_name == "n8n_client":
                if action == "check_health":
                    return skill.check_n8n_health()
                elif action == "list_workflows":
                    return skill.get_workflows_list()
                elif action == "trigger_workflow":
                    return skill.trigger_workflow(payload=payload.get("payload"))

            elif skill_name == "whatsapp_api":
                if action == "send_message":
                    return skill.send_text_message(
                        payload.get("phone", ""),
                        payload.get("message", "")
                    )

            elif skill_name == "rdstation_client":
                if action == "create_lead":
                    return skill.create_or_update_lead(payload.get("email", ""))
                elif action == "get_lead":
                    return skill.get_lead(payload.get("email", ""))
                elif action == "test":
                    return skill.test_connection()

            elif skill_name == "supabase_sync":
                if action == "insert":
                    return skill.insert_event(
                        payload.get("table", "events"),
                        payload.get("data", {})
                    )
                elif action == "query":
                    return skill.query_table(payload.get("table", "events"))
                elif action == "test":
                    return skill.test_connection()

            elif skill_name == "google_services":
                if action == "create_event":
                    return skill.create_calendar_event(payload.get("summary", ""))
                elif action == "send_email":
                    return skill.send_gmail(
                        payload.get("to", ""),
                        payload.get("subject", ""),
                        payload.get("body", "")
                    )
                elif action == "test":
                    return skill.test_connection()

            elif skill_name == "ai_router":
                if action == "route":
                    return skill.route_to_best_model(
                        payload.get("prompt", ""),
                        payload.get("task_type", "general")
                    )

            elif skill_name == "vision_control":
                if action == "process_command":
                    # Usar a interface do Prometheus
                    interface = skill.PrometheusVisionInterface()
                    return interface.process_command(payload.get("command", ""))

            elif skill_name == "always_on_voice":
                if action == "process_command":
                    # Usar a interface do Prometheus
                    interface = skill.PrometheusVoiceInterface()
                    return interface.process_command(payload.get("command", ""))

            elif skill_name == "memory_system":
                if action == "process_command":
                    # Usar a interface do Prometheus
                    interface = skill.PrometheusMemoryInterface()
                    return interface.process_command(payload.get("command", ""))

            logger.warning(f"Ação '{action}' não implementada para skill '{skill_name}'")
            return {"success": False, "error": f"Ação '{action}' não implementada"}

        except Exception as e:
            logger.error(f"Erro ao rotear para skill: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    def test_all_connections(self) -> Dict[str, Any]:
        """Testa conexão com todos os serviços externos"""
        logger.info("Testando todas as conexões...")

        results = {}

        # Testar n8n
        if "n8n_client" in self.skills:
            results["n8n"] = self.skills["n8n_client"].check_n8n_health()

        # Testar RD Station
        if "rdstation_client" in self.skills:
            results["rdstation"] = self.skills["rdstation_client"].test_connection()

        # Testar Supabase
        if "supabase_sync" in self.skills:
            results["supabase"] = self.skills["supabase_sync"].test_connection()

        # Testar Google
        if "google_services" in self.skills:
            results["google"] = self.skills["google_services"].test_connection()

        return {
            "success": True,
            "tests": results
        }

    def _load_config(self) -> Dict[str, Any]:
        """Carrega configuração do arquivo config.yaml"""
        config_path = Path("config/config.yaml")

        if not config_path.exists():
            logger.warning(f"Arquivo de config não encontrado: {config_path}")
            return {}

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                logger.info("Configuração carregada de config.yaml")
                return config or {}
        except Exception as e:
            logger.error(f"Erro ao carregar config: {e}")
            return {}

    def _get_memory_context(self, command: str, limit: int = 3) -> List[Dict]:
        """
        Busca contexto relevante na memória para o comando

        Args:
            command: Comando atual
            limit: Número máximo de memórias a retornar

        Returns:
            Lista de memórias relevantes
        """
        if not self.memory:
            return []

        try:
            result = self.memory.process_command(f"relembrar sobre {command}")
            if result.get("success") and result.get("memories"):
                return result["memories"][:limit]
        except Exception as e:
            logger.error(f"Erro ao buscar contexto na memória: {e}")

        return []

    def _handle_memory_command(self, command: str) -> Dict[str, Any]:
        """
        Processa comandos relacionados à memória

        Args:
            command: Comando em linguagem natural

        Returns:
            Resultado da operação
        """
        if not self.memory:
            return {"success": False, "error": "Memory System não disponível"}

        try:
            return self.memory.process_command(command)
        except Exception as e:
            logger.error(f"Erro ao processar comando de memória: {e}")
            return {"success": False, "error": str(e)}

    def _handle_vision_command(self, command: str) -> Dict[str, Any]:
        """
        Processa comandos relacionados à visão/tela

        Args:
            command: Comando em linguagem natural

        Returns:
            Resultado da operação
        """
        if not self.vision:
            return {"success": False, "error": "Vision Control não disponível"}

        try:
            return self.vision.process_command(command)
        except Exception as e:
            logger.error(f"Erro ao processar comando de visão: {e}")
            return {"success": False, "error": str(e)}

    def _handle_browser_command(self, command: str) -> Dict[str, Any]:
        """
        Processa comandos relacionados ao navegador

        Args:
            command: Comando em linguagem natural

        Returns:
            Resultado da operação
        """
        if not self.browser:
            return {"success": False, "error": "Browser Control não disponível"}

        try:
            return self.browser.process_command(command)
        except Exception as e:
            logger.error(f"Erro ao processar comando de navegador: {e}")
            return {"success": False, "error": str(e)}

    def _handle_ai_command(self, command: str) -> Dict[str, Any]:
        """
        Processa comandos de IA usando AI Master Router

        Args:
            command: Comando/pergunta em linguagem natural

        Returns:
            Resposta da IA
        """
        if not self.ai_master:
            return {"success": False, "error": "AI Master Router não disponível"}

        try:
            # Usar memória para contexto (se disponível)
            context = self._get_memory_context(command, limit=2)

            # Processar com AI Master Router
            result = self.ai_master.process_command(command)

            # Salvar na memória (se disponível e sucesso)
            if self.memory and result.get("success"):
                try:
                    response_text = result.get("response", "")[:200]  # Primeiros 200 chars
                    self.memory.process_command(f"lembrar pergunta '{command}' = resposta '{response_text}'")
                except:
                    pass

            return result

        except Exception as e:
            logger.error(f"Erro ao processar comando de IA: {e}")
            return {"success": False, "error": str(e)}

    # Funções auxiliares para extrair informações de comandos

    def _extract_path(self, command: str) -> Optional[str]:
        """Extrai caminho de arquivo/pasta do comando"""
        # Procurar por caminhos Windows ou Linux
        path_pattern = r'[A-Za-z]:\\[\w\\\s\.\-]+|/[\w/\s\.\-]+'
        match = re.search(path_pattern, command)
        return match.group(0) if match else None

    def _extract_command(self, command: str) -> str:
        """Extrai comando a ser executado"""
        # Procurar por aspas ou depois de "executar"
        if '"' in command:
            match = re.search(r'"([^"]+)"', command)
            return match.group(1) if match else command
        return command

    def _extract_phone(self, command: str) -> str:
        """Extrai número de telefone do comando"""
        # Procurar por padrão de telefone brasileiro
        phone_pattern = r'55\d{10,11}|\d{10,11}'
        match = re.search(phone_pattern, command)
        return match.group(0) if match else ""

    def _extract_email(self, command: str) -> str:
        """Extrai email do comando"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, command)
        return match.group(0) if match else ""

    def _extract_message(self, command: str) -> str:
        """Extrai mensagem entre aspas"""
        if '"' in command:
            match = re.search(r'"([^"]+)"', command)
            return match.group(1) if match else command
        return command

    def _detect_task_type(self, command: str) -> str:
        """Detecta tipo de tarefa para roteamento de AI"""
        command_lower = command.lower()

        if any(word in command_lower for word in ["codigo", "code", "programar", "bug"]):
            return "code"
        elif any(word in command_lower for word in ["criativo", "creative", "historia", "escrever"]):
            return "creative"
        elif any(word in command_lower for word in ["analisar", "analyze", "dados", "data"]):
            return "analysis"
        elif any(word in command_lower for word in ["buscar", "search", "pesquisar"]):
            return "search"
        else:
            return "general"

    def stop(self):
        """Para o sistema Prometheus"""
        logger.info("Parando Prometheus...")
        self.running = False
        logger.info("Prometheus desligado")
