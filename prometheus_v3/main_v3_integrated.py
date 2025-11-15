#!/usr/bin/env python3
"""
PROMETHEUS V3 - MAIN INTEGRATION SCRIPT
Script principal que integra e inicializa todos os módulos
"""

import asyncio
import sys
import os
import signal
import logging
from pathlib import Path
from typing import Optional
import argparse

# Adiciona paths do projeto
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Imports dos módulos V3
from config.config_manager import ConfigManager, EnvironmentManager
from config.logging_config import LogManager
from schedulers.prometheus_scheduler import PrometheusScheduler
from modules.shadow_executor import ShadowExecutor, ExecutionMode
from ui.dashboard import DashboardAPI

# Imports da integration bridge (V1 e V2)
try:
    from integration_bridge import PrometheusIntegrationBridge
    BRIDGE_AVAILABLE = True
except ImportError:
    BRIDGE_AVAILABLE = False
    print("Integration bridge not available")

logger = logging.getLogger('PrometheusV3')

# ============================================================================
# PROMETHEUS V3 MAIN APPLICATION
# ============================================================================

class PrometheusV3:
    """
    Aplicação principal Prometheus V3
    Integra todos os módulos e gerencia o ciclo de vida
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Inicializa Prometheus V3"""
        
        self.config_path = config_path
        self.config = None
        self.components = {}
        self.running = False
        self.tasks = []
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        asyncio.create_task(self.shutdown())
    
    async def initialize(self):
        """Inicializa todos os componentes"""
        
        logger.info("="*60)
        logger.info("🔥 PROMETHEUS V3 INITIALIZATION")
        logger.info("="*60)
        
        # 1. Load environment
        logger.info("Loading environment variables...")
        EnvironmentManager.load_env_file()
        
        # 2. Load configuration
        logger.info("Loading configuration...")
        self.config = ConfigManager()
        if self.config_path:
            self.config.load(self.config_path)
        else:
            self.config.load()
        
        # Enable hot reload
        if self.config.get('runtime.hot_reload', False):
            self.config.enable_hot_reload()
        
        # 3. Setup logging
        logger.info("Setting up logging system...")
        log_config = {
            'level': self.config.get('logging.level', 'INFO'),
            'console': self.config.get('logging.handlers.console.enabled', True),
            'file': self.config.get('logging.handlers.file.enabled', True),
            'json': self.config.get('logging.handlers.remote.enabled', False),
            'log_dir': self.config.get('logging.handlers.file.path', 'logs').split('/')[0]
        }
        LogManager().setup_logging(log_config)
        
        # 4. Initialize Integration Bridge (V1 + V2)
        if BRIDGE_AVAILABLE and self.config.get('modules.v1.browser_control.enabled', True):
            logger.info("Initializing Integration Bridge...")
            try:
                self.components['bridge'] = PrometheusIntegrationBridge()
                await self.components['bridge'].initialize()
                logger.info("✅ Integration Bridge ready")
            except Exception as e:
                logger.error(f"Failed to initialize bridge: {e}")
                self.components['bridge'] = None
        
        # 5. Initialize Scheduler
        if self.config.get('scheduler.enabled', True):
            logger.info("Initializing Scheduler...")
            self.components['scheduler'] = PrometheusScheduler(
                self.config.get_all().get('scheduler', {})
            )
            logger.info("✅ Scheduler ready")
        
        # 6. Initialize Shadow Executor
        if self.config.get('runtime.shadow_mode', True):
            logger.info("Initializing Shadow Executor...")
            self.components['shadow'] = ShadowExecutor()
            logger.info("✅ Shadow Executor ready")
        
        # 7. Initialize Dashboard
        if self.config.get('ui.dashboard.enabled', True):
            logger.info("Initializing Dashboard...")
            self.components['dashboard'] = DashboardAPI()
            logger.info("✅ Dashboard ready")
        
        # 8. Load Playbook Executor
        if self.config.get('runtime.playbooks_enabled', True):
            logger.info("Initializing Playbook Executor...")
            from playbooks.playbook_executor import PlaybookExecutor
            self.components['playbook_executor'] = PlaybookExecutor()
            logger.info("✅ Playbook Executor ready")
        
        # 9. Initialize Providers
        await self._initialize_providers()
        
        logger.info("="*60)
        logger.info("✅ PROMETHEUS V3 INITIALIZATION COMPLETE")
        logger.info("="*60)
    
    async def _initialize_providers(self):
        """Inicializa providers de IA"""
        
        providers_initialized = []
        
        # Claude Provider
        if self.config.get('providers.claude.enabled', False):
            try:
                from providers.claude_provider import ClaudeProvider
                api_key = os.getenv('CLAUDE_API_KEY')
                if api_key:
                    self.components['claude'] = ClaudeProvider(self.config.get_all()['providers']['claude'])
                    providers_initialized.append('Claude')
            except Exception as e:
                logger.error(f"Failed to initialize Claude: {e}")
        
        # GPT Provider
        if self.config.get('providers.gpt4.enabled', False):
            try:
                from providers.gpt_provider import GPTProvider
                api_key = os.getenv('OPENAI_API_KEY')
                if api_key:
                    self.components['gpt4'] = GPTProvider(self.config.get_all()['providers']['gpt4'])
                    providers_initialized.append('GPT-4')
            except Exception as e:
                logger.error(f"Failed to initialize GPT-4: {e}")
        
        # Gemini Provider
        if self.config.get('providers.gemini.enabled', False):
            try:
                from providers.gemini_provider import GeminiProvider, GeminiConfig
                api_key = os.getenv('GEMINI_API_KEY')
                if api_key:
                    config = GeminiConfig(
                        api_key=api_key,
                        model=self.config.get('providers.gemini.model', 'gemini-pro')
                    )
                    self.components['gemini'] = GeminiProvider(config)
                    providers_initialized.append('Gemini')
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
        
        if providers_initialized:
            logger.info(f"✅ AI Providers initialized: {', '.join(providers_initialized)}")
        else:
            logger.warning("⚠️ No AI providers initialized")
    
    async def start(self):
        """Inicia todos os serviços"""
        
        logger.info("Starting Prometheus V3 services...")
        self.running = True
        
        # Start scheduler
        if 'scheduler' in self.components:
            self.components['scheduler'].start()
            logger.info("✅ Scheduler started")
        
        # Start dashboard in background
        if 'dashboard' in self.components:
            dashboard_task = asyncio.create_task(self._run_dashboard())
            self.tasks.append(dashboard_task)
            logger.info("✅ Dashboard started on http://localhost:8000")
        
        # Main loop
        logger.info("🚀 Prometheus V3 is running!")
        logger.info("Press Ctrl+C to stop")
        
        try:
            while self.running:
                await asyncio.sleep(1)
                
                # Periodic health check
                if int(asyncio.get_event_loop().time()) % 30 == 0:
                    await self.health_check()
        
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        
        finally:
            await self.shutdown()
    
    async def _run_dashboard(self):
        """Roda dashboard em background"""
        try:
            await asyncio.to_thread(
                self.components['dashboard'].run,
                host=self.config.get('ui.dashboard.host', '0.0.0.0'),
                port=self.config.get('ui.dashboard.port', 8000)
            )
        except Exception as e:
            logger.error(f"Dashboard error: {e}")
    
    async def health_check(self):
        """Verifica saúde dos componentes"""
        
        health_status = {
            'timestamp': asyncio.get_event_loop().time(),
            'components': {}
        }
        
        # Check each component
        for name, component in self.components.items():
            try:
                if hasattr(component, 'health_check'):
                    status = await component.health_check()
                    health_status['components'][name] = status
                else:
                    health_status['components'][name] = 'running'
            except Exception as e:
                health_status['components'][name] = f'error: {e}'
        
        # Log if any component is unhealthy
        unhealthy = [
            name for name, status in health_status['components'].items()
            if isinstance(status, str) and 'error' in status
        ]
        
        if unhealthy:
            logger.warning(f"Unhealthy components: {unhealthy}")
    
    async def shutdown(self):
        """Desliga todos os serviços"""
        
        logger.info("Shutting down Prometheus V3...")
        self.running = False
        
        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
        
        # Stop scheduler
        if 'scheduler' in self.components:
            self.components['scheduler'].stop()
        
        # Cleanup bridge
        if 'bridge' in self.components and self.components['bridge']:
            # Add bridge cleanup if needed
            pass
        
        logger.info("👋 Prometheus V3 shutdown complete")
    
    async def execute_command(self, command: str, mode: Optional[str] = None):
        """Executa comando usando Shadow Executor"""
        
        if 'shadow' not in self.components:
            logger.error("Shadow Executor not initialized")
            return None
        
        execution_mode = ExecutionMode.HYBRID
        if mode == 'shadow':
            execution_mode = ExecutionMode.SHADOW
        elif mode == 'real':
            execution_mode = ExecutionMode.REAL
        
        result = await self.components['shadow'].execute(
            command=command,
            mode=execution_mode
        )
        
        return result
    
    async def run_playbook(self, playbook_name: str, variables: dict):
        """Executa um playbook"""
        
        if 'playbook_executor' not in self.components:
            logger.error("Playbook Executor not initialized")
            return None
        
        result = await self.components['playbook_executor'].execute(
            playbook_name=playbook_name,
            variables=variables
        )
        
        return result

# ============================================================================
# CLI INTERFACE
# ============================================================================

async def main():
    """Main entry point"""
    
    parser = argparse.ArgumentParser(description='Prometheus V3 - Universal AI Assistant')
    parser.add_argument('--config', '-c', help='Path to config file')
    parser.add_argument('--mode', '-m', choices=['development', 'staging', 'production'],
                       default='development', help='Execution mode')
    parser.add_argument('--command', help='Execute single command and exit')
    parser.add_argument('--playbook', '-p', help='Run playbook')
    parser.add_argument('--var', '-v', action='append', help='Playbook variables (key=value)')
    parser.add_argument('--version', action='version', version='Prometheus V3.0')
    
    args = parser.parse_args()
    
    # Set environment
    os.environ['PROMETHEUS_ENV'] = args.mode
    
    # Create application
    app = PrometheusV3(config_path=args.config)
    
    try:
        # Initialize
        await app.initialize()
        
        # Execute command if provided
        if args.command:
            result = await app.execute_command(args.command)
            print(f"Result: {result}")
            return
        
        # Run playbook if provided
        if args.playbook:
            variables = {}
            if args.var:
                for var in args.var:
                    if '=' in var:
                        key, value = var.split('=', 1)
                        variables[key] = value
            
            result = await app.run_playbook(args.playbook, variables)
            print(f"Playbook result: {result}")
            return
        
        # Start services
        await app.start()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    
    finally:
        await app.shutdown()

if __name__ == "__main__":
    # Setup basic logging before app starts
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run application
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
