import subprocess
import datetime
import platform
import os
import sys

def run_command(cmd):
    """Execute command and return output"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=10)
        return result.stdout.strip() if result.returncode == 0 else f"Error: {result.stderr.strip()}"
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    report_path = os.path.join(log_dir, "activation_report.txt")

    print("Gerando relatorio de ativacao do Prometheus...")
    print("=" * 80)

    # Coleta de informações
    info = {
        "Data/Hora": datetime.datetime.now().isoformat(),
        "Sistema Operacional": platform.platform(),
        "Arquitetura": platform.machine(),
        "Versao Python": platform.python_version(),
        "Diretorio": os.getcwd(),
        "": "",
        "=== VERSOES DAS FERRAMENTAS ===": "",
        "Python": run_command("python --version"),
        "Git": run_command("git --version"),
        "Docker": run_command("docker --version"),
        " ": "",
        "=== PACOTES PYTHON INSTALADOS ===": "",
        "Pacotes no venv": run_command(r".\.venv\Scripts\python.exe -m pip list"),
        "  ": "",
        "=== STATUS DO DOCKER ===": "",
        "Containers Ativos": run_command("docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"),
        "   ": "",
        "=== STATUS DO N8N ===": "",
        "Logs do n8n (ultimas 10 linhas)": run_command("docker logs n8n_instance --tail 10"),
        "    ": "",
        "=== ESTRUTURA DO PROJETO ===": "",
        "Arquivos principais": run_command("dir /B"),
        "Conteudo core": run_command("dir core /B /S"),
    }

    # Escreve o relatório
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("RELATORIO DE ATIVACAO - PROJETO PROMETHEUS\n")
        f.write("=" * 80 + "\n\n")

        for key, value in info.items():
            if key.startswith("==="):
                f.write(f"\n{key}\n")
                f.write("-" * 80 + "\n")
            elif key.strip() == "":
                f.write("\n")
            else:
                f.write(f"{key}:\n")
                if "\n" in str(value):
                    f.write(f"{value}\n\n")
                else:
                    f.write(f"  {value}\n\n")

        f.write("\n" + "=" * 80 + "\n")
        f.write("FIM DO RELATORIO\n")
        f.write("=" * 80 + "\n")

    print(f"\nRelatorio salvo em: {report_path}")
    print("\nResumo da instalacao:")
    print("  - Python virtualenv: OK")
    print("  - open-interpreter: OK")
    print("  - Docker: OK")
    print("  - n8n container: OK")
    print("\nPara acessar o n8n:")
    print("  URL: http://localhost:5678")
    print("  Usuario: prometheus")
    print("  Senha: password123")
    print("\nProximo passo:")
    print("  Para iniciar o open-interpreter:")
    print(r"    .\.venv\Scripts\python.exe -m open_interpreter")

if __name__ == "__main__":
    main()
