"""
Prometheus Brain - Core Intelligence System
Cérebro central que coordena todas as skills e processa comandos
"""

import os
import re
import importlib
from typing import Dict, Any, Optional
from skills.logs import setup_logger

logger = setup_logger(__name__, "./logs/prometheus.log")


class PrometheusCore:
    """
    Classe principal que coordena todas as skills do Prometheus
    """

    def __init__(self):
        """Inicializa o cérebro do Prometheus"""
        self.skills = {}
        self.running = False
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
                "memory_system"
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

            # AI Router
            elif any(word in command_lower for word in ["perguntar", "ai", "ia", "claude", "gpt"]):
                task_type = self._detect_task_type(command)
                return self.route_to_skill("ai_router", {
                    "action": "route",
                    "prompt": command,
                    "task_type": task_type
                })

            # Vision Control
            elif any(word in command_lower for word in ["clicar", "click", "digitar", "type", "screenshot", "tela", "screen", "encontrar", "find", "botao", "button"]):
                return self.route_to_skill("vision_control", {
                    "action": "process_command",
                    "command": command
                })

            # Always-On Voice
            elif any(word in command_lower for word in ["voz", "voice", "escutar", "listen", "transcricao", "transcription", "reuniao", "meeting"]):
                return self.route_to_skill("always_on_voice", {
                    "action": "process_command",
                    "command": command
                })

            # Memory System
            elif any(word in command_lower for word in ["lembrar", "remember", "memoria", "memory", "aprender", "learn", "relembrar", "recall", "padroes", "patterns"]):
                return self.route_to_skill("memory_system", {
                    "action": "process_command",
                    "command": command
                })

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
