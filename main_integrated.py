"""
PROMETHEUS INTEGRATED SYSTEM
Sistema unificado que usa o melhor de V1 e V2
Entry point principal para executar Prometheus com todos módulos
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

# Adiciona ao path
sys.path.insert(0, str(Path(__file__).parent))

from integration_bridge import PrometheusIntegrationBridge


class PrometheusIntegrated:
    """
    Sistema Prometheus Integrado

    Combina:
    - Módulos V1 estáveis (voice, vision, etc)
    - Módulos V2 novos (core, providers, consensus)
    """

    def __init__(self, prefer_v2: bool = True):
        """
        Args:
            prefer_v2: Se True, prioriza módulos V2 quando disponível
        """
        print("\n" + "=" * 70)
        print("PROMETHEUS INTEGRATED SYSTEM v1.0 + v2.0")
        print("=" * 70)

        self.bridge = PrometheusIntegrationBridge(prefer_v2=prefer_v2, verbose=True)
        self.components = {}

        self._initialize_components()

    def _initialize_components(self):
        """Inicializa componentes do sistema"""
        print("\n[INIT] Initializing components...")

        # Core (prioriza V2 se disponível)
        core_module = self.bridge.get_module('core')
        if core_module:
            try:
                self.components['core'] = core_module
                print("[INIT] ✓ Core initialized")
            except Exception as e:
                print(f"[INIT] ✗ Core initialization failed: {e}")

        # Task Analyzer (V2 only)
        task_analyzer = self.bridge.get_module('task_analyzer')
        if task_analyzer:
            try:
                self.components['task_analyzer'] = task_analyzer
                print("[INIT] ✓ Task Analyzer initialized (V2)")
            except Exception as e:
                print(f"[INIT] ✗ Task Analyzer initialization failed: {e}")

        # Consensus Engine (V2 only)
        consensus = self.bridge.get_module('consensus')
        if consensus:
            try:
                self.components['consensus'] = consensus
                print("[INIT] ✓ Consensus Engine initialized (V2)")
            except Exception as e:
                print(f"[INIT] ✗ Consensus initialization failed: {e}")

        # AI Providers (V2 only)
        claude = self.bridge.get_module('claude_provider')
        if claude:
            self.components['claude'] = claude
            print("[INIT] ✓ Claude Provider initialized (V2)")

        gpt = self.bridge.get_module('gpt_provider')
        if gpt:
            self.components['gpt'] = gpt
            print("[INIT] ✓ GPT Provider initialized (V2)")

        # Browser (V2 melhorado ou V1 fallback)
        browser = self.bridge.get_module('browser')
        if browser:
            self.components['browser'] = browser
            print("[INIT] ✓ Browser Controller initialized")

        # Memory (V2 vetorial ou V1 básica)
        memory = self.bridge.get_module('memory')
        if memory:
            self.components['memory'] = memory
            print("[INIT] ✓ Memory Manager initialized")

        # Voice (V1)
        voice = self.bridge.get_module('voice', version='v1')
        if voice:
            self.components['voice'] = voice
            print("[INIT] ✓ Voice System initialized (V1)")

        # Vision (V1)
        vision = self.bridge.get_module('vision', version='v1')
        if vision:
            self.components['vision'] = vision
            print("[INIT] ✓ Vision System initialized (V1)")

        print(f"\n[INIT] Total components loaded: {len(self.components)}")

    async def start(self):
        """Inicia o sistema"""
        print("\n" + "=" * 70)
        print("STARTING PROMETHEUS INTEGRATED SYSTEM")
        print("=" * 70)

        # Status
        self.show_status()

        # Aguarda comandos
        await self.command_loop()

    def show_status(self):
        """Exibe status do sistema"""
        print("\n[STATUS] System components:")
        print("-" * 70)
        for name, component in self.components.items():
            print(f"  ✓ {name:20s} {str(component)[:50]}")

        print("\n[STATUS] Available capabilities:")
        print("-" * 70)

        capabilities = []
        if 'core' in self.components:
            capabilities.append("Core orchestration")
        if 'task_analyzer' in self.components:
            capabilities.append("NLP task parsing")
        if 'consensus' in self.components:
            capabilities.append("Multi-AI consensus")
        if 'claude' in self.components:
            capabilities.append("Claude AI")
        if 'gpt' in self.components:
            capabilities.append("GPT-4 AI")
        if 'browser' in self.components:
            capabilities.append("Browser automation")
        if 'memory' in self.components:
            capabilities.append("Memory management")
        if 'voice' in self.components:
            capabilities.append("Voice commands")
        if 'vision' in self.components:
            capabilities.append("Vision processing")

        for cap in capabilities:
            print(f"  • {cap}")

        print("-" * 70)

    async def command_loop(self):
        """Loop de comandos interativo"""
        print("\n[READY] Prometheus is ready for commands!")
        print("Commands: status | modules | help | exit")
        print("-" * 70)

        while True:
            try:
                command = input("\nPrometheus> ").strip().lower()

                if not command:
                    continue

                if command == 'exit' or command == 'quit':
                    print("[EXIT] Shutting down Prometheus...")
                    break

                elif command == 'status':
                    self.show_status()

                elif command == 'modules':
                    self.bridge.list_modules()

                elif command == 'help':
                    self.show_help()

                elif command.startswith('test '):
                    module_name = command.split(' ', 1)[1]
                    await self.test_module(module_name)

                else:
                    print(f"[INFO] Command '{command}' not recognized. Type 'help' for commands.")

            except KeyboardInterrupt:
                print("\n[EXIT] Interrupted by user")
                break
            except Exception as e:
                print(f"[ERROR] {e}")

    def show_help(self):
        """Exibe ajuda"""
        print("\n" + "=" * 70)
        print("PROMETHEUS INTEGRATED - HELP")
        print("=" * 70)
        print("""
Available Commands:
  status          - Show system status
  modules         - List all available modules (V1 and V2)
  test <module>   - Test specific module
  help            - Show this help
  exit/quit       - Exit Prometheus

Examples:
  test core       - Test core module
  test browser    - Test browser controller
  test memory     - Test memory manager
        """)
        print("=" * 70)

    async def test_module(self, module_name: str):
        """Testa um módulo específico"""
        print(f"\n[TEST] Testing module: {module_name}")

        if module_name not in self.components:
            print(f"[TEST] ✗ Module '{module_name}' not loaded")
            return

        component = self.components[module_name]
        print(f"[TEST] Module type: {type(component)}")
        print(f"[TEST] ✓ Module '{module_name}' is loaded and ready")


async def main():
    """Main entry point"""
    try:
        # Cria sistema integrado
        prometheus = PrometheusIntegrated(prefer_v2=True)

        # Inicia
        await prometheus.start()

    except KeyboardInterrupt:
        print("\n[EXIT] Shutting down...")
    except Exception as e:
        print(f"\n[ERROR] Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║           PROMETHEUS INTEGRATED SYSTEM                            ║
    ║           V1 (Stable) + V2 (Next-Gen)                            ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """)

    asyncio.run(main())
