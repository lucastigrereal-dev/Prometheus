import os
import sys
from pathlib import Path

# Fix encoding for Windows
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 70)
print("ANALISE DE INTEGRACAO PROMETHEUS V1 -> V2")
print("=" * 70)

# V1 modules (existing)
print("\nMODULOS V1 (EXISTENTES):")
print("-" * 70)

v1_modules = {
    'Core Brain': 'prometheus_brain.py',
    'UI': 'prometheus_ui.py',
    'Browser Control': 'skills/browser_control.py',
    'Memory System': 'skills/memory_system.py',
    'Vision Control': 'skills/vision_control.py',
    'Always On Voice': 'skills/always_on_voice.py',
    'AI Router': 'skills/ai_router.py',
    'AI Master Router': 'skills/ai_master_router.py',
}

for name, path in v1_modules.items():
    full_path = Path(path)
    if full_path.exists():
        size = full_path.stat().st_size
        print(f"[OK] {name:25s} {size:>8,} bytes  {path}")
    else:
        print(f"[--] {name:25s} {'':>8s}        {path} (not found)")

# V2 modules (new from Opus)
print("\n\nMODULOS V2 (NOVOS - OPUS):")
print("-" * 70)

downloads = Path("C:/Users/lucas/Downloads")
v2_modules = {
    'Core': 'prometheus_core.py',
    'Task Analyzer': 'task_analyzer.py',
    'Browser Controller': 'browser_controller.py',
    'Memory Manager': 'memory_manager.py',
    'Consensus Engine': 'consensus_engine.py',
    'Claude Provider': 'claude_provider.py',
    'GPT Provider': 'gpt_provider.py',
    'Main Entry': 'main.py',
    'Config': 'prometheus_config.yaml'
}

for name, filename in v2_modules.items():
    path = downloads / filename
    if path.exists():
        size = path.stat().st_size
        print(f"[OK] {name:25s} {size:>8,} bytes  {filename}")
    else:
        print(f"[--] {name:25s} {'':>8s}        {filename} (not found)")

# Migration mapping
print("\n\nMAPEAMENTO DE MIGRACAO:")
print("-" * 70)

mappings = [
    {
        'v1': 'Browser Control',
        'v2': 'Browser Controller',
        'strategy': 'MERGE - Manter V1, adicionar V2 em paralelo',
        'priority': 'MEDIUM'
    },
    {
        'v1': 'Memory System',
        'v2': 'Memory Manager',
        'strategy': 'MERGE - V2 tem vetorial, V1 tem basico',
        'priority': 'HIGH'
    },
    {
        'v1': 'AI Router',
        'v2': 'Consensus Engine',
        'strategy': 'ADD - V2 adiciona consenso multi-IA',
        'priority': 'HIGH'
    },
    {
        'v1': 'prometheus_brain.py',
        'v2': 'prometheus_core.py',
        'strategy': 'REPLACE - V2 e evolucao completa do V1',
        'priority': 'CRITICAL'
    },
    {
        'v1': 'N/A',
        'v2': 'Task Analyzer',
        'strategy': 'ADD - Novo modulo NLP',
        'priority': 'HIGH'
    },
    {
        'v1': 'N/A',
        'v2': 'Claude/GPT Providers',
        'strategy': 'ADD - Novos providers de IA',
        'priority': 'HIGH'
    },
]

for i, m in enumerate(mappings, 1):
    print(f"\n{i}. {m['v1']} -> {m['v2']}")
    print(f"   Strategy: {m['strategy']}")
    print(f"   Priority: {m['priority']}")

print("\n\nESTRATEGIA DE INTEGRACAO RECOMENDADA:")
print("-" * 70)
print("""
FASE 1 - PREPARACAO (AGORA):
  - Criar estrutura prometheus_v2/
  - Mover novos modulos para v2
  - Criar integration_bridge.py
  - Manter V1 funcionando

FASE 2 - INTEGRACAO (PROXIMO):
  - Adicionar providers de IA (Claude, GPT)
  - Integrar Task Analyzer com Brain V1
  - Adicionar Consensus Engine
  - Testar modulos V2 individualmente

FASE 3 - MIGRACAO (FUTURO):
  - Migrar Core Brain -> Core V2
  - Migrar Memory System -> Memory Manager
  - Substituir Browser Control -> Controller
  - Validar tudo funciona

FASE 4 - CONSOLIDACAO (FINAL):
  - Remover codigo V1 duplicado
  - Documentar mudancas
  - Limpar dependencias
""")

print("\nPROXIMA ACAO:")
print("-" * 70)
print("Criar estrutura prometheus_v2 e integration bridge")
print("=" * 70)
