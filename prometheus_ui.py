"""
PROMETHEUS MODO ABSOLUTO - Interface Gráfica
Interface gráfica moderna usando CustomTkinter para controle do Prometheus
"""

import os
import sys
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# CustomTkinter for modern UI
try:
    import customtkinter as ctk
    from tkinter import scrolledtext
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False
    print("CustomTkinter não instalado. Instale com: pip install customtkinter")
    sys.exit(1)

# Prometheus Brain
from prometheus_brain import PrometheusCore


class PrometheusUI:
    """
    Interface gráfica principal do Prometheus
    """

    def __init__(self):
        """Inicializa a UI"""
        # Configurar tema
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # Criar janela principal
        self.root = ctk.CTk()
        self.root.title("PROMETHEUS MODO ABSOLUTO v2.1")
        self.root.geometry("1400x900")

        # Inicializar Prometheus Core
        self.prometheus = None
        self.running = False
        self.command_history = []
        self.history_index = -1

        # Criar interface
        self._create_ui()

        # Inicializar Prometheus em thread separada
        self._init_prometheus()

    def _create_ui(self):
        """Cria todos os elementos da interface"""

        # Grid layout
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # Sidebar esquerda
        self._create_sidebar()

        # Frame principal
        self._create_main_frame()

        # Frame de status na parte inferior
        self._create_status_frame()

    def _create_sidebar(self):
        """Cria barra lateral com informações do sistema"""
        self.sidebar = ctk.CTkFrame(self.root, width=300, corner_radius=0)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar.grid_rowconfigure(10, weight=1)

        # Logo/Título
        title = ctk.CTkLabel(
            self.sidebar,
            text="PROMETHEUS\nMODO ABSOLUTO",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title.grid(row=0, column=0, padx=20, pady=(20, 10))

        version = ctk.CTkLabel(
            self.sidebar,
            text="v2.1 - AI Powered Assistant",
            font=ctk.CTkFont(size=12)
        )
        version.grid(row=1, column=0, padx=20, pady=(0, 20))

        # Status do sistema
        self.status_label = ctk.CTkLabel(
            self.sidebar,
            text="Status: Inicializando...",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="orange"
        )
        self.status_label.grid(row=2, column=0, padx=20, pady=10)

        # Skills carregadas
        skills_label = ctk.CTkLabel(
            self.sidebar,
            text="Skills Carregadas:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        skills_label.grid(row=3, column=0, padx=20, pady=(20, 5))

        # Lista de skills
        self.skills_text = ctk.CTkTextbox(
            self.sidebar,
            height=250,
            width=260,
            font=ctk.CTkFont(size=11)
        )
        self.skills_text.grid(row=4, column=0, padx=20, pady=5)
        self.skills_text.insert("1.0", "Carregando skills...")
        self.skills_text.configure(state="disabled")

        # Ações rápidas
        quick_actions_label = ctk.CTkLabel(
            self.sidebar,
            text="Ações Rápidas:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        quick_actions_label.grid(row=5, column=0, padx=20, pady=(20, 10))

        # Botões de ação
        btn_memory = ctk.CTkButton(
            self.sidebar,
            text="Ver Memórias",
            command=self._view_memories,
            width=260
        )
        btn_memory.grid(row=6, column=0, padx=20, pady=5)

        btn_screenshot = ctk.CTkButton(
            self.sidebar,
            text="Screenshot",
            command=lambda: self._quick_command("tirar screenshot"),
            width=260
        )
        btn_screenshot.grid(row=7, column=0, padx=20, pady=5)

        btn_browser = ctk.CTkButton(
            self.sidebar,
            text="Abrir Google",
            command=lambda: self._quick_command("abrir google.com"),
            width=260
        )
        btn_browser.grid(row=8, column=0, padx=20, pady=5)

        btn_clear = ctk.CTkButton(
            self.sidebar,
            text="Limpar Console",
            command=self._clear_output,
            width=260,
            fg_color="gray40",
            hover_color="gray30"
        )
        btn_clear.grid(row=9, column=0, padx=20, pady=5)

    def _create_main_frame(self):
        """Cria frame principal com console e input"""
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Console de output
        console_label = ctk.CTkLabel(
            self.main_frame,
            text="Console de Comandos",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        console_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")

        self.output_text = ctk.CTkTextbox(
            self.main_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            wrap="word"
        )
        self.output_text.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.output_text.configure(state="disabled")

        # Frame de input
        input_frame = ctk.CTkFrame(self.main_frame)
        input_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        input_frame.grid_columnconfigure(0, weight=1)

        # Campo de comando
        self.command_entry = ctk.CTkEntry(
            input_frame,
            placeholder_text="Digite seu comando aqui... (Ex: 'pesquisar Python no Google', 'lembrar reuniao', 'abrir site')",
            font=ctk.CTkFont(size=14),
            height=40
        )
        self.command_entry.grid(row=0, column=0, padx=(0, 10), pady=5, sticky="ew")
        self.command_entry.bind("<Return>", lambda e: self._send_command())
        self.command_entry.bind("<Up>", self._history_up)
        self.command_entry.bind("<Down>", self._history_down)

        # Botão enviar
        self.send_button = ctk.CTkButton(
            input_frame,
            text="Enviar",
            command=self._send_command,
            width=100,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.send_button.grid(row=0, column=1, pady=5)

    def _create_status_frame(self):
        """Cria barra de status na parte inferior"""
        self.status_frame = ctk.CTkFrame(self.root, height=30)
        self.status_frame.grid(row=1, column=1, padx=20, pady=(0, 20), sticky="ew")

        self.status_info = ctk.CTkLabel(
            self.status_frame,
            text="Pronto | 0 comandos executados",
            font=ctk.CTkFont(size=11)
        )
        self.status_info.pack(side="left", padx=10, pady=5)

        self.time_label = ctk.CTkLabel(
            self.status_frame,
            text=datetime.now().strftime("%H:%M:%S"),
            font=ctk.CTkFont(size=11)
        )
        self.time_label.pack(side="right", padx=10, pady=5)

        # Atualizar relógio
        self._update_clock()

    def _init_prometheus(self):
        """Inicializa Prometheus Core em background"""
        def init():
            try:
                self._log("Inicializando Prometheus Core...", "system")
                self.prometheus = PrometheusCore()
                self.prometheus.start()
                self.running = True

                # Atualizar UI
                self.root.after(100, self._update_skills_list)
                self.root.after(100, lambda: self._update_status("ONLINE", "green"))
                self._log("Prometheus está ONLINE e pronto!", "success")
                self._log("Digite comandos ou use os botões de ação rápida.", "info")

            except Exception as e:
                self._log(f"Erro ao inicializar: {e}", "error")
                self.root.after(100, lambda: self._update_status("ERRO", "red"))

        thread = threading.Thread(target=init, daemon=True)
        thread.start()

    def _send_command(self):
        """Envia comando para o Prometheus"""
        command = self.command_entry.get().strip()

        if not command:
            return

        if not self.running or not self.prometheus:
            self._log("Prometheus ainda não está pronto. Aguarde...", "warning")
            return

        # Adicionar ao histórico
        self.command_history.append(command)
        self.history_index = len(self.command_history)

        # Limpar input
        self.command_entry.delete(0, "end")

        # Log comando
        self._log(f"[VOCÊ] {command}", "command")

        # Processar em thread separada
        def process():
            try:
                result = self.prometheus.process_command(command)
                self.root.after(100, lambda: self._handle_result(result))
            except Exception as e:
                self.root.after(100, lambda: self._log(f"Erro: {e}", "error"))

        thread = threading.Thread(target=process, daemon=True)
        thread.start()

    def _quick_command(self, command: str):
        """Executa comando rápido"""
        self.command_entry.delete(0, "end")
        self.command_entry.insert(0, command)
        self._send_command()

    def _handle_result(self, result: Dict[str, Any]):
        """Processa resultado do comando"""
        if result.get("success"):
            # Diferentes tipos de resposta
            if "response" in result:
                # Resposta de IA
                self._log(f"[PROMETHEUS] {result['response']}", "response")
                if "model" in result:
                    self._log(f"[Modelo usado: {result['model']}]", "info")

            elif "message" in result:
                self._log(f"[PROMETHEUS] {result['message']}", "response")

            elif "memories" in result:
                # Resultado de memória
                memories = result["memories"]
                self._log(f"[PROMETHEUS] Encontradas {len(memories)} memórias:", "response")
                for i, mem in enumerate(memories[:5], 1):
                    content = mem.get("content", "")[:100]
                    self._log(f"  {i}. {content}...", "info")

            elif "text" in result:
                # Texto extraído
                self._log(f"[PROMETHEUS] Texto: {result['text']}", "response")

            elif "path" in result:
                # Caminho de arquivo (screenshot, etc)
                self._log(f"[PROMETHEUS] Salvo em: {result['path']}", "response")

            elif "url" in result:
                # URL de navegação
                self._log(f"[PROMETHEUS] Navegado para: {result['url']}", "response")
                if "title" in result:
                    self._log(f"  Título: {result['title']}", "info")

            else:
                # Resultado genérico
                self._log(f"[PROMETHEUS] {result}", "response")

        else:
            error = result.get("error", "Erro desconhecido")
            self._log(f"[ERRO] {error}", "error")

            if "suggestion" in result:
                self._log(f"  Sugestão: {result['suggestion']}", "info")

    def _view_memories(self):
        """Visualiza memórias recentes"""
        if not self.running or not self.prometheus:
            self._log("Prometheus ainda não está pronto.", "warning")
            return

        self._log("[SISTEMA] Buscando memórias recentes...", "system")

        def fetch():
            try:
                if self.prometheus.memory:
                    result = self.prometheus.memory.process_command("listar memorias recentes")
                    self.root.after(100, lambda: self._handle_result(result))
                else:
                    self.root.after(100, lambda: self._log("Sistema de memória não disponível", "warning"))
            except Exception as e:
                self.root.after(100, lambda: self._log(f"Erro ao buscar memórias: {e}", "error"))

        thread = threading.Thread(target=fetch, daemon=True)
        thread.start()

    def _clear_output(self):
        """Limpa o console de output"""
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", "end")
        self.output_text.configure(state="disabled")
        self._log("Console limpo.", "system")

    def _update_skills_list(self):
        """Atualiza lista de skills carregadas"""
        if not self.prometheus:
            return

        skills = self.prometheus.skills

        self.skills_text.configure(state="normal")
        self.skills_text.delete("1.0", "end")

        self.skills_text.insert("end", f"Total: {len(skills)} skills\n\n")

        for skill_name in sorted(skills.keys()):
            self.skills_text.insert("end", f"✓ {skill_name}\n")

        self.skills_text.configure(state="disabled")

    def _update_status(self, status: str, color: str):
        """Atualiza status do sistema"""
        self.status_label.configure(
            text=f"Status: {status}",
            text_color=color
        )

    def _log(self, message: str, msg_type: str = "info"):
        """
        Adiciona mensagem ao console

        Args:
            message: Mensagem a exibir
            msg_type: Tipo (system, command, response, error, success, warning, info)
        """
        self.output_text.configure(state="normal")

        timestamp = datetime.now().strftime("%H:%M:%S")

        # Cores por tipo
        colors = {
            "system": "#888888",
            "command": "#00BFFF",
            "response": "#00FF00",
            "error": "#FF4444",
            "success": "#00FF88",
            "warning": "#FFA500",
            "info": "#CCCCCC"
        }

        color = colors.get(msg_type, "#FFFFFF")

        # Adicionar mensagem
        self.output_text.insert("end", f"[{timestamp}] {message}\n")

        # Scroll para o final
        self.output_text.see("end")

        self.output_text.configure(state="disabled")

    def _history_up(self, event):
        """Navega histórico para cima"""
        if not self.command_history:
            return

        if self.history_index > 0:
            self.history_index -= 1
            self.command_entry.delete(0, "end")
            self.command_entry.insert(0, self.command_history[self.history_index])

    def _history_down(self, event):
        """Navega histórico para baixo"""
        if not self.command_history:
            return

        if self.history_index < len(self.command_history) - 1:
            self.history_index += 1
            self.command_entry.delete(0, "end")
            self.command_entry.insert(0, self.command_history[self.history_index])
        else:
            self.history_index = len(self.command_history)
            self.command_entry.delete(0, "end")

    def _update_clock(self):
        """Atualiza relógio na barra de status"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.configure(text=current_time)
        self.root.after(1000, self._update_clock)

    def run(self):
        """Inicia a interface gráfica"""
        self._log("Prometheus UI iniciada", "system")
        self._log("Aguarde enquanto o sistema é inicializado...", "info")
        self.root.mainloop()


def main():
    """Função principal"""
    if not CTK_AVAILABLE:
        print("Erro: CustomTkinter não está instalado")
        print("Instale com: pip install customtkinter")
        return

    print("Iniciando Prometheus UI...")
    app = PrometheusUI()
    app.run()


if __name__ == "__main__":
    main()
