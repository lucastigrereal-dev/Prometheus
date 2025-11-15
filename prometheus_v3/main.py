"""
PROMETHEUS MAIN - Ponto de Entrada Principal
Sistema completo integrado e pronto para execução
"""

import asyncio
import sys
import os
import logging
import json
from typing import Dict, Any, Optional
from datetime import datetime
import signal

# Adiciona diretório ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Imports dos módulos do Prometheus
from prometheus_core import PrometheusCore
from task_analyzer import AdvancedTaskAnalyzer
from browser_controller import BrowserController
from memory_manager import MemoryManager, MemoryType
from consensus_engine import ConsensusEngine, ConsensusStrategy
from ai_providers.claude_provider import ClaudeProvider, ClaudeConfig
from ai_providers.gpt_provider import GPTProvider, GPTConfig

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='🔥 %(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('prometheus.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('PROMETHEUS')

# ============================================================================
# CONFIGURAÇÃO DO SISTEMA
# ============================================================================

class PrometheusConfig:
    """Configuração central do Prometheus"""
    
    # Carrega do arquivo YAML ou usa defaults
    @staticmethod
    def load():
        config_path = 'prometheus_config.yaml'
        
        if os.path.exists(config_path):
            import yaml
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Configuração padrão
            return {
                'system': {
                    'name': 'PROMETHEUS',
                    'version': '1.0.0-supreme',
                    'environment': 'development'
                },
                'core': {
                    'max_concurrent_tasks': 5,
                    'task_timeout_seconds': 3600,
                    'retry_max_attempts': 3
                },
                'ai_providers': {
                    'claude': {
                        'enabled': True,
                        'api_key': os.getenv('CLAUDE_API_KEY', ''),
                        'model': 'claude-3-opus-20240229'
                    },
                    'gpt4': {
                        'enabled': True,
                        'api_key': os.getenv('OPENAI_API_KEY', ''),
                        'model': 'gpt-4-turbo-preview'
                    }
                },
                'memory': {
                    'embedding_provider': 'openai',
                    'template_path': './templates'
                },
                'browser': {
                    'browser': 'chromium',
                    'headless': False,
                    'stealth_mode': True
                }
            }

# ============================================================================
# PROMETHEUS SYSTEM - Sistema Completo
# ============================================================================

class PrometheusSystem:
    """
    Sistema Prometheus completo - O Jarvis Real
    Integra todos os componentes em uma interface unificada
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or PrometheusConfig.load()
        self.running = False
        
        # Componentes principais
        self.core = None
        self.task_analyzer = None
        self.browser_controller = None
        self.memory_manager = None
        self.consensus_engine = None
        
        # Providers de IA
        self.claude_provider = None
        self.gpt_provider = None
        
        # Estado
        self.active_sessions = {}
        self.command_history = []
        
        logger.info(f"🚀 Initializing {self.config['system']['name']} v{self.config['system']['version']}")
    
    async def initialize(self) -> bool:
        """Inicializa todos os componentes"""
        try:
            logger.info("Starting initialization sequence...")
            
            # 1. Core
            logger.info("Initializing Core...")
            self.core = PrometheusCore()
            await self.core.initialize()
            
            # 2. Task Analyzer
            logger.info("Initializing Task Analyzer...")
            self.task_analyzer = AdvancedTaskAnalyzer()
            
            # 3. Memory Manager
            logger.info("Initializing Memory Manager...")
            self.memory_manager = MemoryManager(self.config.get('memory'))
            
            # 4. Consensus Engine
            logger.info("Initializing Consensus Engine...")
            self.consensus_engine = ConsensusEngine(self.config.get('consensus'))
            
            # 5. Browser Controller
            logger.info("Initializing Browser Controller...")
            self.browser_controller = BrowserController(self.config.get('browser'))
            await self.browser_controller.initialize()
            
            # 6. AI Providers
            await self._initialize_ai_providers()
            
            self.running = True
            logger.info("✅ PROMETHEUS FULLY OPERATIONAL")
            
            # Mensagem de boas-vindas
            await self._show_welcome_message()
            
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False
    
    async def _initialize_ai_providers(self):
        """Inicializa providers de IA"""
        
        # Claude
        if self.config['ai_providers']['claude']['enabled']:
            try:
                self.claude_provider = ClaudeProvider(
                    ClaudeConfig(
                        api_key=self.config['ai_providers']['claude']['api_key'],
                        model=self.config['ai_providers']['claude']['model']
                    )
                )
                logger.info("✅ Claude Provider ready")
            except Exception as e:
                logger.warning(f"Claude Provider failed: {e}")
        
        # GPT-4
        if self.config['ai_providers']['gpt4']['enabled']:
            try:
                self.gpt_provider = GPTProvider(
                    GPTConfig(
                        api_key=self.config['ai_providers']['gpt4']['api_key'],
                        model=self.config['ai_providers']['gpt4']['model']
                    )
                )
                logger.info("✅ GPT-4 Provider ready")
            except Exception as e:
                logger.warning(f"GPT-4 Provider failed: {e}")
    
    async def _show_welcome_message(self):
        """Mostra mensagem de boas-vindas"""
        print("\n" + "="*70)
        print("🔥 PROMETHEUS SUPREME - THE REAL JARVIS 🔥")
        print("="*70)
        print(f"Version: {self.config['system']['version']}")
        print(f"Environment: {self.config['system']['environment']}")
        print(f"Status: FULLY OPERATIONAL")
        print("\nCapabilities:")
        print("  ✅ Natural Language Understanding")
        print("  ✅ Multi-AI Orchestration")
        print("  ✅ Browser Automation")
        print("  ✅ Memory & Learning")
        print("  ✅ Autonomous Execution")
        print("\n" + "="*70)
        print("Ready for commands. Type 'help' for assistance.\n")
    
    async def execute_command(self, command: str) -> Dict[str, Any]:
        """
        Executa comando completo através de todo o pipeline
        """
        
        logger.info(f"📥 Command received: {command}")
        
        # Adiciona ao histórico
        self.command_history.append({
            'command': command,
            'timestamp': datetime.now().isoformat()
        })
        
        try:
            # 1. Analisa comando com NLP avançado
            analysis = self.task_analyzer.analyze(command)
            logger.info(f"Analysis complete: {len(analysis['subtasks'])} subtasks identified")
            
            # 2. Busca memórias relevantes
            relevant_memories = await self.memory_manager.recall(
                query=command,
                memory_types=[MemoryType.LONG_TERM, MemoryType.PROCEDURAL],
                limit=5
            )
            
            if relevant_memories:
                logger.info(f"Found {len(relevant_memories)} relevant memories")
            
            # 3. Verifica se tem template existente
            template = None
            if analysis['intents']:
                template = self.memory_manager.template_library.find_template(
                    task_type=analysis['intents'][0].name
                )
                if template:
                    logger.info(f"Using template: {template.name} (success rate: {template.success_rate:.2%})")
            
            # 4. Executa através do core
            result = await self.core.execute_command(command)
            
            # 5. Aprende com execução
            if result['success']:
                await self.memory_manager.learn_from_execution(
                    task_type=analysis['intents'][0].name if analysis['intents'] else 'generic',
                    steps=analysis['subtasks'],
                    result=result['result'],
                    success=True,
                    execution_time=result.get('execution_time', 0)
                )
            
            # 6. Armazena na memória
            await self.memory_manager.store(
                content=f"Command: {command}\nResult: {json.dumps(result, default=str)[:500]}",
                memory_type=MemoryType.EPISODIC,
                metadata={
                    'command': command,
                    'success': result['success'],
                    'task_id': result.get('task_id')
                },
                importance=0.7 if result['success'] else 0.3
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def interactive_mode(self):
        """Modo interativo via terminal"""
        
        print("\n🎯 INTERACTIVE MODE ACTIVATED")
        print("Type 'exit' to quit, 'help' for commands\n")
        
        while self.running:
            try:
                # Prompt
                command = await asyncio.get_event_loop().run_in_executor(
                    None,
                    input,
                    "PROMETHEUS> "
                )
                
                # Comandos especiais
                if command.lower() == 'exit':
                    break
                elif command.lower() == 'help':
                    self._show_help()
                    continue
                elif command.lower() == 'status':
                    self._show_status()
                    continue
                elif command.lower() == 'memory':
                    self._show_memory_stats()
                    continue
                elif command.lower() == 'clear':
                    os.system('cls' if os.name == 'nt' else 'clear')
                    continue
                
                # Executa comando
                result = await self.execute_command(command)
                
                # Mostra resultado
                if result['success']:
                    print(f"\n✅ SUCCESS")
                    if 'result' in result:
                        print(f"Result: {json.dumps(result['result'], indent=2, default=str)[:500]}")
                else:
                    print(f"\n❌ FAILED")
                    if 'error' in result:
                        print(f"Error: {result['error']}")
                
                print()
                
            except KeyboardInterrupt:
                print("\n\nInterrupted by user")
                break
            except Exception as e:
                logger.error(f"Interactive mode error: {e}")
                print(f"Error: {e}\n")
    
    def _show_help(self):
        """Mostra ajuda"""
        print("""
PROMETHEUS COMMANDS:
==================
Natural Language:
  - "Create a website for client X"
  - "Send message to all clients about promotion"
  - "Analyze last month sales data"
  - "Automate Instagram posting"
  
System Commands:
  help    - Show this help
  status  - Show system status
  memory  - Show memory statistics
  clear   - Clear screen
  exit    - Exit Prometheus
        """)
    
    def _show_status(self):
        """Mostra status do sistema"""
        status = self.core.get_status() if self.core else {'status': 'not initialized'}
        print(f"\nSystem Status:")
        print(json.dumps(status, indent=2))
    
    def _show_memory_stats(self):
        """Mostra estatísticas de memória"""
        if self.memory_manager:
            stats = self.memory_manager.get_stats()
            print(f"\nMemory Statistics:")
            print(json.dumps(stats, indent=2))
        else:
            print("Memory system not initialized")
    
    async def shutdown(self):
        """Desliga o sistema gracefully"""
        logger.info("Initiating shutdown sequence...")
        
        self.running = False
        
        # Desliga componentes
        if self.browser_controller:
            await self.browser_controller.close()
        
        if self.core:
            await self.core.shutdown()
        
        logger.info("✅ Shutdown complete")
    
    async def api_mode(self, host: str = '0.0.0.0', port: int = 8080):
        """Modo API REST"""
        
        try:
            from aiohttp import web
            
            # Rotas
            routes = web.RouteTableDef()
            
            @routes.post('/execute')
            async def execute_endpoint(request):
                data = await request.json()
                command = data.get('command')
                
                if not command:
                    return web.json_response(
                        {'error': 'No command provided'},
                        status=400
                    )
                
                result = await self.execute_command(command)
                return web.json_response(result)
            
            @routes.get('/status')
            async def status_endpoint(request):
                return web.json_response(self.core.get_status())
            
            @routes.get('/health')
            async def health_endpoint(request):
                return web.json_response({'status': 'healthy'})
            
            # Cria app
            app = web.Application()
            app.add_routes(routes)
            
            # Inicia servidor
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, host, port)
            
            logger.info(f"🌐 API Server running on http://{host}:{port}")
            await site.start()
            
            # Mantém rodando
            while self.running:
                await asyncio.sleep(1)
                
        except ImportError:
            logger.error("aiohttp not installed. Install with: pip install aiohttp")

# ============================================================================
# MAIN - Ponto de Entrada
# ============================================================================

async def main():
    """Função principal"""
    
    # Cria sistema
    prometheus = PrometheusSystem()
    
    # Inicializa
    if not await prometheus.initialize():
        logger.error("Failed to initialize Prometheus")
        return
    
    # Configura signal handlers
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        asyncio.create_task(prometheus.shutdown())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Determina modo de operação
    if len(sys.argv) > 1:
        mode = sys.argv[1]
        
        if mode == 'api':
            # Modo API
            await prometheus.api_mode()
        elif mode == 'execute':
            # Execução única
            if len(sys.argv) > 2:
                command = ' '.join(sys.argv[2:])
                result = await prometheus.execute_command(command)
                print(json.dumps(result, indent=2, default=str))
            else:
                print("Usage: python main.py execute <command>")
        else:
            print(f"Unknown mode: {mode}")
            print("Available modes: interactive, api, execute")
    else:
        # Modo interativo (padrão)
        await prometheus.interactive_mode()
    
    # Shutdown
    await prometheus.shutdown()

if __name__ == "__main__":
    # Roda o sistema
    asyncio.run(main())
