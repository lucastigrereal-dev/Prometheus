# Prometheus Tests

Suite de testes do Prometheus V3.5 Supreme.

## Estrutura

### integration/
Testes de integração entre módulos:
- `test_*_integration.py` - Testes de integração
- `test_v3*.py` - Testes específicos V3
- `integration_bridge.py` - Ponte de integração V1↔V2↔V3
- `validate_*.py` - Scripts de validação

### validation/
Testes de validação de componentes:
- `test_browser_executor.py` - Executor de browser
- `test_dashboard.py` - Dashboard MVP
- `test_executor.py` - Executor geral
- `test_planner.py` - Planner de tarefas
- `test_supervisor.py` - Supervisor de código
- `test_knowledge_bank.py` - Knowledge Brain
- `test_supreme_integration.py` - Integração Supreme
- `test_unified_executor.py` - Executor unificado
- `test_jarvis_e2e.py` - Testes E2E Jarvis
- `test_supabase_direct.py` - Testes Supabase (legacy)

## Executar Testes

### Todos os Testes
```bash
python -m pytest tests/ -v
```

### Apenas Integração
```bash
python -m pytest tests/integration/ -v
```

### Apenas Validação
```bash
python -m pytest tests/validation/ -v
```

### Teste Específico
```bash
python -m pytest tests/validation/test_dashboard.py -v
```

## Testes do V3 Core

Testes unitários dos módulos V3 estão em:
```
prometheus_v3/tests/
├── test_file_integrity.py
├── test_safe_write.py
├── test_supervisor.py
└── __init__.py
```

Execute:
```bash
python -m pytest prometheus_v3/tests/ -v
```

## Cobertura

Para verificar cobertura de testes:
```bash
pip install pytest-cov
python -m pytest tests/ --cov=prometheus_v3 --cov-report=html
```

---

**Organizados em**: 2025-11-20
**Consolidação**: Fase 3 de 10
