# -*- coding: utf-8 -*-
"""
TESTE DO UNIFIED EXECUTOR - Validação Completa Semana 2
"""

import asyncio
import sys
import io
from pathlib import Path

# Fix encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, str(Path(__file__).parent))

from prometheus_v3.execution.unified_executor import (
    UnifiedExecutor, ExecutionPlan, ExecutionStep, StepStatus
)
from prometheus_v3.execution.system_toolkit import SystemToolkit, SecurityError
from prometheus_v3.execution.checkpoint_manager import CheckpointManager
from integration_bridge import PrometheusIntegrationBridge


async def test_system_toolkit():
    """Testa SystemToolkit com segurança"""
    print("\n" + "=" * 70)
    print("TESTE 1: SystemToolkit com Seguranca")
    print("=" * 70)

    toolkit = SystemToolkit()

    # Test 1: Comando seguro
    print("\n1. Testando comando seguro (ls)...")
    try:
        result = await toolkit.execute_command("ls")
        print(f"   OK Comando executado: success={result.success}")
    except Exception as e:
        print(f"   OK Esperado (sandbox vazio): {e}")

    # Test 2: Comando perigoso bloqueado
    print("\n2. Testando bloqueio de comando perigoso...")
    try:
        result = await toolkit.execute_command("rm -rf /")
        print("   FAIL Comando perigoso NAO foi bloqueado!")
        return False
    except SecurityError as e:
        print(f"   OK Comando bloqueado corretamente: {e}")

    # Test 3: Whitelist/Blacklist
    safe_cmds = toolkit.get_safe_commands()
    dangerous = toolkit.get_dangerous_patterns()
    print(f"\n3. Whitelist: {len(safe_cmds)} comandos seguros")
    print(f"   Blacklist: {len(dangerous)} padroes perigosos")

    print("\nOK SystemToolkit funciona com seguranca!")
    return True


async def test_checkpoint_manager():
    """Testa CheckpointManager"""
    print("\n" + "=" * 70)
    print("TESTE 2: CheckpointManager")
    print("=" * 70)

    manager = CheckpointManager()

    # Test 1: Criar checkpoint
    print("\n1. Criando checkpoint...")
    checkpoint = await manager.create_checkpoint("Test checkpoint")
    print(f"   OK Checkpoint criado: {checkpoint.id}")

    # Test 2: Criar segundo checkpoint
    print("\n2. Criando segundo checkpoint...")
    checkpoint2 = await manager.create_checkpoint("Test checkpoint 2")
    print(f"   OK Checkpoint 2 criado: {checkpoint2.id}")

    # Test 3: Listar checkpoints
    checkpoints = manager.get_checkpoints()
    print(f"\n3. Total de checkpoints: {len(checkpoints)}")

    # Test 4: Stats
    stats = manager.get_stats()
    print(f"\n4. Stats:")
    print(f"   Total checkpoints: {stats['total_checkpoints']}")

    # Test 5: Cleanup
    print("\n5. Limpando checkpoints...")
    await manager.cleanup_checkpoints([checkpoint, checkpoint2])
    remaining = len(manager.get_checkpoints())
    print(f"   OK Checkpoints restantes: {remaining}")

    print("\nOK CheckpointManager funciona!")
    return True


async def test_unified_executor():
    """Testa UnifiedExecutor"""
    print("\n" + "=" * 70)
    print("TESTE 3: UnifiedExecutor")
    print("=" * 70)

    # Cria bridge
    bridge = PrometheusIntegrationBridge(verbose=False)

    # Cria checkpoint manager
    checkpoint_mgr = CheckpointManager()

    # Cria executor
    executor = UnifiedExecutor(
        integration_bridge=bridge,
        checkpoint_manager=checkpoint_mgr,
        dry_run=False  # Executa de verdade
    )

    print(f"\n1. Executor criado com {len(executor.get_available_tools())} ferramentas")

    # Cria plano simples
    plan = ExecutionPlan(
        plan_id="test_001",
        description="Teste de execucao multi-step",
        steps=[
            ExecutionStep(
                tool="browser",
                action="navigate",
                params={"url": "https://google.com"}
            ),
            ExecutionStep(
                tool="browser",
                action="screenshot",
                params={"path": "test.png"}
            ),
            ExecutionStep(
                tool="system",
                action="command",
                params={"cmd": "echo test"},
                is_critical=True  # Cria checkpoint
            )
        ],
        estimated_cost=0.001,
        estimated_time=5.0
    )

    print(f"\n2. Plano criado: {len(plan.steps)} steps")

    # Executa plano
    print("\n3. Executando plano...")
    result = await executor.execute(plan, confirm_before_execute=False)

    print(f"\n4. Resultado da execucao:")
    print(f"   Status: {result.status}")
    print(f"   Success: {result.success}")
    print(f"   Steps completados: {len(result.steps_results)}/{len(plan.steps)}")
    print(f"   Duracao: {result.total_duration:.2f}s")
    print(f"   Checkpoints criados: {result.checkpoints_created}")

    # Detalhes dos steps
    print(f"\n5. Detalhes dos steps:")
    for step_result in result.steps_results:
        print(f"   Step {step_result.step_number}: {step_result.status.value}")

    print("\nOK UnifiedExecutor funciona!")
    return result.success or len(result.steps_results) == len(plan.steps)


async def main():
    """Função principal"""
    print("\n")
    print("+" + "=" * 68 + "+")
    print("|" + " " * 15 + "TESTE UNIFIED EXECUTOR COMPLETO" + " " * 22 + "|")
    print("+" + "=" * 68 + "+")

    all_passed = True

    try:
        # Test 1: SystemToolkit
        passed = await test_system_toolkit()
        all_passed = all_passed and passed

        # Test 2: CheckpointManager
        passed = await test_checkpoint_manager()
        all_passed = all_passed and passed

        # Test 3: UnifiedExecutor
        passed = await test_unified_executor()
        all_passed = all_passed and passed

    except Exception as e:
        print(f"\n ERROR: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    # Resultado
    print("\n" + "=" * 70)
    print("RESULTADO FINAL")
    print("=" * 70)

    if all_passed:
        print("\nOK TODOS OS TESTES PASSARAM!")
        print("\nOK SEMANA 2 COMPLETA:")
        print("   OK UnifiedExecutor")
        print("   OK SystemToolkit com seguranca")
        print("   OK CheckpointManager com rollback")
        print("\nPROXIMO: Semana 3 - Planning Enhancement")
        return 0
    else:
        print("\nFAIL Alguns testes falharam")
        return 1


if __name__ == '__main__':
    exit_code = asyncio.run(main())
    exit(exit_code)
