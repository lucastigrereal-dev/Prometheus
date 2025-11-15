"""
PROMETHEUS INTEGRATION VALIDATOR
Script de validação automática da integração V1+V2
"""

import sys
import os
from pathlib import Path

# Fix encoding
sys.stdout.reconfigure(encoding='utf-8')

def validate_structure():
    """Valida estrutura de diretórios"""
    print("\n[1/6] Validating directory structure...")

    required_dirs = [
        'prometheus_v2',
        'prometheus_v2/core',
        'prometheus_v2/ai_providers',
        'prometheus_v2/execution',
        'prometheus_v2/memory',
        'prometheus_v2/config',
        'skills',
    ]

    all_ok = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            print(f"  [OK] {dir_path}")
        else:
            print(f"  [ERROR] {dir_path} - NOT FOUND")
            all_ok = False

    return all_ok

def validate_files():
    """Valida arquivos essenciais"""
    print("\n[2/6] Validating essential files...")

    required_files = [
        'integration_bridge.py',
        'main_integrated.py',
        'prometheus_v2/core/prometheus_core.py',
        'prometheus_v2/core/consensus_engine.py',
        'prometheus_v2/ai_providers/claude_provider.py',
        'prometheus_v2/ai_providers/gpt_provider.py',
        'prometheus_v2/execution/browser_controller.py',
        'prometheus_v2/memory/memory_manager.py',
        'prometheus_v2/config/prometheus_config.yaml',
    ]

    all_ok = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists() and path.is_file():
            size = path.stat().st_size
            print(f"  [OK] {file_path} ({size:,} bytes)")
        else:
            print(f"  [ERROR] {file_path} - NOT FOUND")
            all_ok = False

    return all_ok

def validate_dependencies():
    """Valida dependências Python"""
    print("\n[3/6] Validating Python dependencies...")

    deps = {
        'redis': False,
        'supabase': False,
        'faiss': False,
        'sentence_transformers': False,
        'anthropic': False,
        'openai': False,
    }

    for dep_name in deps.keys():
        try:
            if dep_name == 'faiss':
                __import__('faiss')
            elif dep_name == 'sentence_transformers':
                __import__('sentence_transformers')
            else:
                __import__(dep_name)
            deps[dep_name] = True
            print(f"  [OK] {dep_name}")
        except ImportError:
            print(f"  [WARN] {dep_name} - not installed (optional)")

    # Essenciais
    required = ['anthropic', 'openai']
    all_ok = all(deps.get(dep, False) for dep in required)

    return all_ok

def validate_bridge():
    """Valida integration bridge"""
    print("\n[4/6] Validating integration bridge...")

    try:
        from integration_bridge import PrometheusIntegrationBridge

        bridge = PrometheusIntegrationBridge(verbose=False)
        status = bridge.get_status()

        print(f"  [OK] Bridge initialized")
        print(f"  [OK] V1 modules: {status['v1_count']}")
        print(f"  [OK] V2 modules: {status['v2_count']}")
        print(f"  [OK] Total modules: {status['v1_count'] + status['v2_count']}")

        # Valida módulos essenciais
        essential_v2 = ['core', 'browser', 'memory']
        for mod in essential_v2:
            module = bridge.get_module(mod)
            if module:
                print(f"  [OK] {mod} accessible")
            else:
                print(f"  [ERROR] {mod} not accessible")
                return False

        return True

    except Exception as e:
        print(f"  [ERROR] Bridge validation failed: {e}")
        return False

def validate_v2_modules():
    """Valida módulos V2 individualmente"""
    print("\n[5/6] Validating V2 modules individually...")

    modules = {
        'Core': 'prometheus_v2.core.prometheus_core',
        'Task Analyzer': 'prometheus_v2.core.task_analyzer',
        'Consensus Engine': 'prometheus_v2.core.consensus_engine',
        'Claude Provider': 'prometheus_v2.ai_providers.claude_provider',
        'GPT Provider': 'prometheus_v2.ai_providers.gpt_provider',
        'Browser Controller': 'prometheus_v2.execution.browser_controller',
        'Memory Manager': 'prometheus_v2.memory.memory_manager',
    }

    loaded = 0
    for name, module_path in modules.items():
        try:
            __import__(module_path)
            print(f"  [OK] {name}")
            loaded += 1
        except ImportError as e:
            # Task Analyzer pode falhar (spacy)
            if 'spacy' in str(e):
                print(f"  [WARN] {name} - needs spacy (optional)")
            else:
                print(f"  [ERROR] {name} - {e}")

    print(f"\n  Total: {loaded}/{len(modules)} modules loaded")
    return loaded >= 6  # Pelo menos 6 dos 7 (Task Analyzer é opcional)

def validate_python_version():
    """Valida versão do Python"""
    print("\n[6/6] Validating Python version...")

    version = sys.version_info
    print(f"  Python {version.major}.{version.minor}.{version.micro}")

    if version.major == 3 and version.minor >= 10:
        print(f"  [OK] Python version compatible")
        return True
    else:
        print(f"  [WARN] Python 3.10+ recommended")
        return True  # Warning, not error

def main():
    """Run all validations"""
    print("=" * 70)
    print("PROMETHEUS INTEGRATION VALIDATION")
    print("=" * 70)

    results = {
        'Structure': validate_structure(),
        'Files': validate_files(),
        'Dependencies': validate_dependencies(),
        'Bridge': validate_bridge(),
        'V2 Modules': validate_v2_modules(),
        'Python': validate_python_version(),
    }

    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)

    for test, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {test}")

    # Overall
    all_passed = all(results.values())

    print("\n" + "=" * 70)
    if all_passed:
        print("RESULT: ALL VALIDATIONS PASSED!")
        print("\nSystem is ready for use:")
        print("  .venv\\Scripts\\python.exe main_integrated.py")
    else:
        print("RESULT: SOME VALIDATIONS FAILED")
        print("\nCheck errors above and fix before using.")
    print("=" * 70)

    return 0 if all_passed else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
