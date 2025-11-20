# PLANO OFICIAL DE INTEGRAÇÃO E CONSOLIDAÇÃO - PROMETHEUS V3.5

**Data**: 2025-11-20
**Arquiteto Supremo**: Claude Code (Sonnet 4.5)
**Objetivo**: Consolidar Prometheus Local removendo redundâncias e preservando sistema funcional

---

## DECISÃO ESTRATÉGICA PRINCIPAL

**CONCLUSÃO DA ANÁLISE COMPARATIVA**:

❌ **NÃO INTEGRAR** ZIP no LOCAL (ZIP é subset obsoleto)
✅ **LIMPAR E CONSOLIDAR** LOCAL (remover código obsoleto)
✅ **PRESERVAR** Prometheus Supreme V3.5 (sistema atual funcional)

**RAZÃO**:
O Prometheus V3.5 ZIP contém apenas 26 arquivos que JÁ EXISTEM no Prometheus LOCAL. O LOCAL é um superset completo com sistema unificado funcional, Knowledge Brain operacional, Dashboard, e 3 interfaces.

**ESTRATÉGIA**:
Este "plano de integração" é na verdade um **PLANO DE LIMPEZA E CONSOLIDAÇÃO** do Prometheus LOCAL para remover dívida técnica acumulada.

---

## PRINCÍPIOS FUNDAMENTAIS

### ✅ PROTEGER (Nunca Tocar)

1. **Knowledge Brain** 🔴 CRÍTICO
   - `knowledge/cleaned/` (426 JSONs)
   - ChromaDB data (6,973 chunks, $1.77)
   - `knowledge/backups/`

2. **Prometheus Supreme V3.5** 🔴 CRÍTICO
   - `prometheus_supreme.py`
   - `launch_supreme.py`
   - `prometheus_gui.py`
   - `prometheus_web.py`

3. **Prometheus V3 Core** 🔴 CRÍTICO
   - `prometheus_v3/` (86 arquivos)

4. **Dashboard** 🔴 CRÍTICO
   - `prometheus-dashboard/` (Next.js)
   - `dashboard_api/` (FastAPI)

5. **Runtime Operacional** 🔴 CRÍTICO
   - `runtime/` (índices, estados, backups)

6. **Configurações Ativas** 🟡 IMPORTANTE
   - `.env` (raiz) - após consolidação
   - `prometheus.yaml`

### ❌ REMOVER (Código Obsoleto)

1. **V1 Deprecated** 🗑️
   - `start_prometheus.py`
   - `prometheus_brain.py`
   - `prometheus_ui.py`
   - `skills/` (5 arquivos)
   - `memory/prometheus_memory.db`

2. **Backup Antigo** 🗑️
   - `backup_20251115_104711/` (2GB)

3. **Scripts Temporários** 🗑️ (15 arquivos)
   - `analyze_integration.py`
   - `check_credentials*.py`
   - `convert_json_to_txt.py`
   - `decode_jwt.py`
   - `fix_*.py`
   - `clean_*.py`
   - `split_*.py`

4. **Testes Desorganizados** 🗑️
   - 15 arquivos test_*.py na raiz

5. **Supabase Legacy** 🗑️
   - `supabase_schema.sql`
   - `prometheus_v3/knowledge/supabase_client.py`

### ⚙️ CONSOLIDAR (Unificar)

1. **Arquivos .env** (múltiplos → único)
2. **requirements.txt** (incompleto → completo)
3. **Testes** (raiz → tests/)
4. **Scripts utilitários** (raiz → tools/)

---

## FASES DE EXECUÇÃO

### FASE 0: PREPARAÇÃO E SEGURANÇA (OBRIGATÓRIA)

**Duração**: 10min
**Risco**: ZERO

**Ações**:

1. ✅ **Criar Backup Completo**
```bash
# Criar backup ANTES de qualquer mudança
cd C:\Users\lucas
tar -czf prometheus_backup_$(date +%Y%m%d_%H%M%S).tar.gz Prometheus/
```

2. ✅ **Verificar Git Status**
```bash
cd C:\Users\lucas\Prometheus
git status
git log -1  # Confirmar commit fb6f5ad
```

3. ✅ **Validar Sistema Funcional**
```bash
# Testar que sistema está funcional ANTES
python launch_supreme.py --test
```

4. ✅ **Criar Branch de Segurança**
```bash
git checkout -b prometheus_consolidation_safety
git push origin prometheus_consolidation_safety
```

**CHECKPOINT**: ✅ Backup criado, Git OK, Sistema testado

---

### FASE 1: ARQUIVAMENTO DO ZIP V3.5

**Duração**: 5min
**Risco**: ZERO

**Objetivo**: Arquivar ZIP V3.5 como referência histórica

**Ações**:

1. ✅ **Criar Diretório de Archive**
```bash
cd C:\Users\lucas\Prometheus
mkdir -p archive/prometheus_v3.5_zip_original
```

2. ✅ **Mover ZIP Extraído**
```bash
mv C:\Users\lucas\Prometheus_V3.5_EXTRACTED\prometheus_v3.5 \
   C:\Users\lucas\Prometheus\archive\prometheus_v3.5_zip_original\
```

3. ✅ **Mover ZIP Original**
```bash
mv C:\Users\lucas\Downloads\prometheus_v3.5.zip \
   C:\Users\lucas\Prometheus\archive\
```

4. ✅ **Criar README no Archive**
```bash
cat > archive/README.md << 'EOF'
# Prometheus V3.5 ZIP Archive

Este é o ZIP original do Prometheus V3.5 recebido em 19/11/2025.

**Status**: ARCHIVED (conteúdo já integrado no sistema principal)

**Conteúdo**: 26 arquivos Python (~54KB)
- browser_executor/
- dashboard_api/
- file_integrity/
- safe_write/
- supervisor/
- telemetry/
- tests/

**Nota**: Todo o código deste ZIP JÁ EXISTE em `prometheus_v3/`
e está integrado no sistema Prometheus Supreme V3.5.

**Data de Arquivamento**: 2025-11-20
EOF
```

**CHECKPOINT**: ✅ ZIP arquivado, não interferindo no sistema

---

### FASE 2: LIMPEZA V1 DEPRECATED

**Duração**: 15min
**Risco**: BAIXO (código não usado)

**Objetivo**: Remover sistema V1 deprecated

**ATENÇÃO**: V1 NÃO é usado por Supreme. Validar antes de deletar.

**Ações**:

1. ✅ **Verificar Referências a V1**
```bash
cd C:\Users\lucas\Prometheus
grep -r "prometheus_brain" --include="*.py" prometheus_supreme.py prometheus_gui.py prometheus_web.py
grep -r "start_prometheus" --include="*.py" prometheus_supreme.py prometheus_gui.py prometheus_web.py
grep -r "from skills" --include="*.py" prometheus_v3/
```

Se retornar VAZIO → Seguro deletar

2. ✅ **Mover V1 para Deprecated**
```bash
mkdir -p deprecated/v1_legacy
mv start_prometheus.py deprecated/v1_legacy/
mv prometheus_brain.py deprecated/v1_legacy/
mv prometheus_ui.py deprecated/v1_legacy/
mv skills/ deprecated/v1_legacy/
mv memory/prometheus_memory.db deprecated/v1_legacy/ 2>/dev/null
```

3. ✅ **Criar README no Deprecated**
```bash
cat > deprecated/README.md << 'EOF'
# Deprecated Code

Código obsoleto removido do sistema principal.

## V1 Legacy (2024)
Sistema original Prometheus V1 com 5 skills modulares.

**Status**: DEPRECATED em 15/11/2025
**Substituído por**: Prometheus V3.5 Supreme
**Pode ser deletado**: Sim (após 30 dias de validação)
EOF
```

4. ✅ **Testar Sistema Sem V1**
```bash
python launch_supreme.py --test
python prometheus_gui.py --test 2>/dev/null
```

**CHECKPOINT**: ✅ V1 removido, sistema funcional

---

### FASE 3: ORGANIZAÇÃO DE SCRIPTS E TESTES

**Duração**: 20min
**Risco**: BAIXO

**Objetivo**: Mover scripts temporários e testes para estrutura organizada

**Ações**:

1. ✅ **Criar Diretórios Organizados**
```bash
mkdir -p tools/utilities
mkdir -p tools/fixes
mkdir -p tools/converters
mkdir -p tests/integration
mkdir -p tests/validation
```

2. ✅ **Mover Scripts Utilitários**
```bash
# Utilities
mv check_credentials*.py tools/utilities/
mv analyze_integration.py tools/utilities/

# Fixes
mv fix_*.py tools/fixes/
mv clean_*.py tools/fixes/

# Converters
mv convert_*.py tools/converters/
mv json_to_text_converter.py tools/converters/
mv split_*.py tools/converters/
mv decode_jwt.py tools/converters/
```

3. ✅ **Mover Testes para Estrutura Organizada**
```bash
# Testes de Integração
mv test_*_integration.py tests/integration/ 2>/dev/null
mv test_v3*.py tests/integration/ 2>/dev/null
mv integration_bridge.py tests/integration/ 2>/dev/null

# Testes de Validação
mv test_browser_executor.py tests/validation/ 2>/dev/null
mv test_dashboard.py tests/validation/ 2>/dev/null
mv test_executor.py tests/validation/ 2>/dev/null
mv test_planner.py tests/validation/ 2>/dev/null
mv test_supervisor.py tests/validation/ 2>/dev/null
mv test_knowledge_bank.py tests/validation/ 2>/dev/null
mv test_supreme_integration.py tests/validation/ 2>/dev/null
mv test_unified_executor.py tests/validation/ 2>/dev/null
mv test_jarvis_e2e.py tests/validation/ 2>/dev/null
mv test_supabase_direct.py tests/validation/ 2>/dev/null

# Testes Triviais/Obsoletos para Deprecated
mv test_oi.py deprecated/ 2>/dev/null
mv test_final.py deprecated/ 2>/dev/null
mv test_import.py deprecated/ 2>/dev/null
```

4. ✅ **Criar README em Tools**
```bash
cat > tools/README.md << 'EOF'
# Prometheus Tools

Scripts utilitários para manutenção e desenvolvimento.

## Estrutura

- `utilities/` - Scripts de utilidades gerais
- `fixes/` - Scripts de correção e manutenção
- `converters/` - Scripts de conversão de dados

## Uso

Estes scripts NÃO fazem parte do sistema principal.
Use conforme necessário para tarefas administrativas.
EOF
```

**CHECKPOINT**: ✅ Scripts organizados, raiz limpa

---

### FASE 4: CONSOLIDAÇÃO DE CONFIGURAÇÕES

**Duração**: 30min
**Risco**: MÉDIO (afeta configurações)

**Objetivo**: Unificar .env e criar requirements.txt completo

**ATENÇÃO**: Esta fase modifica configurações. Backup já feito na FASE 0.

**Ações**:

1. ✅ **Analisar .env Files**
```bash
echo "=== .env RAIZ ===" && cat .env
echo "=== prometheus_v3/.env ===" && cat prometheus_v3/.env
```

2. ✅ **Consolidar .env (Manual - Revisar Duplicatas)**
```python
# Executar script Python para merge inteligente
python << 'PYTHON'
import os
from pathlib import Path

# Ler ambos .env
env_root = Path(".env").read_text() if Path(".env").exists() else ""
env_v3 = Path("prometheus_v3/.env").read_text() if Path("prometheus_v3/.env").exists() else ""

# Criar .env.backup
Path(".env.backup").write_text(env_root)
Path("prometheus_v3/.env.backup").write_text(env_v3)

# Merge (prioridade para raiz, adicionar chaves únicas de V3)
lines_root = {line.split('=')[0].strip(): line for line in env_root.splitlines() if '=' in line}
lines_v3 = {line.split('=')[0].strip(): line for line in env_v3.splitlines() if '=' in line}

merged = lines_root.copy()
for key, line in lines_v3.items():
    if key not in merged:
        merged[key] = line

# Escrever .env consolidado
with open(".env", "w") as f:
    f.write("# Prometheus V3.5 Supreme - Unified Configuration\n")
    f.write("# Generated: 2025-11-20\n\n")
    for line in sorted(merged.values()):
        f.write(line + "\n")

print("✅ .env consolidado criado")
print(f"Total de chaves: {len(merged)}")
PYTHON
```

3. ✅ **Atualizar prometheus_v3/.env para Apontar para Raiz**
```bash
cat > prometheus_v3/.env << 'EOF'
# Prometheus V3 Configuration
# Este arquivo agora usa as configurações da raiz
# Configurações principais em: ../env

# Se precisar de configs específicas de V3, adicione aqui
# Caso contrário, todas as configs estão em /.env
EOF
```

4. ✅ **Gerar requirements.txt Completo**
```bash
# Criar requirements.txt baseado nos imports reais
cat > requirements.txt << 'EOF'
# Prometheus V3.5 Supreme - Complete Dependencies
# Generated: 2025-11-20

# Core
python-dotenv>=1.0.0
requests>=2.31.0
docker>=7.0.0
open-interpreter>=0.3.0

# AI Providers
anthropic>=0.18.0
openai>=1.12.0
litellm>=1.30.0

# Knowledge & Memory
chromadb>=0.4.22
sentence-transformers>=2.5.0

# Web & API
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
websockets>=12.0
pydantic>=2.5.0

# Browser Automation
playwright>=1.40.0

# Data Processing
pyyaml>=6.0.0
tiktoken>=0.6.0
shortuuid>=1.0.11
markdown-it-py>=3.0.0
regex>=2023.12.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-mock>=3.12.0

# UI (Desktop)
# tkinter - Built-in on Windows

# Database
# sqlite3 - Built-in Python
EOF
```

5. ✅ **Validar Requirements**
```bash
# Criar venv temporário e testar
python -m venv test_venv
test_venv\Scripts\activate
pip install -r requirements.txt
deactivate
rm -rf test_venv
```

**CHECKPOINT**: ✅ .env consolidado, requirements.txt completo

---

### FASE 5: CORREÇÃO DE SYNTAX ERRORS

**Duração**: 1 hora
**Risco**: MÉDIO (modifica código)

**Objetivo**: Corrigir 2 syntax errors identificados

**ATENÇÃO**: Validar módulos após correção.

**Errors Identificados**:
1. `prometheus_v3/supervisor_ext/config_watcher.py` - linha 309
2. `prometheus_v3/telemetry_ext/integrity_metrics.py` - import error

**Ações**:

1. ✅ **Analisar Error 1: config_watcher.py**
```bash
python -m py_compile prometheus_v3/supervisor_ext/config_watcher.py
```

Se syntax error → Ler arquivo e corrigir linha 309

2. ✅ **Analisar Error 2: integrity_metrics.py**
```bash
python -c "from prometheus_v3.telemetry_ext import integrity_metrics"
```

Se import error → Verificar missing exports

3. ✅ **Opção Alternativa: Deprecate Módulos Quebrados**

Se correção for complexa, mover para deprecated:
```bash
mkdir -p deprecated/broken_modules
mv prometheus_v3/supervisor_ext/config_watcher.py deprecated/broken_modules/ 2>/dev/null
mv prometheus_v3/telemetry_ext/integrity_metrics.py deprecated/broken_modules/ 2>/dev/null
```

E atualizar __init__.py para não importar:
```python
# prometheus_v3/supervisor_ext/__init__.py
# Remover import de config_watcher se foi deprecado

# prometheus_v3/telemetry_ext/__init__.py
# Remover import de integrity_metrics se foi deprecado
```

4. ✅ **Testar Sistema Após Correções**
```bash
python launch_supreme.py --test
python -m pytest tests/ -v
```

**CHECKPOINT**: ✅ Syntax errors corrigidos ou módulos deprecados

---

### FASE 6: REMOÇÃO DE CÓDIGO LEGACY SUPABASE

**Duração**: 10min
**Risco**: BAIXO (código não usado)

**Objetivo**: Remover integração Supabase deprecated

**Ações**:

1. ✅ **Verificar Referências a Supabase**
```bash
grep -r "supabase" --include="*.py" prometheus_supreme.py prometheus_v3/ | grep -v "# DEPRECATED"
```

2. ✅ **Mover Código Supabase para Deprecated**
```bash
mkdir -p deprecated/supabase_legacy
mv supabase_schema.sql deprecated/supabase_legacy/
mv prometheus_v3/knowledge/supabase_client.py deprecated/supabase_legacy/ 2>/dev/null
```

3. ✅ **Atualizar knowledge/__init__.py**
```python
# Remover import de supabase_client se existir
# Sistema usa ChromaDB agora
```

**CHECKPOINT**: ✅ Supabase removido

---

### FASE 7: LIMPEZA DE BACKUP ANTIGO

**Duração**: 5min
**Risco**: ZERO (backup de backup)

**Objetivo**: Remover backup antigo de 2GB

**Ações**:

1. ✅ **Verificar Backup**
```bash
ls -lh backup_20251115_104711/
```

2. ✅ **Arquivar Externamente (Opcional)**
```bash
# Se quiser manter, compactar e mover
tar -czf backup_20251115_archived.tar.gz backup_20251115_104711/
mv backup_20251115_archived.tar.gz ~/backups/ 2>/dev/null
```

3. ✅ **Deletar Backup Local**
```bash
rm -rf backup_20251115_104711/
```

**CHECKPOINT**: ✅ 2GB liberados

---

### FASE 8: DOCUMENTAÇÃO E ATUALIZAÇÃO

**Duração**: 1 hora
**Risco**: ZERO

**Objetivo**: Atualizar documentação para refletir sistema consolidado

**Ações**:

1. ✅ **Criar README.md Principal Atualizado**
```markdown
# Prometheus V3.5 Supreme

Sistema unificado de IA multimodal com Knowledge Brain e Self-Improvement.

## Início Rápido

### Pré-requisitos
- Python 3.11+
- Node.js 18+ (para Dashboard)

### Instalação
\`\`\`bash
# 1. Clonar repositório
git clone <repo>
cd Prometheus

# 2. Instalar dependências Python
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 3. Configurar .env
cp .env.example .env
# Editar .env com suas API keys

# 4. Instalar Dashboard (opcional)
cd prometheus-dashboard
npm install
\`\`\`

### Uso

**Opção 1: Terminal CLI** (Recomendado)
\`\`\`bash
python launch_supreme.py
\`\`\`

**Opção 2: Desktop GUI**
\`\`\`bash
python prometheus_gui.py
\`\`\`

**Opção 3: Web Interface**
\`\`\`bash
python prometheus_web.py
# Acesse http://localhost:8100
\`\`\`

## Arquitetura

\`\`\`
Prometheus V3.5 Supreme
├─ Knowledge Brain (6,973 chunks)
├─ File Integrity System
├─ Safe Write Engine
├─ Supervisor (Code Review)
├─ Telemetry
└─ 3 Interfaces (CLI, Desktop, Web)
\`\`\`

## Documentação

- [Guia Rápido V3](QUICKSTART_V3.md)
- [Knowledge Brain](KNOWLEDGE_BRAIN_README.md)
- [Dashboard MVP](prometheus-dashboard/README.md)
- [Arquitetura Completa](PROMETHEUS_LOCAL_ANALYSIS.md)

## Status

✅ Sistema 100% funcional
✅ 9/9 testes de integração passando
✅ Última atualização: 2025-11-20

## Suporte

Para problemas, consulte a documentação ou abra issue.
\`\`\`
```

2. ✅ **Atualizar QUICKSTART_V3.md**

Adicionar seção sobre sistema consolidado.

3. ✅ **Criar ARCHITECTURE.md**

Documentar arquitetura atualizada pós-limpeza.

4. ✅ **Atualizar .gitignore**
```bash
cat >> .gitignore << 'EOF'

# Deprecated
deprecated/

# Archive
archive/

# Tools
tools/

# Test artifacts
tests/integration/*.log
tests/validation/*.log

# Backups
*.backup
*.tar.gz

# Environment
.env
*.db

# Runtime
runtime/
EOF
```

**CHECKPOINT**: ✅ Documentação atualizada

---

### FASE 9: VALIDAÇÃO FINAL

**Duração**: 30min
**Risco**: ZERO (apenas validação)

**Objetivo**: Validar que sistema consolidado está 100% funcional

**Ações**:

1. ✅ **Executar Todos os Testes**
```bash
# Testes unitários V3
python -m pytest prometheus_v3/tests/ -v

# Testes de integração
python -m pytest tests/integration/ -v

# Testes de validação
python -m pytest tests/validation/ -v
```

2. ✅ **Validar Knowledge Brain**
```bash
python knowledge_search.py "async tasks" --top-k 3
```

3. ✅ **Validar Dashboard**
```bash
# Backend
cd dashboard_api
python main.py &  # Porta 8000
sleep 5
curl http://localhost:8000/api/stats

# Frontend
cd ../prometheus-dashboard
npm run build
npm run dev &  # Porta 3001
sleep 10
curl http://localhost:3001
```

4. ✅ **Validar Supreme**
```bash
# Terminal CLI
python launch_supreme.py --test

# Desktop GUI (test mode)
python prometheus_gui.py --test

# Web Interface (test mode)
python prometheus_web.py --test
```

5. ✅ **Validar File Integrity**
```bash
python -c "
from prometheus_v3.file_integrity import FileIntegrityService
service = FileIntegrityService()
print('✅ File Integrity OK')
"
```

6. ✅ **Validar Safe Write**
```bash
python -c "
from prometheus_v3.safe_write import SafeWriter
writer = SafeWriter()
print('✅ Safe Write OK')
"
```

**CHECKPOINT**: ✅ Sistema 100% validado

---

### FASE 10: COMMIT E DOCUMENTAÇÃO

**Duração**: 15min
**Risco**: ZERO

**Objetivo**: Registrar consolidação no Git

**Ações**:

1. ✅ **Criar Branch de Consolidação**
```bash
git checkout -b prometheus_v3.5_consolidated
```

2. ✅ **Staged Changes**
```bash
git add .
git status  # Revisar mudanças
```

3. ✅ **Commit Consolidação**
```bash
git commit -m "$(cat <<'EOF'
feat: Consolidar Prometheus V3.5 - Limpeza Completa

FASE 1: Arquivamento
- Arquivado ZIP V3.5 em archive/
- Criado README de histórico

FASE 2: Limpeza V1
- Removido sistema V1 deprecated
- Movido para deprecated/v1_legacy/

FASE 3: Organização
- Scripts utilitários → tools/
- Testes → tests/integration e tests/validation/

FASE 4: Configurações
- Consolidado .env (raiz única)
- Criado requirements.txt completo (25 deps)

FASE 5: Correções
- Corrigido syntax errors em supervisor_ext/
- Corrigido import errors em telemetry_ext/

FASE 6: Supabase
- Removida integração Supabase deprecated
- Sistema usa ChromaDB

FASE 7: Backups
- Removido backup antigo (2GB)

FASE 8: Documentação
- Atualizado README.md principal
- Criado ARCHITECTURE.md
- Atualizado .gitignore

FASE 9: Validação
- ✅ Todos os testes passando
- ✅ Knowledge Brain OK (6,973 chunks)
- ✅ Dashboard OK
- ✅ Supreme OK

Resultado:
- Raiz limpa e organizada
- Sistema 100% funcional
- Dívida técnica eliminada
- Documentação atualizada

🤖 Generated with Claude Code (Anthropic)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

4. ✅ **Tag Release**
```bash
git tag -a v3.5-consolidated -m "Prometheus V3.5 - Consolidated and Clean"
```

5. ✅ **Push (Após Aprovação)**
```bash
# AGUARDAR AUTORIZAÇÃO DO USUÁRIO
# git push origin prometheus_v3.5_consolidated
# git push origin v3.5-consolidated
```

**CHECKPOINT**: ✅ Git commit criado, aguardando push

---

## VALIDAÇÃO DE SEGURANÇA

### Checklist Pré-Execução

Antes de executar QUALQUER fase, validar:

- [ ] Backup completo criado (FASE 0)
- [ ] Git status clean ou committed
- [ ] Branch de segurança criado
- [ ] Sistema testado e funcional
- [ ] Credenciais em .env NÃO vazadas no Git

### Checklist Durante Execução

Para CADA fase:

- [ ] Ler descrição e entender objetivo
- [ ] Validar risco da fase
- [ ] Executar comandos um por um
- [ ] Validar checkpoint ao final
- [ ] NÃO pular para próxima fase sem checkpoint OK

### Checklist Pós-Execução

Após TODAS as fases:

- [ ] Todos os checkpoints ✅
- [ ] Sistema 100% funcional
- [ ] Knowledge Brain preservado
- [ ] Dashboard funcional
- [ ] Testes passando
- [ ] Git commit criado
- [ ] Documentação atualizada

---

## ROLLBACK EM CASO DE PROBLEMA

Se QUALQUER fase falhar:

**OPÇÃO 1: Rollback da Fase**
```bash
# Desfazer mudanças da fase atual
git checkout .
git clean -fd
```

**OPÇÃO 2: Rollback Completo**
```bash
# Voltar ao estado inicial (FASE 0)
git checkout prometheus_consolidation_safety
git reset --hard
```

**OPÇÃO 3: Restaurar Backup**
```bash
# Restaurar do backup tar.gz criado na FASE 0
cd C:\Users\lucas
tar -xzf prometheus_backup_<timestamp>.tar.gz
```

---

## ESTIMATIVAS

### Tempo Total: 4-5 horas

| Fase | Duração | Risco | Pode Pular? |
|------|---------|-------|-------------|
| FASE 0: Preparação | 10min | ZERO | ❌ NÃO |
| FASE 1: Arquivar ZIP | 5min | ZERO | ❌ NÃO |
| FASE 2: Limpar V1 | 15min | BAIXO | ⚠️ Opcional |
| FASE 3: Organizar | 20min | BAIXO | ⚠️ Opcional |
| FASE 4: Configs | 30min | MÉDIO | ❌ NÃO |
| FASE 5: Syntax Errors | 1h | MÉDIO | ⚠️ Opcional |
| FASE 6: Supabase | 10min | BAIXO | ⚠️ Opcional |
| FASE 7: Backup | 5min | ZERO | ✅ Pode |
| FASE 8: Docs | 1h | ZERO | ⚠️ Opcional |
| FASE 9: Validação | 30min | ZERO | ❌ NÃO |
| FASE 10: Commit | 15min | ZERO | ❌ NÃO |

### Fases OBRIGATÓRIAS (Mínimo Viável):
- FASE 0: Preparação
- FASE 1: Arquivar ZIP
- FASE 4: Configs
- FASE 9: Validação
- FASE 10: Commit

**Tempo Mínimo**: 1h30min

---

## RESUMO EXECUTIVO

**Objetivo**: Consolidar Prometheus LOCAL removendo redundâncias

**Estratégia**: Não integrar ZIP (já existe). Limpar LOCAL.

**Fases**: 10 fases (4-5 horas total, ou 1h30min mínimo)

**Risco**: BAIXO (com backup e Git safety branch)

**Resultado Esperado**:
- ✅ Raiz limpa e organizada
- ✅ Sistema 100% funcional
- ✅ Dívida técnica eliminada
- ✅ Documentação atualizada
- ✅ Knowledge Brain preservado (6,973 chunks)
- ✅ requirements.txt completo
- ✅ .env consolidado

**Aprovação Necessária**: SIM (antes de FASE 5 - Ação)

---

**FIM DO PLANO DE INTEGRAÇÃO**

**Próximo Passo**: Aguardar autorização do usuário para executar.
