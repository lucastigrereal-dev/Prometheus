"""
PROMETHEUS V3 INTEGRATION - COMPREHENSIVE VALIDATION
Valida toda a integração V1+V2+V3
"""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

def print_section(title):
    """Print section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)

def print_result(test_name, passed, details=""):
    """Print test result"""
    status = "[PASS]" if passed else "[FAIL]"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status}{reset} {test_name}")
    if details:
        print(f"       {details}")

def validate_imports():
    """Valida todos os imports V3"""
    print_section("VALIDATING V3 IMPORTS")

    tests = [
        ('ConfigManager', 'prometheus_v3.config.config_manager', 'ConfigManager'),
        ('ShadowExecutor', 'prometheus_v3.modules.shadow_executor', 'ShadowExecutor'),
        ('PrometheusScheduler', 'prometheus_v3.schedulers.prometheus_scheduler', 'PrometheusScheduler'),
        ('PlaybookExecutor', 'prometheus_v3.playbooks.playbook_executor', 'PlaybookExecutor'),
        ('GeminiProvider', 'prometheus_v3.providers.gemini_provider', 'GeminiProvider'),
        ('DashboardAPI', 'prometheus_v3.ui.dashboard', 'DashboardAPI'),
    ]

    passed = 0
    failed = 0

    for name, module_path, class_name in tests:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            print_result(name, True, f"{module_path}.{class_name}")
            passed += 1
        except Exception as e:
            error_msg = str(e).split('\n')[0]
            print_result(name, False, f"{error_msg}")
            failed += 1

    print(f"\nImport Tests: {passed} passed, {failed} failed")
    return failed == 0

def validate_integration_bridge():
    """Valida integration bridge"""
    print_section("VALIDATING INTEGRATION BRIDGE")

    try:
        from integration_bridge import PrometheusIntegrationBridge

        # Test initialization
        bridge = PrometheusIntegrationBridge(prefer_version=3, verbose=False)
        print_result("Bridge Initialization", True)

        # Get status
        status = bridge.get_status()

        # Test module counts
        v1_count = status['v1_count']
        v2_count = status['v2_count']
        v3_count = status['v3_count']
        total = status['total_modules']

        print_result("V1 Modules Loaded", v1_count > 0, f"{v1_count} modules")
        print_result("V2 Modules Loaded", v2_count > 0, f"{v2_count} modules")
        print_result("V3 Modules Loaded", v3_count > 0, f"{v3_count} modules")
        print_result("Total Modules", total >= 15, f"{total} modules")

        # Test module retrieval
        core_module = bridge.get_module('core')
        shadow_module = bridge.get_module('shadow_executor')
        dashboard_module = bridge.get_module('dashboard')

        print_result("Core Module Retrieval", core_module is not None)
        print_result("Shadow Executor Retrieval", shadow_module is not None)
        print_result("Dashboard Retrieval", dashboard_module is not None)

        # Test fallback system
        print_result("Prefer Version", status['prefer_version'] == 3, f"prefer_version={status['prefer_version']}")

        print(f"\nModules Summary:")
        print(f"  V1: {v1_count} | V2: {v2_count} | V3: {v3_count} | Total: {total}")

        return True

    except Exception as e:
        print_result("Integration Bridge", False, str(e))
        return False

def validate_configuration():
    """Valida arquivos de configuração"""
    print_section("VALIDATING CONFIGURATION")

    config_files = [
        ('V3 .env', Path(__file__).parent / 'prometheus_v3' / '.env'),
        ('V3 .env.example', Path(__file__).parent / 'prometheus_v3' / '.env.example'),
        ('V3 requirements.txt', Path(__file__).parent / 'prometheus_v3' / 'requirements.txt'),
    ]

    passed = 0
    for name, path in config_files:
        exists = path.exists()
        print_result(name, exists, str(path) if exists else "Not found")
        if exists:
            passed += 1

    # Check .env has API keys
    env_path = Path(__file__).parent / 'prometheus_v3' / '.env'
    if env_path.exists():
        content = env_path.read_text()
        has_anthropic = 'ANTHROPIC_API_KEY=' in content and 'sk-ant' in content
        has_openai = 'OPENAI_API_KEY=' in content
        has_supabase = 'SUPABASE_URL=' in content

        print_result("Anthropic API Key", has_anthropic)
        print_result("OpenAI API Key", has_openai)
        print_result("Supabase Config", has_supabase)

    return passed >= 2

def validate_structure():
    """Valida estrutura de diretórios V3"""
    print_section("VALIDATING V3 STRUCTURE")

    base = Path(__file__).parent / 'prometheus_v3'

    directories = [
        'config',
        'ui',
        'modules',
        'schedulers',
        'playbooks',
        'providers',
        'tests',
        'data',
        'logs',
    ]

    passed = 0
    for dir_name in directories:
        dir_path = base / dir_name
        exists = dir_path.exists() and dir_path.is_dir()
        print_result(f"Directory: {dir_name}", exists, str(dir_path))
        if exists:
            passed += 1

    return passed >= 7

def validate_dashboard():
    """Valida Dashboard API"""
    print_section("VALIDATING DASHBOARD")

    try:
        from prometheus_v3.ui.dashboard import DashboardAPI

        dashboard = DashboardAPI()
        print_result("Dashboard Initialization", True)
        print_result("FastAPI App Created", dashboard.app is not None)
        print_result("Routes Registered", len(dashboard.app.routes) > 0,
                     f"{len(dashboard.app.routes)} routes")
        print_result("WebSocket Queue", dashboard.command_queue is not None)

        return True
    except Exception as e:
        print_result("Dashboard", False, str(e))
        return False

def main():
    """Executa validação completa"""
    print("\n" + "=" * 70)
    print("  PROMETHEUS V3 INTEGRATION - COMPREHENSIVE VALIDATION")
    print("=" * 70)

    results = {}

    # Run all validations
    results['imports'] = validate_imports()
    results['bridge'] = validate_integration_bridge()
    results['config'] = validate_configuration()
    results['structure'] = validate_structure()
    results['dashboard'] = validate_dashboard()

    # Final summary
    print_section("VALIDATION SUMMARY")

    total_passed = sum(1 for v in results.values() if v)
    total_tests = len(results)

    for test_name, passed in results.items():
        print_result(test_name.upper(), passed)

    print(f"\n{'=' * 70}")
    print(f"  OVERALL: {total_passed}/{total_tests} test suites passed")

    if total_passed == total_tests:
        print("  STATUS: ✓ ALL VALIDATIONS PASSED")
    else:
        print(f"  STATUS: ✗ {total_tests - total_passed} test suite(s) failed")

    print("=" * 70)

    return total_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
