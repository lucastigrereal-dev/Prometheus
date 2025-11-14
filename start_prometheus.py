#!/usr/bin/env python3
"""
Start Prometheus - Inicializador completo do sistema
MODO ABSOLUTO - Sistema Jarvis completo com reconhecimento de voz e skills
"""
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

# Importar componentes do Prometheus
from prometheus_brain import PrometheusCore
from voice_listener import VoiceListener, SPEECH_RECOGNITION_AVAILABLE
from skills.logs import setup_logger

# Carregar variáveis de ambiente
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("⚠️ python-dotenv não instalado. Execute: pip install python-dotenv")

logger = setup_logger("start_prometheus", "./logs/prometheus.log")


def log(message):
    """Função de log compatível com código anterior"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")
    logger.info(message)


def run_cmd(cmd, check=True):
    """Executa comando e retorna resultado"""
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        return result
    except subprocess.CalledProcessError as e:
        log(f"Erro ao executar: {cmd}")
        log(f"   {e.stderr.strip()}")
        return None


def check_docker():
    """Verifica se Docker está ativo"""
    result = run_cmd("docker ps", check=False)
    return result and result.returncode == 0


def start_n8n():
    """Inicia n8n via Docker Compose"""
    log("Iniciando n8n...")

    if not check_docker():
        log("Docker não está rodando. Inicie o Docker Desktop primeiro.")
        return False

    # Para container existente
    run_cmd("docker stop n8n_instance", check=False)
    run_cmd("docker rm n8n_instance", check=False)

    # Inicia via docker-compose
    result = run_cmd("docker-compose up -d")

    if result and result.returncode == 0:
        log("n8n iniciado em http://localhost:5678")
        return True
    else:
        log("Falha ao iniciar n8n")
        return False


def check_dependencies():
    """Verifica dependências necessárias"""
    log("Verificando dependências...")

    missing = []

    # Verificar bibliotecas essenciais
    try:
        import requests
        log("  requests: OK")
    except ImportError:
        missing.append("requests")
        log("  requests: FALTANDO")

    try:
        import yaml
        log("  pyyaml: OK")
    except ImportError:
        missing.append("pyyaml")
        log("  pyyaml: FALTANDO")

    if not SPEECH_RECOGNITION_AVAILABLE:
        log("  speech_recognition: FALTANDO (opcional)")
        log("    Para ativar voz: pip install SpeechRecognition pyaudio")
    else:
        log("  speech_recognition: OK")

    if missing:
        log(f"Dependências faltando: {', '.join(missing)}")
        log(f"Instale com: pip install {' '.join(missing)}")
        return False

    return True


def process_command_queue(brain: PrometheusCore, queue_file: str):
    """Processa comandos da fila"""
    try:
        if not os.path.exists(queue_file):
            return

        with open(queue_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Filtrar comandos válidos (não vazios, não comentários)
        commands = [line.strip() for line in lines if line.strip() and not line.strip().startswith('#')]

        if commands:
            log(f"Processando {len(commands)} comando(s) da fila...")

            for command in commands:
                log(f"Executando: {command}")
                result = brain.handle_text_command(command)

                if result.get("success"):
                    log(f"  Resultado: {result.get('message', 'OK')}")
                else:
                    log(f"  Erro: {result.get('error', 'Unknown')}")

            # Limpar fila após processamento
            with open(queue_file, 'w', encoding='utf-8') as f:
                f.write("# Prometheus Command Queue\n")
                f.write("# Comandos processados e limpos\n\n")

    except Exception as e:
        logger.error(f"Erro ao processar fila: {e}", exc_info=True)


def interactive_mode(brain: PrometheusCore):
    """Modo interativo para comandos de texto"""
    log("")
    log("=" * 60)
    log("MODO INTERATIVO ATIVADO")
    log("Digite comandos ou 'sair' para encerrar")
    log("Exemplos:")
    log("  - listar arquivos C:\\Users")
    log("  - organizar downloads")
    log("  - status")
    log("  - abrir pasta C:\\Temp")
    log("=" * 60)
    log("")

    while True:
        try:
            command = input("Prometheus> ").strip()

            if not command:
                continue

            if command.lower() in ["sair", "exit", "quit", "q"]:
                log("Encerrando Prometheus...")
                break

            if command.lower() in ["ajuda", "help", "?"]:
                show_help()
                continue

            # Processar comando
            result = brain.handle_text_command(command)

            if result.get("success"):
                print(f"\nRESULTADO:")
                print_result(result)
            else:
                print(f"\nERRO: {result.get('error', 'Unknown')}")
                if result.get("suggestion"):
                    print(f"SUGESTÃO: {result.get('suggestion')}")

            print("")

        except KeyboardInterrupt:
            log("\nInterrompido pelo usuário")
            break
        except Exception as e:
            logger.error(f"Erro no modo interativo: {e}", exc_info=True)
            print(f"Erro: {e}")


def print_result(result: dict):
    """Imprime resultado de forma formatada"""
    for key, value in result.items():
        if key == "success":
            continue
        print(f"  {key}: {value}")


def show_help():
    """Exibe ajuda"""
    print("""
COMANDOS DISPONÍVEIS:

Sistema:
  - listar arquivos [caminho]
  - abrir pasta [caminho]
  - organizar downloads
  - executar [comando]

n8n:
  - status n8n
  - listar workflows
  - n8n [mensagem]

WhatsApp:
  - whatsapp [número] "[mensagem]"

RD Station:
  - criar lead [email]
  - buscar lead [email]

Supabase:
  - inserir supabase [dados]
  - consultar supabase

AI:
  - perguntar [pergunta]
  - ai [prompt]

Geral:
  - status - testa todas as conexões
  - ajuda - exibe esta mensagem
  - sair - encerra o sistema
    """)


def voice_mode(brain: PrometheusCore):
    """Modo de escuta contínua com voz"""
    log("")
    log("=" * 60)
    log("MODO VOZ ATIVADO")
    log("Diga 'Prometheus' seguido do comando")
    log("Pressione Ctrl+C para parar")
    log("=" * 60)
    log("")

    listener = VoiceListener()

    def handle_voice_command(command: str):
        """Callback para comandos de voz"""
        log(f"Comando de voz: {command}")
        result = brain.handle_text_command(command)

        if result.get("success"):
            log(f"Executado com sucesso")
        else:
            log(f"Erro: {result.get('error')}")

    try:
        listener.listen_continuous(handle_voice_command)
    except KeyboardInterrupt:
        log("Modo voz encerrado")


def main():
    log("=" * 60)
    log("PROMETHEUS MODO ABSOLUTO - INICIANDO")
    log("=" * 60)

    # 1. Verificar dependências
    if not check_dependencies():
        log("Instale as dependências faltando antes de continuar")
        sys.exit(1)

    # 2. Verificar Docker (opcional)
    if check_docker():
        log("Docker: ATIVO")

        # Tentar iniciar n8n
        n8n_ok = start_n8n()
        if n8n_ok:
            log("n8n: RODANDO em http://localhost:5678")
    else:
        log("Docker: NÃO ATIVO (n8n não será iniciado)")

    # 3. Criar diretórios necessários
    os.makedirs("./logs", exist_ok=True)
    os.makedirs("./runtime", exist_ok=True)

    # 4. Inicializar Prometheus Brain
    log("")
    log("Inicializando Prometheus Brain...")
    brain = PrometheusCore()
    result = brain.start()

    if not result.get("success"):
        log(f"Erro ao iniciar brain: {result.get('error')}")
        sys.exit(1)

    log("")
    log("=" * 60)
    log("PROMETHEUS ONLINE E OPERACIONAL")
    log("=" * 60)

    # 5. Processar fila de comandos se houver
    queue_file = "./runtime/commands_queue.txt"
    process_command_queue(brain, queue_file)

    # 6. Escolher modo de operação
    log("")
    log("Escolha o modo de operação:")
    log("  1. Modo Interativo (texto)")
    log("  2. Modo Voz (reconhecimento de voz)")
    log("  3. Sair")

    try:
        choice = input("\nEscolha [1/2/3]: ").strip()

        if choice == "1":
            interactive_mode(brain)
        elif choice == "2":
            if SPEECH_RECOGNITION_AVAILABLE:
                voice_mode(brain)
            else:
                log("Reconhecimento de voz não disponível")
                log("Instale com: pip install SpeechRecognition pyaudio")
                log("Iniciando modo interativo...")
                interactive_mode(brain)
        elif choice == "3":
            log("Encerrando...")
        else:
            log("Opção inválida. Iniciando modo interativo...")
            interactive_mode(brain)

    except KeyboardInterrupt:
        log("\nInterrompido pelo usuário")

    # 7. Finalizar
    brain.stop()
    log("")
    log("Prometheus encerrado. Até logo!")


if __name__ == "__main__":
    main()

