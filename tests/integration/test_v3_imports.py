"""
Test V3 imports
"""
import sys
import importlib
import traceback
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """Test all V3 critical imports"""

    modules_to_test = [
        # V3 Config
        ('prometheus_v3.config.config_manager', 'ConfigManager'),
        ('prometheus_v3.config.logging_config', 'setup_logging'),

        # V3 UI
        ('prometheus_v3.ui.dashboard', 'app'),

        # V3 Modules
        ('prometheus_v3.modules.shadow_executor', 'ShadowExecutor'),

        # V3 Schedulers
        ('prometheus_v3.schedulers.prometheus_scheduler', 'PrometheusScheduler'),

        # V3 Playbooks
        ('prometheus_v3.playbooks.playbook_executor', 'PlaybookExecutor'),

        # V3 Providers
        ('prometheus_v3.providers.gemini_provider', 'GeminiProvider'),

        # V3 Main
        ('prometheus_v3.main_v3_integrated', 'PrometheusV3'),
    ]

    results = {'success': [], 'failed': []}

    print("=" * 70)
    print("PROMETHEUS V3 - IMPORT TESTS")
    print("=" * 70)
    print()

    for module_path, class_name in modules_to_test:
        try:
            module = importlib.import_module(module_path)

            # Try to get the class if specified
            if class_name and hasattr(module, class_name):
                getattr(module, class_name)
                status = f"[OK] {module_path}.{class_name}"
            else:
                status = f"[OK] {module_path}"

            results['success'].append(module_path)
            print(f"\033[92m{status}\033[0m")

        except Exception as e:
            error_msg = str(e).split('\n')[0]  # First line only
            status = f"[FAIL] {module_path}: {error_msg}"
            results['failed'].append({
                'module': module_path,
                'error': error_msg,
                'traceback': traceback.format_exc()
            })
            print(f"\033[91m{status}\033[0m")

    print()
    print("=" * 70)
    print(f"Results: {len(results['success'])} SUCCESS / {len(results['failed'])} FAILED")
    print("=" * 70)

    if results['failed']:
        print("\nFAILED IMPORTS DETAILS:")
        print("-" * 70)
        for fail in results['failed']:
            print(f"\nModule: {fail['module']}")
            print(f"Error: {fail['error']}")
            print("Traceback (last 3 lines):")
            tb_lines = fail['traceback'].strip().split('\n')
            for line in tb_lines[-3:]:
                print(f"  {line}")

    return len(results['failed']) == 0

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
