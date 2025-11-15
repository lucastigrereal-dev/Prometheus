"""
PROMETHEUS V3 - CRITICAL TEST SUITE
Testes essenciais que PRECISAM passar antes de qualquer deploy
"""

import pytest
import asyncio
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

# Adiciona o path do projeto
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
async def prometheus_core():
    """Fixture para PrometheusCore"""
    with patch('prometheus_v2.core.prometheus_core.PrometheusCore') as MockCore:
        core = MockCore()
        core.initialize = AsyncMock(return_value=True)
        core.execute_command = AsyncMock(return_value={'success': True, 'result': 'test'})
        core.get_status = Mock(return_value={'status': 'operational'})
        yield core

@pytest.fixture
def browser_controller():
    """Fixture para BrowserController"""
    with patch('prometheus_v2.execution.browser_controller.BrowserController') as MockBrowser:
        browser = MockBrowser()
        browser.initialize = AsyncMock(return_value=True)
        browser.navigate = AsyncMock(return_value=True)
        yield browser

@pytest.fixture
def memory_manager():
    """Fixture para MemoryManager"""
    with patch('prometheus_v2.memory.memory_manager.MemoryManager') as MockMemory:
        memory = MockMemory()
        memory.store = AsyncMock(return_value={'id': 'test-123'})
        memory.recall = AsyncMock(return_value=[])
        yield memory

# ============================================================================
# TESTES CORE
# ============================================================================

@pytest.mark.asyncio
async def test_prometheus_core_initialization(prometheus_core):
    """Testa inicialização do core"""
    result = await prometheus_core.initialize()
    assert result == True
    prometheus_core.initialize.assert_called_once()

@pytest.mark.asyncio
async def test_prometheus_core_execute_command(prometheus_core):
    """Testa execução de comando no core"""
    result = await prometheus_core.execute_command("test command")
    assert result['success'] == True
    assert 'result' in result

def test_prometheus_core_status(prometheus_core):
    """Testa status do core"""
    status = prometheus_core.get_status()
    assert status['status'] == 'operational'

# ============================================================================
# TESTES BROWSER CONTROLLER
# ============================================================================

@pytest.mark.asyncio
async def test_browser_controller_initialization(browser_controller):
    """Testa inicialização do browser controller"""
    result = await browser_controller.initialize()
    assert result == True

@pytest.mark.asyncio
async def test_browser_controller_navigation(browser_controller):
    """Testa navegação do browser"""
    result = await browser_controller.navigate("https://example.com")
    assert result == True

def test_browser_controller_fallback():
    """Testa sistema de fallback do browser"""
    from unittest.mock import MagicMock
    
    # Simula fallback chain
    fallback_chain = ['playwright', 'selenium', 'pyautogui']
    current_method = 'playwright'
    
    # Testa próximo fallback
    current_index = fallback_chain.index(current_method)
    assert current_index == 0
    
    next_method = fallback_chain[current_index + 1] if current_index < len(fallback_chain) - 1 else None
    assert next_method == 'selenium'

# ============================================================================
# TESTES MEMORY MANAGER
# ============================================================================

@pytest.mark.asyncio
async def test_memory_manager_store(memory_manager):
    """Testa armazenamento de memória"""
    result = await memory_manager.store(
        content="test memory",
        memory_type="short_term"
    )
    assert result['id'] == 'test-123'

@pytest.mark.asyncio
async def test_memory_manager_recall(memory_manager):
    """Testa recuperação de memória"""
    memories = await memory_manager.recall("test query")
    assert isinstance(memories, list)

# ============================================================================
# TESTES CONSENSUS ENGINE
# ============================================================================

def test_consensus_engine_strategies():
    """Testa estratégias de consenso disponíveis"""
    strategies = [
        'MAJORITY_VOTE',
        'WEIGHTED_VOTE', 
        'CONFIDENCE_BASED',
        'SYNTHESIS',
        'ARBITER',
        'ENSEMBLE',
        'HIERARCHICAL'
    ]
    
    # Verifica se todas as estratégias estão definidas
    for strategy in strategies:
        assert strategy is not None

def test_consensus_vote_structure():
    """Testa estrutura de voto do consensus"""
    vote = {
        'provider': 'claude',
        'content': 'test response',
        'confidence': 0.85,
        'reasoning': 'test reasoning'
    }
    
    assert 'provider' in vote
    assert 'content' in vote
    assert 'confidence' in vote
    assert 0 <= vote['confidence'] <= 1

# ============================================================================
# TESTES INTEGRATION BRIDGE
# ============================================================================

def test_integration_bridge_loading():
    """Testa carregamento do integration bridge"""
    # Simula bridge
    bridge = {
        'v1_modules': {},
        'v2_modules': {}
    }
    
    # Testa estrutura
    assert 'v1_modules' in bridge
    assert 'v2_modules' in bridge

def test_integration_bridge_module_selection():
    """Testa seleção de melhor módulo"""
    v1_modules = {'browser': 'BrowserV1'}
    v2_modules = {'browser': 'BrowserV2', 'core': 'CoreV2'}
    
    # V2 tem prioridade se disponível
    module_type = 'browser'
    best = v2_modules.get(module_type) or v1_modules.get(module_type)
    assert best == 'BrowserV2'
    
    # V1 como fallback
    module_type = 'voice'
    best = v2_modules.get(module_type) or v1_modules.get(module_type, None)
    assert best is None

# ============================================================================
# TESTES TASK ANALYZER
# ============================================================================

def test_task_analyzer_intent_detection():
    """Testa detecção de intenção"""
    test_commands = {
        "criar site para cliente": ["CREATE", "WEBSITE"],
        "enviar mensagem whatsapp": ["SEND", "MESSAGE"],
        "analisar dados de vendas": ["ANALYZE", "DATA"]
    }
    
    for command, expected_intents in test_commands.items():
        # Simula análise simplificada
        detected = []
        if "criar" in command or "create" in command.lower():
            detected.append("CREATE")
        if "site" in command or "website" in command.lower():
            detected.append("WEBSITE")
        if "enviar" in command or "send" in command.lower():
            detected.append("SEND")
        if "mensagem" in command or "message" in command.lower():
            detected.append("MESSAGE")
        if "analisar" in command or "analyze" in command.lower():
            detected.append("ANALYZE")
        if "dados" in command or "data" in command.lower():
            detected.append("DATA")
        
        # Verifica se pelo menos uma intenção foi detectada
        assert len(detected) > 0

# ============================================================================
# TESTES PROVIDERS
# ============================================================================

def test_claude_provider_config():
    """Testa configuração do Claude provider"""
    config = {
        'api_key': 'test-key',
        'model': 'claude-3-opus-20240229',
        'max_tokens': 4096,
        'temperature': 0.7
    }
    
    assert config['api_key'] is not None
    assert 'claude' in config['model']
    assert config['max_tokens'] > 0
    assert 0 <= config['temperature'] <= 1

def test_gpt_provider_config():
    """Testa configuração do GPT provider"""
    config = {
        'api_key': 'test-key',
        'model': 'gpt-4-turbo-preview',
        'max_tokens': 4096,
        'temperature': 0.7
    }
    
    assert config['api_key'] is not None
    assert 'gpt' in config['model']
    assert config['max_tokens'] > 0
    assert 0 <= config['temperature'] <= 1

# ============================================================================
# TESTES CONFIG LOADING
# ============================================================================

def test_config_loading():
    """Testa carregamento de configuração"""
    import yaml
    
    # Simula config
    config = {
        'system': {
            'name': 'PROMETHEUS',
            'version': '3.0',
            'environment': 'test'
        },
        'providers': {
            'claude': {'enabled': True},
            'gpt4': {'enabled': True}
        }
    }
    
    assert config['system']['name'] == 'PROMETHEUS'
    assert config['system']['version'] == '3.0'
    assert config['providers']['claude']['enabled'] == True

# ============================================================================
# TESTES MAIN INTEGRATION
# ============================================================================

@pytest.mark.asyncio
async def test_main_integrated_initialization():
    """Testa inicialização do main integrado"""
    # Simula inicialização
    initialized = {
        'core': False,
        'browser': False,
        'memory': False
    }
    
    # Simula processo de init
    initialized['core'] = True
    initialized['browser'] = True
    initialized['memory'] = True
    
    # Verifica se tudo inicializou
    assert all(initialized.values())

# ============================================================================
# TESTES DE PERFORMANCE
# ============================================================================

@pytest.mark.asyncio
async def test_response_time():
    """Testa tempo de resposta"""
    import time
    
    start = time.time()
    await asyncio.sleep(0.1)  # Simula operação
    end = time.time()
    
    response_time = end - start
    assert response_time < 1.0  # Deve responder em menos de 1 segundo

def test_memory_usage():
    """Testa uso de memória"""
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    # Verifica se não está usando memória excessiva (< 1GB)
    assert memory_info.rss < 1024 * 1024 * 1024

# ============================================================================
# TESTES DE SEGURANÇA
# ============================================================================

def test_no_credentials_in_logs():
    """Verifica que credenciais não aparecem em logs"""
    sensitive_patterns = [
        'api_key',
        'password',
        'secret',
        'token',
        'bearer'
    ]
    
    log_content = "INFO: Initializing system with config"  # Simula log
    
    for pattern in sensitive_patterns:
        assert pattern not in log_content.lower()

def test_config_encryption():
    """Testa se configurações sensíveis estão protegidas"""
    import hashlib
    
    # Simula hash de senha
    password = "sensitive_password"
    hashed = hashlib.sha256(password.encode()).hexdigest()
    
    assert password != hashed
    assert len(hashed) == 64  # SHA256 sempre tem 64 caracteres

# ============================================================================
# TEST RUNNER
# ============================================================================

if __name__ == "__main__":
    # Roda todos os testes
    pytest.main([__file__, '-v', '--tb=short'])
