#!/usr/bin/env python
"""
PROMETHEUS SUPREME - INTERFACE GRAFICA DESKTOP
Interface futurista estilo JARVIS com Tkinter
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import asyncio
import threading
from datetime import datetime
import json
import sys
from pathlib import Path

# Importar Prometheus
sys.path.insert(0, str(Path.cwd()))

class PrometheusGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("PROMETHEUS SUPREME - AI EXECUTOR")
        self.root.geometry("1200x700")

        # Cores tema dark/cyber
        self.bg_color = "#0a0e27"
        self.fg_color = "#00ff41"
        self.accent = "#00bfff"
        self.error = "#ff0040"

        self.root.configure(bg=self.bg_color)

        # Prometheus instance
        self.prometheus = None
        self.loop = None

        self.create_widgets()
        self.start_async_loop()

    def create_widgets(self):
        """Cria todos os widgets da interface"""

        # Frame superior - Status
        status_frame = tk.Frame(self.root, bg=self.bg_color, height=100)
        status_frame.pack(fill=tk.X, padx=10, pady=5)

        # Titulo principal
        title = tk.Label(
            status_frame,
            text="PROMETHEUS SUPREME",
            font=("Courier", 24, "bold"),
            bg=self.bg_color,
            fg=self.fg_color
        )
        title.pack()

        # Status labels
        self.status_label = tk.Label(
            status_frame,
            text="STATUS: INICIALIZANDO...",
            font=("Courier", 12),
            bg=self.bg_color,
            fg=self.accent
        )
        self.status_label.pack()

        # Frame principal com duas colunas
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Coluna esquerda - Input e Output
        left_frame = tk.Frame(main_frame, bg=self.bg_color)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Input area
        tk.Label(
            left_frame,
            text="COMANDO:",
            font=("Courier", 12, "bold"),
            bg=self.bg_color,
            fg=self.fg_color
        ).pack(anchor=tk.W)

        self.input_text = scrolledtext.ScrolledText(
            left_frame,
            height=5,
            font=("Courier", 11),
            bg="#1a1f3a",
            fg=self.fg_color,
            insertbackground=self.fg_color,
            wrap=tk.WORD
        )
        self.input_text.pack(fill=tk.X, pady=5)

        # Botoes de acao
        button_frame = tk.Frame(left_frame, bg=self.bg_color)
        button_frame.pack(fill=tk.X, pady=5)

        self.execute_btn = tk.Button(
            button_frame,
            text="EXECUTAR",
            command=self.execute_command,
            bg=self.accent,
            fg="white",
            font=("Courier", 12, "bold"),
            cursor="hand2",
            width=15
        )
        self.execute_btn.pack(side=tk.LEFT, padx=5)

        self.clear_btn = tk.Button(
            button_frame,
            text="LIMPAR",
            command=self.clear_output,
            bg="#444",
            fg="white",
            font=("Courier", 12),
            width=10
        )
        self.clear_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = tk.Button(
            button_frame,
            text="PARAR",
            command=self.stop_execution,
            bg=self.error,
            fg="white",
            font=("Courier", 12),
            width=10,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        # Output area
        tk.Label(
            left_frame,
            text="OUTPUT:",
            font=("Courier", 12, "bold"),
            bg=self.bg_color,
            fg=self.fg_color
        ).pack(anchor=tk.W, pady=(10, 0))

        self.output_text = scrolledtext.ScrolledText(
            left_frame,
            height=20,
            font=("Courier", 10),
            bg="#0f1628",
            fg=self.fg_color,
            wrap=tk.WORD
        )
        self.output_text.pack(fill=tk.BOTH, expand=True, pady=5)

        # Coluna direita - Stats e Info
        right_frame = tk.Frame(main_frame, bg=self.bg_color, width=350)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        right_frame.pack_propagate(False)

        # Stats
        tk.Label(
            right_frame,
            text="ESTATISTICAS:",
            font=("Courier", 12, "bold"),
            bg=self.bg_color,
            fg=self.fg_color
        ).pack(anchor=tk.W)

        self.stats_frame = tk.Frame(right_frame, bg=self.bg_color)
        self.stats_frame.pack(fill=tk.X, pady=10)

        # Componentes ativos
        tk.Label(
            right_frame,
            text="COMPONENTES:",
            font=("Courier", 12, "bold"),
            bg=self.bg_color,
            fg=self.fg_color
        ).pack(anchor=tk.W, pady=(20, 5))

        self.components_frame = tk.Frame(right_frame, bg=self.bg_color)
        self.components_frame.pack(fill=tk.X)

        # Quick actions
        tk.Label(
            right_frame,
            text="ACOES RAPIDAS:",
            font=("Courier", 12, "bold"),
            bg=self.bg_color,
            fg=self.fg_color
        ).pack(anchor=tk.W, pady=(20, 5))

        quick_actions = [
            ("Health Check", self.health_check),
            ("Ver Skills", self.show_skills),
            ("Ver Status", self.show_status),
            ("Buscar Knowledge", self.search_knowledge),
            ("Exemplos", self.show_examples)
        ]

        for text, command in quick_actions:
            btn = tk.Button(
                right_frame,
                text=text,
                command=command,
                bg="#2a3f5f",
                fg="white",
                font=("Courier", 10),
                cursor="hand2",
                width=20
            )
            btn.pack(fill=tk.X, pady=2)

        # Footer
        footer = tk.Frame(self.root, bg="#0a0e27", height=30)
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        self.footer_label = tk.Label(
            footer,
            text="Pronto para comandos...",
            font=("Courier", 10),
            bg=self.bg_color,
            fg=self.accent
        )
        self.footer_label.pack(side=tk.LEFT, padx=10)

        # Hora
        self.time_label = tk.Label(
            footer,
            text="",
            font=("Courier", 10),
            bg=self.bg_color,
            fg=self.fg_color
        )
        self.time_label.pack(side=tk.RIGHT, padx=10)

        self.update_time()

    def start_async_loop(self):
        """Inicia loop asyncio em thread separada"""
        def run_loop():
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()

        thread = threading.Thread(target=run_loop, daemon=True)
        thread.start()

        # Inicializar Prometheus
        self.root.after(100, self.init_prometheus)

    def init_prometheus(self):
        """Inicializa Prometheus Supreme"""
        def init_async():
            try:
                from prometheus_supreme import PrometheusSupreme
                self.prometheus = PrometheusSupreme()
                self.root.after(0, self.on_prometheus_ready)
            except Exception as e:
                self.root.after(0, lambda: self.on_prometheus_error(str(e)))

        # Executar em thread separada (nao precisa ser coroutine)
        import threading
        threading.Thread(target=init_async, daemon=True).start()

    def on_prometheus_ready(self):
        """Callback quando Prometheus esta pronto"""
        self.status_label.config(text="STATUS: ONLINE", fg=self.fg_color)
        self.output("[SISTEMA] Prometheus Supreme inicializado com sucesso!")
        self.output("[SISTEMA] Digite um comando ou use as acoes rapidas")
        self.output("-" * 60)
        self.update_stats()
        self.update_components()

    def on_prometheus_error(self, error):
        """Callback para erros de inicializacao"""
        self.status_label.config(text="STATUS: ERRO", fg=self.error)
        self.output(f"[ERRO] Falha ao inicializar: {error}", error=True)

    def execute_command(self):
        """Executa comando no Prometheus"""
        command = self.input_text.get("1.0", tk.END).strip()

        if not command:
            messagebox.showwarning("Aviso", "Digite um comando!")
            return

        if not self.prometheus:
            messagebox.showerror("Erro", "Sistema nao inicializado!")
            return

        self.output(f"\n[COMANDO] {command}\n")
        self.execute_btn.config(state=tk.DISABLED, text="PROCESSANDO...")
        self.stop_btn.config(state=tk.NORMAL)
        self.footer_label.config(text="Processando comando...")

        async def execute():
            try:
                result = await self.prometheus.execute(command)
                return result
            except Exception as e:
                return {"success": False, "error": str(e)}

        def callback(future):
            result = future.result()
            self.root.after(0, lambda: self.on_command_complete(result))

        future = asyncio.run_coroutine_threadsafe(execute(), self.loop)
        future.add_done_callback(lambda f: callback(f))

    def on_command_complete(self, result):
        """Callback quando comando completa"""
        self.execute_btn.config(state=tk.NORMAL, text="EXECUTAR")
        self.stop_btn.config(state=tk.DISABLED)

        if result.get("success"):
            self.output("[SUCESSO] Comando executado com sucesso!", success=True)
            self.footer_label.config(text="Comando executado com sucesso!")
        else:
            self.output("[ERRO] Falha na execucao!", error=True)
            self.footer_label.config(text="Erro na execucao")

        # Mostrar output
        if result.get("output"):
            self.output(f"[OUTPUT] {str(result['output'])[:1000]}")

        # Mostrar tempo
        if result.get("duration"):
            self.output(f"[TEMPO] {result['duration']:.2f} segundos")

        # Mostrar erros
        if result.get("errors"):
            for error in result["errors"]:
                self.output(f"[ERRO] {error}", error=True)

        self.output("-" * 60)

        # Atualizar stats
        self.update_stats()

    def stop_execution(self):
        """Para execucao atual"""
        self.output("[INFO] Parando execucao...")
        self.execute_btn.config(state=tk.NORMAL, text="EXECUTAR")
        self.stop_btn.config(state=tk.DISABLED)
        self.footer_label.config(text="Execucao cancelada")

    def health_check(self):
        """Executa health check"""
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert("1.0", "health check do sistema")
        self.execute_command()

    def show_skills(self):
        """Mostra skills aprendidas"""
        self.input_text.delete("1.0", tk.END)
        self.input_text.insert("1.0", "mostre as habilidades aprendidas")
        self.execute_command()

    def show_status(self):
        """Mostra status do sistema"""
        self.update_stats()
        self.update_components()
        self.output("[INFO] Status atualizado")

    def search_knowledge(self):
        """Dialog para buscar no knowledge base"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Buscar Knowledge Base")
        dialog.geometry("500x200")
        dialog.configure(bg=self.bg_color)

        tk.Label(
            dialog,
            text="Digite sua busca:",
            font=("Courier", 12),
            bg=self.bg_color,
            fg=self.fg_color
        ).pack(pady=10)

        entry = tk.Entry(
            dialog,
            font=("Courier", 11),
            bg="#1a1f3a",
            fg=self.fg_color,
            width=50
        )
        entry.pack(fill=tk.X, padx=20, pady=5)
        entry.focus()

        def search():
            query = entry.get()
            if query:
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert("1.0", f"Busque no knowledge base: {query}")
                dialog.destroy()
                self.execute_command()

        tk.Button(
            dialog,
            text="Buscar",
            command=search,
            bg=self.accent,
            fg="white",
            font=("Courier", 11),
            width=15
        ).pack(pady=10)

        # Enter para buscar
        entry.bind('<Return>', lambda e: search())

    def show_examples(self):
        """Mostra exemplos de comandos"""
        examples = [
            "Crie um script Python para analise de dados",
            "Busque informacoes sobre machine learning",
            "Analise o codigo e sugira melhorias",
            "Crie uma API REST com FastAPI",
            "Automatize o processo de backup"
        ]

        self.output("\n[EXEMPLOS DE COMANDOS]")
        for i, ex in enumerate(examples, 1):
            self.output(f"  {i}. {ex}")
        self.output("\nClique em um exemplo para usa-lo")
        self.output("-" * 60)

    def update_stats(self):
        """Atualiza estatisticas"""
        if self.prometheus and hasattr(self.prometheus, "stats"):
            stats = self.prometheus.stats

            # Limpar frame
            for widget in self.stats_frame.winfo_children():
                widget.destroy()

            # Adicionar stats
            stats_data = [
                ("Tasks Executadas:", stats.get("tasks_executed", 0)),
                ("Taxa de Sucesso:", f"{stats.get('success_rate', 0):.1f}%"),
                ("Aprendizados:", stats.get("learnings_acquired", 0)),
                ("Tempo Total:", f"{stats.get('total_time_saved', 0):.1f}s")
            ]

            for label, value in stats_data:
                frame = tk.Frame(self.stats_frame, bg=self.bg_color)
                frame.pack(fill=tk.X, pady=2)

                lbl = tk.Label(
                    frame,
                    text=label,
                    font=("Courier", 10),
                    bg=self.bg_color,
                    fg=self.accent
                )
                lbl.pack(side=tk.LEFT)

                val = tk.Label(
                    frame,
                    text=str(value),
                    font=("Courier", 10, "bold"),
                    bg=self.bg_color,
                    fg=self.fg_color
                )
                val.pack(side=tk.RIGHT)

    def update_components(self):
        """Atualiza status dos componentes"""
        # Limpar frame
        for widget in self.components_frame.winfo_children():
            widget.destroy()

        components = [
            ("Vision (OCR)", True, "Ativo"),
            ("Supervisor", True, "Ativo"),
            ("Learning Engine", True, "Ativo"),
            ("File Integrity", True, "Ativo"),
            ("Brain (Knowledge)", False, "Opcional"),
            ("Multi-IA Consensus", False, "Opcional")
        ]

        for name, active, status in components:
            frame = tk.Frame(self.components_frame, bg=self.bg_color)
            frame.pack(fill=tk.X, pady=2)

            color = self.fg_color if active else "#666"
            symbol = "[+]" if active else "[-]"

            label = tk.Label(
                frame,
                text=f"{symbol} {name}",
                font=("Courier", 10),
                bg=self.bg_color,
                fg=color
            )
            label.pack(side=tk.LEFT)

            status_label = tk.Label(
                frame,
                text=status,
                font=("Courier", 9),
                bg=self.bg_color,
                fg="#888"
            )
            status_label.pack(side=tk.RIGHT)

    def update_time(self):
        """Atualiza relogio"""
        now = datetime.now().strftime("%H:%M:%S")
        self.time_label.config(text=now)
        self.root.after(1000, self.update_time)

    def output(self, text, error=False, success=False):
        """Adiciona texto ao output"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_text = f"[{timestamp}] {text}\n"

        self.output_text.insert(tk.END, formatted_text)

        if error:
            # Colorir ultima linha de vermelho
            self.output_text.tag_add("error", "end-2l", "end-1l")
            self.output_text.tag_config("error", foreground=self.error)
        elif success:
            # Colorir ultima linha de verde brilhante
            self.output_text.tag_add("success", "end-2l", "end-1l")
            self.output_text.tag_config("success", foreground="#00ff00")

        self.output_text.see(tk.END)

    def clear_output(self):
        """Limpa output e input"""
        self.output_text.delete("1.0", tk.END)
        self.input_text.delete("1.0", tk.END)
        self.output("[SISTEMA] Interface limpa")

    def run(self):
        """Inicia a interface"""
        # Centralizar janela
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

        self.root.mainloop()


if __name__ == "__main__":
    print("[*] Iniciando Prometheus Supreme GUI...")
    print("[*] Interface Desktop carregando...")
    app = PrometheusGUI()
    app.run()
