#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PROMETHEUS SUPREME - TESTE DE INTEGRACAO
Verifica se todos os modulos estao integrados e funcionando corretamente
"""

import sys
import asyncio
from pathlib import Path

# Adicionar path do Prometheus ao Python
PROMETHEUS_PATH = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROMETHEUS_PATH))

# Carregar variáveis de ambiente
from dotenv import load_dotenv
load_dotenv()


def print_section(title: str):
    """Imprime seção de teste"""
    print("\n" + "="*70)
    print(f"{title}")
    print("="*70)


def print_test(test_name: str):
    """Imprime nome do teste"""
    print(f"\n[TEST] {test_name}")
    print("-"*70)


def print_success(message: str):
    """Imprime mensagem de sucesso"""
    print(f"[OK] {message}")


def print_error(message: str):
    """Imprime mensagem de erro"""
    print(f"[FAIL] {message}")


def print_warning(message: str):
    """Imprime mensagem de aviso"""
    print(f"[WARN] {message}")


async def test_imports():
    """Testa importação dos módulos principais"""
    print_section("TESTE 1: Imports de Módulos")

    results = []

    # Teste 1.1: Importar prometheus_supreme
    print_test("Import do Prometheus Supreme")
    try:
        from prometheus_supreme import PrometheusSupreme
        print_success("PrometheusSupreme importado com sucesso")
        results.append(("Import PrometheusSupreme", True))
    except ImportError as e:
        print_error(f"Falha ao importar PrometheusSupreme: {e}")
        results.append(("Import PrometheusSupreme", False))

    # Teste 1.2: Importar Universal Executor
    print_test("Import do Universal Executor")
    try:
        from prometheus_v3.prometheus_universal_executor import UniversalExecutor
        print_success("UniversalExecutor importado com sucesso")
        results.append(("Import UniversalExecutor", True))
    except ImportError as e:
        print_error(f"Falha ao importar UniversalExecutor: {e}")
        results.append(("Import UniversalExecutor", False))

    # Teste 1.3: Importar Self Improvement
    print_test("Import do Self Improvement")
    try:
        from prometheus_v3.prometheus_self_improvement import SelfImprovementEngine
        print_success("SelfImprovementEngine importado com sucesso")
        results.append(("Import SelfImprovementEngine", True))
    except ImportError as e:
        print_error(f"Falha ao importar SelfImprovementEngine: {e}")
        results.append(("Import SelfImprovementEngine", False))

    return results


async def test_initialization():
    """Testa inicialização do Prometheus Supreme"""
    print_section("TESTE 2: Inicialização do Sistema")

    results = []

    print_test("Instanciar Prometheus Supreme")
    try:
        from prometheus_supreme import PrometheusSupreme
        prometheus = PrometheusSupreme()
        print_success("PrometheusSupreme instanciado com sucesso")
        results.append(("Instanciar PrometheusSupreme", True))

        # Teste 2.1: Verificar atributos essenciais
        print_test("Verificar atributos essenciais")
        has_required_attrs = all([
            hasattr(prometheus, 'config'),
            hasattr(prometheus, 'initialize'),
            hasattr(prometheus, 'execute_command'),
        ])

        if has_required_attrs:
            print_success("Todos os atributos essenciais presentes")
            results.append(("Atributos essenciais", True))
        else:
            print_error("Faltam atributos essenciais")
            results.append(("Atributos essenciais", False))

        # Teste 2.2: Tentar inicializar (pode falhar se credenciais não estiverem configuradas)
        print_test("Inicializar sistema")
        try:
            await prometheus.initialize()
            print_success("Sistema inicializado com sucesso")
            results.append(("Inicialização", True))
            return results, prometheus
        except Exception as e:
            print_warning(f"Inicialização falhou (pode ser normal se APIs não configuradas): {e}")
            results.append(("Inicialização", False))
            return results, None

    except Exception as e:
        print_error(f"Erro ao instanciar PrometheusSupreme: {e}")
        results.append(("Instanciar PrometheusSupreme", False))
        return results, None


async def test_system_status(prometheus):
    """Testa obtenção de status do sistema"""
    print_section("TESTE 3: Status do Sistema")

    results = []

    if prometheus is None:
        print_warning("Sistema não inicializado, pulando teste")
        return results

    print_test("Obter status do sistema")
    try:
        status = await prometheus.get_system_status()
        print_success(f"Status obtido: {status.get('online', 'N/A')}")

        # Verificar estrutura do status
        has_required_keys = all([
            'online' in status,
            'modules' in status,
        ])

        if has_required_keys:
            print_success("Estrutura de status correta")
            results.append(("Status do sistema", True))

            # Mostrar módulos disponíveis
            print("\n[MODULES] Modulos detectados:")
            for module_name, module_status in status.get('modules', {}).items():
                icon = "[+]" if module_status else "[-]"
                print(f"  {icon} {module_name}")

        else:
            print_error("Estrutura de status incorreta")
            results.append(("Status do sistema", False))

    except Exception as e:
        print_error(f"Erro ao obter status: {e}")
        results.append(("Status do sistema", False))

    return results


async def test_command_execution(prometheus):
    """Testa execução de comando simples"""
    print_section("TESTE 4: Execução de Comando")

    results = []

    if prometheus is None:
        print_warning("Sistema não inicializado, pulando teste")
        return results

    print_test("Executar comando simples de teste")
    try:
        # Comando de teste simples
        test_command = "echo 'Hello from Prometheus Supreme!'"
        result = await prometheus.execute_command(test_command)

        if result.get('success'):
            print_success(f"Comando executado com sucesso")
            print(f"   Output: {result.get('output', 'N/A')[:100]}")
            results.append(("Execução de comando", True))
        else:
            print_warning(f"Comando falhou: {result.get('error', 'N/A')}")
            results.append(("Execução de comando", False))

    except Exception as e:
        print_error(f"Erro ao executar comando: {e}")
        results.append(("Execução de comando", False))

    return results


async def test_health_check(prometheus):
    """Testa health check do sistema"""
    print_section("TESTE 5: Health Check")

    results = []

    if prometheus is None:
        print_warning("Sistema não inicializado, pulando teste")
        return results

    print_test("Executar health check completo")
    try:
        health = await prometheus.health_check()
        print_success(f"Health check executado: Status = {health.get('status', 'N/A')}")

        # Mostrar checks individuais
        print("\n[HEALTH] Verificações de saúde:")
        checks = health.get('checks', {})

        healthy_count = sum(1 for check in checks.values() if check.get('healthy'))
        total_checks = len(checks)

        for check_name, check_result in checks.items():
            icon = "[+]" if check_result.get('healthy') else "[-]"
            print(f"  {icon} {check_name}: {check_result.get('status', 'N/A')}")

        print(f"\n[STATS] Resultado: {healthy_count}/{total_checks} checks passaram")

        if healthy_count > 0:
            results.append(("Health check", True))
        else:
            results.append(("Health check", False))

    except Exception as e:
        print_error(f"Erro ao executar health check: {e}")
        results.append(("Health check", False))

    return results


async def main():
    """Função principal de teste"""
    print("\n" + "="*70)
    print("[TEST] PROMETHEUS SUPREME - SUITE DE TESTES DE INTEGRAÇÃO")
    print("="*70)
    print("Verificando integração de todos os módulos V3.5...")

    all_results = []

    # Teste 1: Imports
    import_results = await test_imports()
    all_results.extend(import_results)

    # Teste 2: Inicialização
    init_results, prometheus = await test_initialization()
    all_results.extend(init_results)

    # Teste 3: Status (se inicializado)
    if prometheus:
        status_results = await test_system_status(prometheus)
        all_results.extend(status_results)

        # Teste 4: Execução de comando (se inicializado)
        command_results = await test_command_execution(prometheus)
        all_results.extend(command_results)

        # Teste 5: Health check (se inicializado)
        health_results = await test_health_check(prometheus)
        all_results.extend(health_results)

        # Shutdown
        try:
            await prometheus.shutdown()
            print("\n[+] Sistema encerrado corretamente")
        except Exception as e:
            print(f"\n[!] Erro ao encerrar sistema: {e}")

    # Resultados finais
    print_section("RESULTADOS FINAIS")

    passed = sum(1 for _, result in all_results if result)
    total = len(all_results)
    success_rate = (passed / total * 100) if total > 0 else 0

    print("\n[STATS] RESUMO DOS TESTES:")
    for test_name, result in all_results:
        icon = "[+]" if result else "[-]"
        print(f"  {icon} {test_name}")

    print("\n" + "="*70)
    print(f"TOTAL: {passed}/{total} testes passaram ({success_rate:.1f}%)")
    print("="*70)

    if passed == total:
        print("\n[SUCCESS] INTEGRAÇÃO PROMETHEUS SUPREME CONCLUÍDA COM SUCESSO!")
        print("[+] Todos os testes passaram!")
        return 0
    elif passed > 0:
        print(f"\n[!]  INTEGRAÇÃO PARCIAL: {passed}/{total} testes passaram")
        print("Alguns módulos podem não estar configurados corretamente.")
        print("Verifique:")
        print("  1. Configuração do .env (credenciais de API)")
        print("  2. Módulos V3.5 instalados")
        print("  3. Dependências Python instaladas")
        return 1
    else:
        print("\n[-] FALHA NA INTEGRAÇÃO")
        print("Nenhum teste passou. Verifique a instalação.")
        return 2


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n[!] Testes interrompidos pelo usuário.")
        sys.exit(130)
    except Exception as e:
        print(f"\n[-] Erro fatal nos testes: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
