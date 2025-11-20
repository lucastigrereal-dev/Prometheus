"""
PROMETHEUS INTEGRATION BRIDGE
Conecta Prometheus V1 (existente) com V2 (novos módulos Opus)
Permite usar ambas versões em harmonia durante migração gradual
"""

import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Adiciona paths
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir / "prometheus_v2"))
sys.path.insert(0, str(current_dir / "skills"))


class PrometheusIntegrationBridge:
    """
    Ponte de integração entre V1, V2 e V3

    Permite:
    - Usar módulos V1 que já funcionam (stable)
    - Integrar módulos V2 gradualmente (opus)
    - Integrar módulos V3 (next-gen)
    - Fallback automático: V3 -> V2 -> V1
    - Logging de qual versão está sendo usada
    """

    def __init__(self, prefer_version: int = 3, verbose: bool = True):
        """
        Args:
            prefer_version: Versão preferida (3, 2 ou 1). Default: 3
            verbose: Se True, exibe logs de qual módulo foi carregado
        """
        self.prefer_version = prefer_version
        self.verbose = verbose

        self.v1_modules: Dict[str, Any] = {}
        self.v2_modules: Dict[str, Any] = {}
        self.v3_modules: Dict[str, Any] = {}

        self._load_modules()

    def _log(self, message: str):
        """Log condicional"""
        if self.verbose:
            print(f"[BRIDGE] {message}")

    def _load_modules(self):
        """Carrega módulos de todas versões"""
        self._log("Iniciando carregamento de módulos...")

        # === V1 MODULES (Existentes - Stable) ===
        self._load_v1_core()
        self._load_v1_skills()

        # === V2 MODULES (Opus - Enhanced) ===
        self._load_v2_core()
        self._load_v2_providers()
        self._load_v2_execution()
        self._load_v2_memory()

        # === V3 MODULES (Next-Gen - Enterprise) ===
        self._load_v3_core()
        self._load_v3_ui()
        self._load_v3_modules()
        self._load_v3_schedulers()

        self._log(f"V1 modules loaded: {len(self.v1_modules)}")
        self._log(f"V2 modules loaded: {len(self.v2_modules)}")
        self._log(f"V3 modules loaded: {len(self.v3_modules)}")

    def _load_v1_core(self):
        """Carrega núcleo V1"""
        try:
            from prometheus_brain import PrometheusCore as V1Core
            self.v1_modules['core'] = V1Core
            self._log("[OK] V1 Core Brain loaded")
        except Exception as e:
            self._log(f"[ERROR] V1 Core Brain not loaded: {e}")

    def _load_v1_skills(self):
        """Carrega skills V1"""
        skills = {
            'browser': 'browser_control',
            'memory': 'memory_system',
            'vision': 'vision_control',
            'voice': 'always_on_voice',
            'ai_router': 'ai_router',
            'ai_master': 'ai_master_router',
        }

        for key, module_name in skills.items():
            try:
                module = __import__(module_name)
                # Tenta pegar a classe principal
                classes = [name for name in dir(module) if not name.startswith('_')]
                if classes:
                    self.v1_modules[key] = module
                    self._log(f"[OK] V1 {key} loaded ({module_name})")
            except Exception as e:
                self._log(f"[X] V1 {key} not loaded: {e}")

    def _load_v2_core(self):
        """Carrega núcleo V2"""
        try:
            from prometheus_v2.core.prometheus_core import PrometheusCore as V2Core
            self.v2_modules['core'] = V2Core
            self._log("[OK] V2 Core loaded")
        except Exception as e:
            self._log(f"[X] V2 Core not loaded: {e}")

        try:
            from prometheus_v2.core.task_analyzer import TaskAnalyzer
            self.v2_modules['task_analyzer'] = TaskAnalyzer
            self._log("[OK] V2 Task Analyzer loaded")
        except Exception as e:
            self._log(f"[X] V2 Task Analyzer not loaded: {e}")

        try:
            from prometheus_v2.core.consensus_engine import ConsensusEngine
            self.v2_modules['consensus'] = ConsensusEngine
            self._log("[OK] V2 Consensus Engine loaded")
        except Exception as e:
            self._log(f"[X] V2 Consensus Engine not loaded: {e}")

    def _load_v2_providers(self):
        """Carrega providers V2"""
        try:
            from prometheus_v2.ai_providers.claude_provider import ClaudeProvider
            self.v2_modules['claude_provider'] = ClaudeProvider
            self._log("[OK] V2 Claude Provider loaded")
        except Exception as e:
            self._log(f"[X] V2 Claude Provider not loaded: {e}")

        try:
            from prometheus_v2.ai_providers.gpt_provider import GPTProvider
            self.v2_modules['gpt_provider'] = GPTProvider
            self._log("[OK] V2 GPT Provider loaded")
        except Exception as e:
            self._log(f"[X] V2 GPT Provider not loaded: {e}")

    def _load_v2_execution(self):
        """Carrega execution V2"""
        try:
            from prometheus_v2.execution.browser_controller import BrowserController
            self.v2_modules['browser'] = BrowserController
            self._log("[OK] V2 Browser Controller loaded")
        except Exception as e:
            self._log(f"[X] V2 Browser Controller not loaded: {e}")

    def _load_v2_memory(self):
        """Carrega memory V2"""
        try:
            from prometheus_v2.memory.memory_manager import MemoryManager
            self.v2_modules['memory'] = MemoryManager
            self._log("[OK] V2 Memory Manager loaded")
        except Exception as e:
            self._log(f"[X] V2 Memory Manager not loaded: {e}")

    def _load_v3_core(self):
        """Carrega núcleo V3"""
        try:
            from prometheus_v3.config.config_manager import ConfigManager
            self.v3_modules['config_manager'] = ConfigManager
            self._log("[OK] V3 Config Manager loaded")
        except Exception as e:
            self._log(f"[X] V3 Config Manager not loaded: {e}")

        try:
            from prometheus_v3.config.logging_config import setup_logging
            self.v3_modules['logging_config'] = setup_logging
            self._log("[OK] V3 Logging Config loaded")
        except Exception as e:
            self._log(f"[X] V3 Logging Config not loaded: {e}")

        try:
            from prometheus_v3.main_v3_integrated import PrometheusV3
            self.v3_modules['core'] = PrometheusV3
            self._log("[OK] V3 Core loaded")
        except Exception as e:
            self._log(f"[X] V3 Core not loaded: {e}")

    def _load_v3_ui(self):
        """Carrega UI V3"""
        try:
            from prometheus_v3.ui.dashboard import DashboardAPI, run_dashboard
            self.v3_modules['dashboard'] = DashboardAPI
            self.v3_modules['dashboard_runner'] = run_dashboard
            self._log("[OK] V3 Dashboard loaded")
        except Exception as e:
            self._log(f"[X] V3 Dashboard not loaded: {e}")

    def _load_v3_modules(self):
        """Carrega modules V3"""
        try:
            from prometheus_v3.modules.shadow_executor import ShadowExecutor
            self.v3_modules['shadow_executor'] = ShadowExecutor
            self._log("[OK] V3 Shadow Executor loaded")
        except Exception as e:
            self._log(f"[X] V3 Shadow Executor not loaded: {e}")

    def _load_v3_schedulers(self):
        """Carrega schedulers V3"""
        try:
            from prometheus_v3.schedulers.prometheus_scheduler import PrometheusScheduler
            self.v3_modules['scheduler'] = PrometheusScheduler
            self._log("[OK] V3 Scheduler loaded")
        except Exception as e:
            self._log(f"[X] V3 Scheduler not loaded: {e}")

        try:
            from prometheus_v3.playbooks.playbook_executor import PlaybookExecutor
            self.v3_modules['playbook_executor'] = PlaybookExecutor
            self._log("[OK] V3 Playbook Executor loaded")
        except Exception as e:
            self._log(f"[X] V3 Playbook Executor not loaded: {e}")

        try:
            from prometheus_v3.providers.gemini_provider import GeminiProvider
            self.v3_modules['gemini_provider'] = GeminiProvider
            self._log("[OK] V3 Gemini Provider loaded")
        except Exception as e:
            self._log(f"[X] V3 Gemini Provider not loaded: {e}")

    def get_module(self, module_type: str, version: Optional[str] = None):
        """
        Retorna módulo solicitado

        Args:
            module_type: Tipo do módulo ('core', 'browser', 'memory', etc)
            version: 'v1', 'v2', 'v3' ou None (usa prefer_version)

        Returns:
            Módulo ou None se não encontrado
        """
        # Seleção explícita de versão
        if version == 'v1':
            module = self.v1_modules.get(module_type)
            if module:
                self._log(f"Using V1 {module_type}")
                return module

        elif version == 'v2':
            module = self.v2_modules.get(module_type)
            if module:
                self._log(f"Using V2 {module_type}")
                return module

        elif version == 'v3':
            module = self.v3_modules.get(module_type)
            if module:
                self._log(f"Using V3 {module_type}")
                return module

        else:  # Auto select com fallback V3 -> V2 -> V1
            if self.prefer_version == 3:
                # Prioriza V3
                if module_type in self.v3_modules:
                    self._log(f"Using V3 {module_type} (preferred)")
                    return self.v3_modules[module_type]
                elif module_type in self.v2_modules:
                    self._log(f"Using V2 {module_type} (V3 fallback)")
                    return self.v2_modules[module_type]
                elif module_type in self.v1_modules:
                    self._log(f"Using V1 {module_type} (V2 fallback)")
                    return self.v1_modules[module_type]

            elif self.prefer_version == 2:
                # Prioriza V2
                if module_type in self.v2_modules:
                    self._log(f"Using V2 {module_type} (preferred)")
                    return self.v2_modules[module_type]
                elif module_type in self.v1_modules:
                    self._log(f"Using V1 {module_type} (V2 fallback)")
                    return self.v1_modules[module_type]
                elif module_type in self.v3_modules:
                    self._log(f"Using V3 {module_type} (only option)")
                    return self.v3_modules[module_type]

            else:  # prefer_version == 1
                # Prioriza V1
                if module_type in self.v1_modules:
                    self._log(f"Using V1 {module_type} (preferred)")
                    return self.v1_modules[module_type]
                elif module_type in self.v2_modules:
                    self._log(f"Using V2 {module_type} (V1 fallback)")
                    return self.v2_modules[module_type]
                elif module_type in self.v3_modules:
                    self._log(f"Using V3 {module_type} (only option)")
                    return self.v3_modules[module_type]

        self._log(f"[X] Module {module_type} not found in any version")
        return None

    def list_modules(self):
        """Lista todos os módulos disponíveis"""
        print("\n" + "=" * 70)
        print("PROMETHEUS MODULES AVAILABLE")
        print("=" * 70)

        print("\nV1 MODULES (Existentes - Stable):")
        print("-" * 70)
        for key in sorted(self.v1_modules.keys()):
            print(f"  [OK] {key}")

        print("\nV2 MODULES (Enhanced - Opus):")
        print("-" * 70)
        for key in sorted(self.v2_modules.keys()):
            print(f"  [OK] {key}")

        print("\nV3 MODULES (Next-Gen - Enterprise):")
        print("-" * 70)
        for key in sorted(self.v3_modules.keys()):
            print(f"  [OK] {key}")

        print("\nNEW IN V2 (não existem em V1):")
        print("-" * 70)
        v2_only = set(self.v2_modules.keys()) - set(self.v1_modules.keys())
        for key in sorted(v2_only):
            print(f"  + {key}")

        print("\nNEW IN V3 (não existem em V1/V2):")
        print("-" * 70)
        v3_only = set(self.v3_modules.keys()) - set(self.v2_modules.keys()) - set(self.v1_modules.keys())
        for key in sorted(v3_only):
            print(f"  + {key}")

        print("=" * 70)

    def get_status(self) -> Dict[str, Any]:
        """Retorna status detalhado"""
        return {
            'v1_count': len(self.v1_modules),
            'v2_count': len(self.v2_modules),
            'v3_count': len(self.v3_modules),
            'v1_modules': list(self.v1_modules.keys()),
            'v2_modules': list(self.v2_modules.keys()),
            'v3_modules': list(self.v3_modules.keys()),
            'prefer_version': self.prefer_version,
            'v2_only': list(set(self.v2_modules.keys()) - set(self.v1_modules.keys())),
            'v3_only': list(set(self.v3_modules.keys()) - set(self.v2_modules.keys()) - set(self.v1_modules.keys())),
            'total_modules': len(self.v1_modules) + len(self.v2_modules) + len(self.v3_modules),
        }


def test_bridge():
    """Teste do integration bridge"""
    print("\n" + "=" * 70)
    print("TESTING PROMETHEUS INTEGRATION BRIDGE V1+V2+V3")
    print("=" * 70)

    # Cria bridge
    bridge = PrometheusIntegrationBridge(prefer_version=3, verbose=True)

    print("\n" + "-" * 70)
    print("STATUS:")
    print("-" * 70)
    status = bridge.get_status()
    print(f"V1 modules: {status['v1_count']}")
    print(f"V2 modules: {status['v2_count']}")
    print(f"V3 modules: {status['v3_count']}")
    print(f"Total modules: {status['total_modules']}")
    print(f"Prefer version: {status['prefer_version']}")

    # Lista módulos
    bridge.list_modules()

    # Testa get_module
    print("\n" + "-" * 70)
    print("TESTING MODULE RETRIEVAL:")
    print("-" * 70)

    tests = ['core', 'browser', 'memory', 'claude_provider', 'task_analyzer',
             'dashboard', 'shadow_executor', 'scheduler', 'config_manager']
    for test in tests:
        module = bridge.get_module(test)
        if module:
            print(f"[OK] {test}: {module}")
        else:
            print(f"[X] {test}: Not found")

    print("\n" + "=" * 70)
    print("BRIDGE READY FOR USE!")
    print("=" * 70)

    return bridge


if __name__ == "__main__":
    bridge = test_bridge()
