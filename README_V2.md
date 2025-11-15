# PROMETHEUS MODO ABSOLUTO v2.1 + V2 INTEGRATED

Sistema de automacao inteligente inspirado em Jarvis, com IA multi-modelo, controle de visao, navegador web, memoria semantica e interface grafica moderna.

---

## NOVIDADE: V2 INTEGRATED (2025-11-15)

**Sistema agora roda V1 (estavel) + V2 (next-gen) simultaneamente!**

- 11 modulos totais (5 V1 + 6 V2)
- Consenso Multi-IA (Claude + GPT-4)
- Memoria Vetorial FAISS (busca semantica ultra-rapida)
- Providers de IA avancados (Claude Sonnet 4, GPT-4)
- Integration Bridge (migracao gradual V1->V2)

### Inicio Rapido V2
```bash
# Launcher interativo
launch.bat

# Ou direto
.venv\Scripts\python.exe main_integrated.py

# Validar sistema
.venv\Scripts\python.exe validate_integration.py
```

### Documentacao V2
- **QUICKSTART_V2.md** - Guia rapido (leia primeiro!)
- **INTEGRATION_REPORT.md** - Relatorio tecnico completo
- **prometheus_v2/** - Novos modulos (Opus)

---

## Recursos Principais

### Modulos V1 (Estaveis)
1. **System Control** - Controle de sistema operacional e arquivos
2. **N8N Client** - Integracao com automacoes n8n
3. **WhatsApp API** - Envio e recebimento de mensagens WhatsApp
4. **RD Station Client** - Integracao com CRM e marketing
5. **Supabase Sync** - Sincronizacao de banco de dados
6. **Google Services** - Integracao com Gmail, Calendar, Drive
7. **Vision Control** - Controle visual da tela (OCR, cliques, automacao)
8. **Always-On Voice** - Sistema de voz sempre ativo com wake words
9. **Memory System** - Memoria persistente com busca semantica
10. **Browser Control** - Automacao de navegador web com Playwright
11. **AI Master Router** - Roteamento inteligente entre Claude, GPT-4 e Gemini

### Modulos V2 (Next-Gen - Opus)
1. **Prometheus Core V2** - Orquestrador central avancado
2. **Task Analyzer** - Parser NLP avancado (requer spacy)
3. **Consensus Engine** - Motor de consenso multi-IA
4. **Claude Provider** - Provider Claude Sonnet 4
5. **GPT Provider** - Provider GPT-4 + Aurora
6. **Browser Controller V2** - Browser automation melhorado
7. **Memory Manager V2** - Memoria vetorial com FAISS

---

## Instalacao

### Requisitos
- Python 3.10+
- Docker (para n8n)
- Windows 10/11

### Setup Rapido
```bash
# 1. Clone o repositorio
git clone <repo>
cd Prometheus

# 2. Instale dependencias
pip install -r requirements.txt

# 3. Configure .env (opcional)
cp .env.example .env
# Edite .env com suas API keys

# 4. Inicie V2
launch.bat
```

---

## Como Usar

### Opcao 1: Launcher Interativo
```bash
launch.bat
```

### Opcao 2: Sistema Integrado (V1+V2)
```bash
.venv\Scripts\python.exe main_integrated.py
```

Comandos disponiveis:
- `status` - Ver status do sistema
- `modules` - Listar todos os modulos V1/V2
- `test <module>` - Testar modulo especifico
- `help` - Ajuda
- `exit` - Sair

### Opcao 3: Sistema V1 Original
```bash
python start_prometheus.py
```

---

## Arquitetura

```
Prometheus/
├── prometheus_v2/              # Modulos V2 (Next-Gen)
│   ├── core/                   # Nucleo orquestrador
│   ├── ai_providers/           # Providers de IA
│   ├── execution/              # Execucao/automacao
│   ├── memory/                 # Sistema de memoria
│   └── config/                 # Configuracoes
├── skills/                     # Skills V1 (Estaveis)
├── integration_bridge.py       # Bridge V1<->V2
├── main_integrated.py          # Entry point integrado
├── validate_integration.py     # Validacao automatica
└── launch.bat                  # Launcher conveniente
```

---

## Configuracao

### API Keys (Opcional)
Edite `.env`:
```bash
# Claude
ANTHROPIC_API_KEY=sk-ant-...

# OpenAI
OPENAI_API_KEY=sk-...

# Supabase
SUPABASE_URL=https://...
SUPABASE_KEY=...
```

### Dependencias Opcionais

#### Para Task Analyzer (NLP)
```bash
pip install spacy
python -m spacy download pt_core_news_sm
```

#### Para memoria vetorial (ja instalado)
```bash
pip install faiss-cpu sentence-transformers
```

---

## Status Atual

### Testes de Validacao
```bash
.venv\Scripts\python.exe validate_integration.py
```

Resultado esperado:
```
[PASS] Structure
[PASS] Files
[PASS] Dependencies
[PASS] Bridge
[PASS] V2 Modules
[PASS] Python
```

### Modulos Carregados
- V1: 5 modulos (browser, memory, vision, voice, ai_master)
- V2: 6 modulos (core, browser, memory, consensus, claude, gpt)
- Total: 11 modulos funcionais

---

## Troubleshooting

### Sistema nao inicia
```bash
# Valide instalacao
.venv\Scripts\python.exe validate_integration.py

# Teste bridge
.venv\Scripts\python.exe integration_bridge.py
```

### Modulo nao carrega
Veja logs em `logs/prometheus.log`

### Dependencia faltando
```bash
pip install -r requirements.txt
```

---

## Documentacao Completa

- **QUICKSTART_V2.md** - Guia rapido V2
- **INTEGRATION_REPORT.md** - Relatorio tecnico completo
- **MODO_ABSOLUTO_GUIA.md** - Guia V1 original
- **prometheus_v2/config/prometheus_config.yaml** - Config V2

---

## Roadmap

### Fase Atual: V1+V2 Integrated
- [x] Estrutura V2 criada
- [x] Modulos V2 integrados
- [x] Bridge funcionando
- [x] Sistema validado

### Proximo: Testes e Otimizacao
- [ ] Testar cada provider de IA
- [ ] Benchmark consenso engine
- [ ] Otimizar memoria vetorial
- [ ] Documentar APIs V2

### Futuro: Migracao Completa
- [ ] Deprecar modulos V1 duplicados
- [ ] Consolidar configuracoes
- [ ] Deploy production
- [ ] CI/CD pipeline

---

## Contribuindo

Este e um projeto pessoal, mas sugestoes sao bem-vindas!

---

## Licenca

MIT

---

**Versao:** V1+V2 Integrated
**Data:** 2025-11-15
**Status:** PRODUCTION READY
