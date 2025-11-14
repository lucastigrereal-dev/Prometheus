# Prometheus MODO ABSOLUTO - Guia de Uso

## O que foi criado

O sistema Jarvis completo está pronto com os seguintes componentes:

### 📁 Arquivos Principais

1. **prometheus_brain.py** - Cérebro central do sistema
   - Classe `PrometheusCore` que coordena todas as skills
   - Interpretação de comandos em linguagem natural
   - Roteamento inteligente para skills apropriadas

2. **prometheus.yaml** - Arquivo de configuração
   - Configurações de voz, logging, skills
   - Parâmetros de segurança e runtime

3. **voice_listener.py** - Sistema de reconhecimento de voz
   - Escuta comando de ativação "Prometheus"
   - Reconhecimento em português (pt-BR)
   - Fila de comandos para processamento

4. **start_prometheus.py** - Inicializador do sistema
   - Verifica dependências
   - Inicia serviços (n8n, Docker)
   - Oferece modo interativo (texto) ou modo voz

### 📂 Diretórios

```
C:\Users\lucas\Prometheus\
├── prometheus_brain.py           # Cérebro principal
├── prometheus.yaml                # Configuração
├── voice_listener.py              # Reconhecimento de voz
├── start_prometheus.py            # Inicializador
├── .env                           # Variáveis de ambiente (APIs)
├── skills/                        # Módulos de habilidades
│   ├── __init__.py
│   ├── logs.py                   # Sistema de logging
│   ├── system_control.py         # Controle do sistema
│   ├── n8n_client.py             # Integração n8n
│   ├── whatsapp_api.py           # WhatsApp Cloud API
│   ├── rdstation_client.py       # RD Station CRM
│   ├── supabase_sync.py          # Supabase database
│   ├── google_services.py        # Google APIs (TODO)
│   └── ai_router.py              # Roteamento de AI (TODO)
├── runtime/                       # Runtime do sistema
│   └── commands_queue.txt        # Fila de comandos
└── logs/                          # Logs do sistema
    └── prometheus.log
```

## Como Usar

### 1. Configurar Credenciais (Opcional)

Edite o arquivo `.env` e adicione suas credenciais das APIs que deseja usar:

```bash
# WhatsApp Cloud API
WHATSAPP_PHONE_NUMBER_ID=seu_id_aqui
WHATSAPP_ACCESS_TOKEN=seu_token_aqui

# RD Station
RDSTATION_API_TOKEN=seu_token_aqui

# Supabase
SUPABASE_URL=sua_url_aqui
SUPABASE_SERVICE_ROLE_KEY=sua_chave_aqui

# AI APIs (Claude, OpenAI, etc)
ANTHROPIC_API_KEY=sua_chave_aqui
OPENAI_API_KEY=sua_chave_aqui
```

**Nota:** O sistema funciona mesmo sem credenciais configuradas. As skills sem credenciais simplesmente retornarão mensagens de erro informativas.

### 2. Iniciar o Sistema

```bash
# Ativar o ambiente virtual
cd C:\Users\lucas\Prometheus
.venv\Scripts\activate

# Iniciar o Prometheus
python start_prometheus.py
```

### 3. Escolher Modo de Operação

O sistema oferecerá 3 opções:

**Opção 1: Modo Interativo (Texto)**
- Digite comandos diretamente no terminal
- Mais confiável para começar
- Recomendado para primeiros testes

**Opção 2: Modo Voz**
- Reconhecimento de voz em português
- Diga "Prometheus" seguido do comando
- Requer instalação de: `pip install SpeechRecognition pyaudio`

**Opção 3: Sair**

## Comandos Disponíveis

### Sistema e Arquivos

```
listar arquivos C:\Users
abrir pasta C:\Temp
organizar downloads
executar "notepad.exe"
```

### n8n (Automação)

```
status n8n
listar workflows
n8n executar workflow
```

### WhatsApp

```
whatsapp 5511999999999 "Olá, esta é uma mensagem de teste"
```

### RD Station (CRM)

```
criar lead usuario@exemplo.com
buscar lead usuario@exemplo.com
```

### Supabase (Database)

```
inserir supabase
consultar supabase
```

### Google Services

```
criar evento calendario "Reunião importante"
enviar email para usuario@exemplo.com
```

### AI (Inteligência Artificial)

```
perguntar Como fazer X em Python?
ai analise estes dados
```

### Comandos Gerais

```
status          # Testa todas as conexões
ajuda           # Exibe ajuda
sair            # Encerra o sistema
```

## Exemplos de Uso

### Exemplo 1: Organizar Downloads

```
Prometheus> organizar downloads

RESULTADO:
  message: Downloads organizados com sucesso
  files_moved: 15
  categories: ['Documentos', 'Imagens', 'Videos']
```

### Exemplo 2: Listar Arquivos

```
Prometheus> listar arquivos C:\Users\lucas\Documents

RESULTADO:
  files: ['arquivo1.txt', 'arquivo2.pdf', ...]
  count: 10
```

### Exemplo 3: Status do Sistema

```
Prometheus> status

RESULTADO:
  tests:
    n8n: {success: true, status: "healthy"}
    rdstation: {success: false, error: "API token não configurado"}
    supabase: {success: false, error: "Credentials não configuradas"}
```

## Modo Voz

Para usar o reconhecimento de voz:

### 1. Instalar Dependências

```bash
pip install SpeechRecognition pyaudio
```

**Nota:** No Windows, `pyaudio` pode ser complicado de instalar. Se der erro, baixe o wheel:
```bash
# Baixe de: https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
pip install PyAudio-0.2.11-cp312-cp312-win_amd64.whl
```

### 2. Usar Modo Voz

1. Inicie o sistema: `python start_prometheus.py`
2. Escolha opção 2 (Modo Voz)
3. Diga "Prometheus" para ativar
4. Em seguida, diga o comando
5. Exemplo: "Prometheus" ... "listar arquivos"

## Arquitetura do Sistema

### PrometheusCore (prometheus_brain.py)

```python
brain = PrometheusCore()
brain.start()  # Inicia e carrega todas as skills

# Processar comando
result = brain.handle_text_command("listar arquivos")

# Rotear para skill específica
result = brain.route_to_skill("system_control", {
    "action": "list_files",
    "path": "."
})
```

### Skills

Cada skill é um módulo Python em `skills/` com funções específicas:

```python
# skills/system_control.py
def list_files(path: str) -> Dict:
    """Lista arquivos em um diretório"""
    ...
    return {"success": True, "files": [...]}
```

### Adicionar Nova Skill

1. Criar arquivo em `skills/nome_da_skill.py`
2. Importar logging: `from .logs import setup_logger`
3. Criar funções que retornam `Dict` com `{"success": bool, ...}`
4. Adicionar à lista em `prometheus_brain.py` na função `load_skills()`
5. Adicionar lógica de roteamento em `handle_text_command()`

## Logs

Todos os logs são salvos em:
- `./logs/prometheus.log` - Log principal do sistema
- `./logs/prometheus_startup.log` - Log de inicialização

Para verificar logs:
```bash
type logs\prometheus.log
```

## Solução de Problemas

### Erro: "Dependências faltando"
```bash
pip install pyyaml python-dotenv requests
```

### Erro: "Docker não está ativo"
- Abra o Docker Desktop
- Aguarde inicializar
- Execute novamente

### Erro: "Biblioteca supabase não instalada"
```bash
pip install supabase
```

### Erro: "Speech recognition não disponível"
```bash
pip install SpeechRecognition pyaudio
```

### n8n não inicia
- Verifique se Docker está rodando: `docker ps`
- Verifique logs: `docker logs n8n_instance`
- Tente manualmente: `docker-compose up -d`

## Próximos Passos

### Implementar Skills TODO

1. **google_services.py** - Integração completa com Google
   - Configurar OAuth2
   - Implementar Calendar, Gmail, Drive

2. **ai_router.py** - Chamadas reais às APIs de IA
   - Implementar Anthropic Claude API
   - Implementar OpenAI API
   - Implementar Perplexity API

### Expandir Funcionalidades

1. Adicionar mais comandos ao sistema
2. Criar interface web com Flask/FastAPI
3. Adicionar reconhecimento de entidades (NER)
4. Implementar cache de respostas
5. Adicionar métricas e analytics

## Referências

- **n8n**: http://localhost:5678
- **Logs**: `./logs/prometheus.log`
- **Config**: `prometheus.yaml`
- **Credenciais**: `.env`

## Notas de Segurança

⚠️ **IMPORTANTE:**

1. **Nunca commite o arquivo `.env`** com credenciais reais
2. O sistema tem proteção contra comandos perigosos (ver `prometheus.yaml`)
3. Comandos destrutivos requerem confirmação
4. Sempre revise logs em `./logs/` para auditoria

---

**Prometheus MODO ABSOLUTO está pronto! 🚀**

Para iniciar: `python start_prometheus.py`
