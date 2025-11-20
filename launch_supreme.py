#!/usr/bin/env python
"""
[RUN] PROMETHEUS SUPREME LAUNCHER
Inicializa o sistema completo integrado
"""

import os
import sys
import asyncio
from pathlib import Path

# Adicionar path do Prometheus ao Python
PROMETHEUS_PATH = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROMETHEUS_PATH))

# Carregar variáveis de ambiente
from dotenv import load_dotenv
load_dotenv()

# Importar Prometheus Supreme
try:
    from prometheus_supreme import PrometheusSupreme
except ImportError as e:
    print(f"[-] Erro ao importar Prometheus Supreme: {e}")
    print("Certifique-se de que todos os módulos estão instalados corretamente.")
    sys.exit(1)


def print_header():
    """Exibe header do sistema"""
    print("\n" + "="*70)
    print("[*] PROMETHEUS SUPREME - SISTEMA INTEGRADO")
    print("="*70)
    print("Unificação completa dos módulos V3.5:")
    print("  [BRAIN] Brain & Knowledge (6,973+ chunks)")
    print("  [TASK] Tasks & Scheduling")
    print("  [EXEC] Execution Engine")
    print("  [SUPER] Supervisor & Telemetry")
    print("  [SECURE] File Integrity")
    print("  [WEB] Browser Executor V2")
    print("  [AI] Multi-AI Consensus (Claude + GPT-4 + Gemini)")
    print("  [LEARN] Self-Improvement & Learning")
    print("="*70 + "\n")


def print_menu():
    """Exibe menu de opções"""
    print("\n+-----------------------------------------+")
    print("|         MENU PROMETHEUS SUPREME         |")
    print("+-----------------------------------------+")
    print("| 1. Executar Comando                     |")
    print("| 2. Buscar na Base de Conhecimento       |")
    print("| 3. Ver Status do Sistema                |")
    print("| 4. Ver Habilidades Aprendidas           |")
    print("| 5. Health Check Completo                |")
    print("| 6. Sair                                 |")
    print("+-----------------------------------------+")


async def execute_command(prometheus: PrometheusSupreme):
    """Executa comando via Prometheus Supreme"""
    print("\n" + "─"*70)
    command = input("Digite o comando: ").strip()

    if not command:
        print("[!] Comando vazio, cancelando...")
        return

    print(f"\n[RUN] Executando: {command}")
    print("─"*70)

    try:
        result = await prometheus.execute_command(command)

        print("\n" + "="*70)
        print("[+] RESULTADO:")
        print("="*70)
        print(result.get("output", "Sem output"))

        if result.get("success"):
            print("\n[+] Comando executado com sucesso!")
        else:
            print(f"\n[-] Erro: {result.get('error', 'Erro desconhecido')}")

    except Exception as e:
        print(f"\n[-] Erro ao executar comando: {e}")


async def search_knowledge(prometheus: PrometheusSupreme):
    """Busca na base de conhecimento"""
    print("\n" + "─"*70)
    query = input("Digite sua busca: ").strip()

    if not query:
        print("[!] Busca vazia, cancelando...")
        return

    print(f"\n[SEARCH] Buscando: {query}")
    print("─"*70)

    try:
        results = await prometheus.search_knowledge(query, top_k=5)

        print("\n" + "="*70)
        print(f"[LEARN] RESULTADOS DA BUSCA ({len(results)} encontrados):")
        print("="*70)

        for i, result in enumerate(results, 1):
            print(f"\n[{i}] Relevância: {result.get('score', 0):.2f}")
            print(f"    Fonte: {result.get('source', 'Desconhecida')}")
            print(f"    Preview: {result.get('content', '')[:200]}...")
            print("    " + "─"*66)

    except Exception as e:
        print(f"\n[-] Erro ao buscar conhecimento: {e}")


async def show_status(prometheus: PrometheusSupreme):
    """Mostra status do sistema"""
    print("\n" + "="*70)
    print("[STATS] STATUS DO SISTEMA PROMETHEUS SUPREME")
    print("="*70)

    try:
        status = await prometheus.get_system_status()

        print(f"\n[OK] Sistema: {'Online' if status.get('online') else 'Offline'}")
        print(f"[TIME] Uptime: {status.get('uptime', 'N/A')}")
        print(f"[NOTE] Tarefas Ativas: {status.get('active_tasks', 0)}")
        print(f"[LEARN] Chunks de Conhecimento: {status.get('knowledge_chunks', 0)}")
        print(f"[SKILL] Habilidades Aprendidas: {status.get('learned_skills', 0)}")

        # Módulos
        print("\n[MODULE] MÓDULOS:")
        modules = status.get('modules', {})
        for module_name, module_status in modules.items():
            icon = "[+]" if module_status else "[-]"
            print(f"  {icon} {module_name}")

        # AIs disponíveis
        print("\n[AI] MULTI-AI STATUS:")
        ais = status.get('ai_providers', {})
        for ai_name, ai_status in ais.items():
            icon = "[+]" if ai_status else "[-]"
            print(f"  {icon} {ai_name}")

    except Exception as e:
        print(f"\n[-] Erro ao obter status: {e}")


async def show_learned_skills(prometheus: PrometheusSupreme):
    """Mostra habilidades aprendidas"""
    print("\n" + "="*70)
    print("[SKILL] HABILIDADES APRENDIDAS")
    print("="*70)

    try:
        skills = await prometheus.get_learned_skills()

        if not skills:
            print("\n[!] Nenhuma habilidade aprendida ainda.")
            return

        for i, skill in enumerate(skills, 1):
            print(f"\n[{i}] {skill.get('name', 'Sem nome')}")
            print(f"    Categoria: {skill.get('category', 'N/A')}")
            print(f"    Nível: {skill.get('proficiency', 0):.1f}/10")
            print(f"    Vezes usada: {skill.get('usage_count', 0)}")
            print(f"    Aprendida em: {skill.get('learned_at', 'N/A')}")
            print("    " + "─"*66)

    except Exception as e:
        print(f"\n[-] Erro ao obter habilidades: {e}")


async def health_check(prometheus: PrometheusSupreme):
    """Executa health check completo"""
    print("\n" + "="*70)
    print("[HEALTH] HEALTH CHECK COMPLETO")
    print("="*70)

    try:
        health = await prometheus.health_check()

        print(f"\n[SEARCH] Status Geral: {health.get('status', 'UNKNOWN')}")
        print(f"[TIME] Timestamp: {health.get('timestamp', 'N/A')}")

        # Checks individuais
        print("\n[LIST] VERIFICAÇÕES:")
        checks = health.get('checks', {})

        for check_name, check_result in checks.items():
            status_icon = "[+]" if check_result.get('healthy') else "[-]"
            print(f"\n  {status_icon} {check_name}")
            print(f"      Status: {check_result.get('status', 'N/A')}")

            if check_result.get('message'):
                print(f"      Mensagem: {check_result.get('message')}")

            if check_result.get('metrics'):
                print(f"      Métricas: {check_result.get('metrics')}")

        # Recomendações
        if health.get('recommendations'):
            print("\n[IDEA] RECOMENDAÇÕES:")
            for rec in health.get('recommendations', []):
                print(f"  • {rec}")

    except Exception as e:
        print(f"\n[-] Erro ao executar health check: {e}")


async def main():
    """Loop principal do launcher"""
    print_header()

    # Inicializar Prometheus Supreme
    print("[TOOL] Inicializando Prometheus Supreme...")

    try:
        prometheus = PrometheusSupreme()
        await prometheus.initialize()
        print("[+] Prometheus Supreme inicializado com sucesso!\n")
    except Exception as e:
        print(f"[-] Erro ao inicializar Prometheus Supreme: {e}")
        print("\nVerifique:")
        print("  1. Se todos os módulos estão instalados")
        print("  2. Se o arquivo .env está configurado corretamente")
        print("  3. Se as credenciais de API estão válidas")
        sys.exit(1)

    # Loop do menu
    while True:
        print_menu()
        choice = input("\nEscolha uma opção: ").strip()

        if choice == "1":
            await execute_command(prometheus)
        elif choice == "2":
            await search_knowledge(prometheus)
        elif choice == "3":
            await show_status(prometheus)
        elif choice == "4":
            await show_learned_skills(prometheus)
        elif choice == "5":
            await health_check(prometheus)
        elif choice == "6":
            print("\n[WAVE] Encerrando Prometheus Supreme...")
            await prometheus.shutdown()
            print("[+] Sistema encerrado com sucesso!")
            break
        else:
            print("[!] Opção inválida, tente novamente.")

        input("\nPressione ENTER para continuar...")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n[!] Interrompido pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"\n[-] Erro fatal: {e}")
        sys.exit(1)
