# PROMETHEUS - ÍNDICE DE DOCUMENTAÇÃO

**Atualizado:** 2025-11-15
**Sistema:** V1 + V2 Integrated

---

## 📖 LEIA PRIMEIRO

### 🌟 Para Começar (HOJE)
1. **INTEGRATION_COMPLETE.md** ⭐⭐⭐
   - Resumo de tudo que foi feito
   - Como usar agora
   - Comandos principais

2. **QUICKSTART_V2.md** ⭐⭐⭐
   - Guia rápido de 30 segundos
   - Casos de uso
   - Exemplos práticos

### 🔧 Para Entender o Sistema
3. **INTEGRATION_REPORT.md** ⭐⭐
   - Relatório técnico completo
   - Arquitetura detalhada
   - Estratégia de migração

4. **README_V2.md** ⭐⭐
   - Overview geral
   - Recursos V1 + V2
   - Instalação e setup

---

## 📚 DOCUMENTAÇÃO POR CATEGORIA

### Início Rápido
| Arquivo | Descrição | Quando Ler |
|---------|-----------|------------|
| INTEGRATION_COMPLETE.md | Resumo completo da integração | Agora |
| QUICKSTART_V2.md | Guia rápido de uso | Agora |
| README_V2.md | Overview geral atualizado | Hoje |

### Técnica
| Arquivo | Descrição | Quando Ler |
|---------|-----------|------------|
| INTEGRATION_REPORT.md | Relatório técnico completo | Esta semana |
| MODO_ABSOLUTO_GUIA.md | Guia original V1 | Referência |
| prometheus_v2/config/prometheus_config.yaml | Configurações V2 | Quando configurar |

### Scripts
| Arquivo | Descrição | Como Usar |
|---------|-----------|-----------|
| launch.bat | Launcher Windows | Duplo clique |
| validate_integration.py | Validação automática | `python validate_integration.py` |
| analyze_integration.py | Análise de módulos | `python analyze_integration.py` |
| integration_bridge.py | Bridge V1↔V2 | `python integration_bridge.py` |
| main_integrated.py | Sistema integrado | `python main_integrated.py` |

---

## 🗂️ ESTRUTURA DE ARQUIVOS

### Raiz
```
C:\Users\lucas\Prometheus\
├── INTEGRATION_COMPLETE.md     ⭐ Leia primeiro!
├── QUICKSTART_V2.md             ⭐ Guia rápido
├── INTEGRATION_REPORT.md        📊 Relatório técnico
├── README_V2.md                 📄 README atualizado
├── DOCS_INDEX.md                📑 Este arquivo
├── launch.bat                   🚀 Launcher
├── integration_bridge.py        🌉 Bridge V1↔V2
├── main_integrated.py           🎯 Entry point
├── validate_integration.py      ✅ Validação
└── analyze_integration.py       🔍 Análise
```

### Módulos V2
```
prometheus_v2/
├── core/
│   ├── prometheus_core.py       💎 Núcleo V2
│   ├── task_analyzer.py         🧠 NLP parser
│   └── consensus_engine.py      🤝 Multi-IA consensus
├── ai_providers/
│   ├── claude_provider.py       🤖 Claude API
│   └── gpt_provider.py          🤖 GPT-4 API
├── execution/
│   └── browser_controller.py    🌐 Browser V2
├── memory/
│   └── memory_manager.py        💾 FAISS memory
└── config/
    └── prometheus_config.yaml   ⚙️ Config V2
```

### Módulos V1
```
skills/
├── browser_control.py           🌐 Browser V1
├── memory_system.py             💾 Memory V1
├── vision_control.py            👁️ Vision
├── always_on_voice.py           🎤 Voice
├── ai_master_router.py          🧭 AI Router
├── system_control.py            💻 System
├── n8n_client.py                🔗 n8n
├── whatsapp_api.py              💬 WhatsApp
├── rdstation_client.py          📧 RD Station
└── supabase_sync.py             🗄️ Supabase
```

---

## 🎯 FLUXO DE LEITURA RECOMENDADO

### Para Usuário Final
```
1. INTEGRATION_COMPLETE.md  (5 min)
   ↓
2. QUICKSTART_V2.md         (10 min)
   ↓
3. Execute: launch.bat
   ↓
4. Teste: comandos básicos
   ↓
5. Leia: README_V2.md       (15 min)
```

### Para Desenvolvedor
```
1. INTEGRATION_COMPLETE.md  (5 min)
   ↓
2. INTEGRATION_REPORT.md    (20 min)
   ↓
3. Estude: integration_bridge.py
   ↓
4. Estude: main_integrated.py
   ↓
5. Explore: prometheus_v2/
```

### Para Troubleshooting
```
1. Execute: validate_integration.py
   ↓
2. Se falhar: veja logs/prometheus.log
   ↓
3. Consulte: INTEGRATION_REPORT.md → Troubleshooting
   ↓
4. Se necessário: restaure backup/
```

---

## 🔍 ENCONTRE RAPIDAMENTE

### "Como eu...?"

#### Como iniciar o sistema?
→ `QUICKSTART_V2.md` seção "Início Rápido"

#### Como funciona a integração?
→ `INTEGRATION_REPORT.md` seção "Estratégia"

#### Como usar módulo X?
→ `QUICKSTART_V2.md` seção "Casos de Uso"

#### Como configurar APIs?
→ `README_V2.md` seção "Configuração"

#### Como validar sistema?
→ `INTEGRATION_COMPLETE.md` seção "Validação"

#### Como restaurar backup?
→ `INTEGRATION_COMPLETE.md` seção "Backups"

---

## 📊 DOCUMENTAÇÃO POR MÓDULO

### Core V2
- **Arquivo:** `prometheus_v2/core/prometheus_core.py`
- **Docs:** Ver código (bem comentado)
- **Config:** `prometheus_v2/config/prometheus_config.yaml`

### Consensus Engine
- **Arquivo:** `prometheus_v2/core/consensus_engine.py`
- **Uso:** `QUICKSTART_V2.md` → "Consenso Multi-IA"

### Claude Provider
- **Arquivo:** `prometheus_v2/ai_providers/claude_provider.py`
- **Config:** `.env` → `ANTHROPIC_API_KEY`

### GPT Provider
- **Arquivo:** `prometheus_v2/ai_providers/gpt_provider.py`
- **Config:** `.env` → `OPENAI_API_KEY`

### Memory Manager V2
- **Arquivo:** `prometheus_v2/memory/memory_manager.py`
- **Deps:** FAISS, sentence-transformers (já instalados)

### Browser Controller V2
- **Arquivo:** `prometheus_v2/execution/browser_controller.py`
- **Deps:** Playwright (verificar instalação)

---

## 🛠️ SCRIPTS E FERRAMENTAS

### Launcher
```bash
launch.bat
```
Menu interativo com opções:
1. Iniciar sistema integrado
2. Testar bridge
3. Validar sistema
4. Analisar integração

### Validação
```bash
python validate_integration.py
```
Valida:
- Estrutura de diretórios
- Arquivos essenciais
- Dependências Python
- Bridge V1↔V2
- Módulos V2
- Versão Python

### Análise
```bash
python analyze_integration.py
```
Mostra:
- Módulos V1 disponíveis
- Módulos V2 disponíveis
- Mapeamento de migração
- Estratégia sugerida

### Bridge
```bash
python integration_bridge.py
```
Testa:
- Carregamento V1
- Carregamento V2
- Roteamento inteligente
- Lista todos módulos

---

## 📝 LOGS E DEBUG

### Onde encontrar
```
logs/prometheus.log
```

### Como usar
```bash
# Ver últimas 50 linhas
tail -50 logs/prometheus.log

# Acompanhar em tempo real
tail -f logs/prometheus.log

# Buscar erro
grep ERROR logs/prometheus.log
```

---

## 🎓 TUTORIAIS E EXEMPLOS

### Tutorial 1: Primeiro Uso
**Arquivo:** `QUICKSTART_V2.md`
**Tempo:** 5 minutos
**Objetivo:** Iniciar e testar sistema

### Tutorial 2: Usar Bridge
**Arquivo:** `INTEGRATION_REPORT.md` → "Integration Bridge"
**Tempo:** 10 minutos
**Objetivo:** Entender roteamento V1↔V2

### Tutorial 3: Consenso Multi-IA
**Arquivo:** `QUICKSTART_V2.md` → "Casos de Uso"
**Tempo:** 15 minutos
**Objetivo:** Usar Claude + GPT juntos

---

## 🔗 LINKS RÁPIDOS

### Código Principal
- [Integration Bridge](integration_bridge.py)
- [Main Integrated](main_integrated.py)
- [Core V2](prometheus_v2/core/prometheus_core.py)

### Configuração
- [Config V2](prometheus_v2/config/prometheus_config.yaml)
- [Environment](.env)
- [Requirements](requirements.txt)

### Validação
- [Validate Script](validate_integration.py)
- [Analyze Script](analyze_integration.py)
- [Logs](logs/prometheus.log)

---

## 📅 HISTÓRICO DE VERSÕES

### v2.1 Integrated (2025-11-15)
- ✅ Integração V1+V2 completa
- ✅ 11 módulos totais
- ✅ FAISS vetorial ativo
- ✅ Consenso multi-IA
- ✅ Documentação completa

### v2.0 Absoluto (2025-11-13)
- Sistema V1 completo
- 8 skills integradas
- Voice, Vision, Browser
- n8n, WhatsApp, RD Station

---

## 🆘 SUPORTE RÁPIDO

### Problema Comum 1: Sistema não inicia
**Solução:** `INTEGRATION_COMPLETE.md` → "Suporte"

### Problema Comum 2: Módulo não carrega
**Solução:** `python validate_integration.py`

### Problema Comum 3: Dependência faltando
**Solução:** `pip install -r requirements.txt`

### Problema Comum 4: Erro de configuração
**Solução:** Verificar `.env` e `prometheus.yaml`

---

## 📞 CHECKLIST DIÁRIO

Use este checklist antes de começar:

```bash
# 1. Sistema OK?
cd C:\Users\lucas\Prometheus
python validate_integration.py

# 2. Validações passaram?
# ✅ [PASS] Structure
# ✅ [PASS] Files
# ✅ [PASS] Dependencies
# ✅ [PASS] Bridge
# ✅ [PASS] V2 Modules
# ✅ [PASS] Python

# 3. Iniciar sistema
launch.bat
# ou
python main_integrated.py
```

---

## 🎯 OBJETIVOS DE APRENDIZADO

### Semana 1: Familiarização
- [ ] Ler INTEGRATION_COMPLETE.md
- [ ] Ler QUICKSTART_V2.md
- [ ] Executar validate_integration.py
- [ ] Iniciar main_integrated.py
- [ ] Testar comandos básicos

### Semana 2: Exploração
- [ ] Ler INTEGRATION_REPORT.md
- [ ] Estudar integration_bridge.py
- [ ] Testar cada módulo V2
- [ ] Configurar API keys
- [ ] Usar consenso multi-IA

### Semana 3: Avançado
- [ ] Estudar prometheus_core.py
- [ ] Implementar caso de uso real
- [ ] Otimizar configurações
- [ ] Documentar workflows
- [ ] Contribuir melhorias

---

## ✅ CONCLUSÃO

Você tem acesso a:
- ✅ 5 documentos principais
- ✅ 8+ scripts utilitários
- ✅ Estrutura organizada
- ✅ Exemplos práticos
- ✅ Troubleshooting completo

**Comece por:** `INTEGRATION_COMPLETE.md`

---

**Versão:** 1.0
**Mantido por:** Claude Code
**Atualizado:** 2025-11-15
