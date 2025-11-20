# PROMETHEUS SUPREME - INTERFACES GRÁFICAS

Prometheus Supreme agora possui **3 interfaces** para interação com o sistema!

## 🖥️ Interface Desktop (Tkinter)

Interface gráfica local estilo JARVIS com design futurista dark/cyber.

### Como executar:

```bash
# Método 1: Script de lançamento (recomendado)
run_desktop.bat

# Método 2: Python direto
.venv\Scripts\python.exe prometheus_gui.py
```

### Recursos:
- ✅ Campo de comando com syntax highlighting
- ✅ Output em tempo real com cores (sucesso/erro/info)
- ✅ Painel de estatísticas (tasks, sucesso, aprendizados, tempo)
- ✅ Status de 6 componentes (Vision, Supervisor, Learning, etc.)
- ✅ 5 Ações rápidas:
  - Health Check do sistema
  - Ver Skills aprendidas
  - Ver Status completo
  - Buscar no Knowledge Base
  - Exemplos de comandos
- ✅ Relógio em tempo real
- ✅ Botões: Executar, Limpar, Parar
- ✅ Comunicação assíncrona com Prometheus

### Design:
- Background: `#0a0e27` (azul escuro espacial)
- Texto: `#00ff41` (verde Matrix)
- Accent: `#00bfff` (azul ciano)
- Erro: `#ff0040` (vermelho vibrante)

---

## 🌐 Interface Web (FastAPI + WebSockets)

Interface web moderna e responsiva acessível de qualquer dispositivo.

### Como executar:

```bash
# Método 1: Script de lançamento (recomendado)
run_web.bat

# Método 2: Python direto
.venv\Scripts\python.exe prometheus_web.py
```

### Acessar:
```
http://localhost:8100
```

### Recursos:
- ✅ Interface responsiva (funciona em mobile)
- ✅ WebSocket para comunicação em tempo real
- ✅ Reconexão automática se cair
- ✅ Mesmos recursos da interface Desktop
- ✅ Indicador de conexão visual
- ✅ Atalhos de teclado:
  - `Ctrl + Enter` - Executar comando
  - `Ctrl + L` - Limpar interface

### Tecnologias:
- **Backend**: FastAPI + Uvicorn + WebSockets
- **Frontend**: HTML5 + CSS3 + JavaScript vanilla
- **Design**: Gradient backgrounds, animações, responsive

---

## 💻 Interface Terminal (Menu Interativo)

Interface CLI com menu interativo para uso no terminal.

### Como executar:

```bash
.venv\Scripts\python.exe launch_supreme.py
```

### Menu:
```
+-----------------------------------------+
|         MENU PROMETHEUS SUPREME         |
+-----------------------------------------+
| 1. Executar Comando                     |
| 2. Buscar na Base de Conhecimento       |
| 3. Ver Status do Sistema                |
| 4. Ver Habilidades Aprendidas           |
| 5. Health Check Completo                |
| 6. Sair                                 |
+-----------------------------------------+
```

---

## 📊 Comparação de Interfaces

| Recurso | Desktop | Web | Terminal |
|---------|---------|-----|----------|
| Instalação | Tkinter (built-in) | FastAPI + Uvicorn | Nenhuma |
| Acesso remoto | ❌ | ✅ | ❌ |
| Interface gráfica | ✅ | ✅ | ❌ |
| Mobile-friendly | ❌ | ✅ | ❌ |
| Recursos visuais | ⭐⭐⭐ | ⭐⭐⭐ | ⭐ |
| Performance | Rápida | Rápida | Muito rápida |
| Uso de memória | Baixo | Baixo | Muito baixo |

---

## 🚀 Exemplos de Comandos

Teste estes comandos em qualquer interface:

```
1. Crie um script Python para análise de dados
2. Busque informações sobre machine learning
3. Analise o código e sugira melhorias
4. Crie uma API REST com FastAPI
5. Automatize o processo de backup
```

---

## 🔧 Configuração

### Requisitos:
- Python 3.11+
- Tkinter (geralmente incluído no Python)
- FastAPI, Uvicorn, WebSockets (instalados automaticamente)

### Instalação das dependências:
```bash
pip install fastapi uvicorn websockets
```

---

## 📝 Arquivos

```
prometheus_gui.py       # Interface Desktop (Tkinter)
prometheus_web.py       # Interface Web (FastAPI)
launch_supreme.py       # Interface Terminal (CLI)
run_desktop.bat         # Launcher Desktop
run_web.bat             # Launcher Web
```

---

## 🎨 Screenshots

### Desktop Interface
- Janela 1200x700
- 2 painéis (esquerda: comando/output, direita: stats/componentes/ações)
- Design futurista com gradientes e sombras

### Web Interface
- Responsiva (adapta ao tamanho da tela)
- Mesmo layout da Desktop
- Animações suaves e hover effects
- Status de conexão em tempo real

---

## 🐛 Troubleshooting

### Desktop não inicia:
```bash
# Verificar se Tkinter está instalado
python -c "import tkinter; print('Tkinter OK')"
```

### Web não conecta:
- Verifique se a porta 8100 está livre
- Firewall pode estar bloqueando
- Acesse: `http://localhost:8100` (não `127.0.0.1`)

### Terminal tem problemas de encoding:
- Use `chcp 65001` no Windows para UTF-8
- Ou execute via PowerShell

---

## 📚 Documentação Completa

Para mais informações, consulte o README.md principal do projeto.

---

**Desenvolvido com [Claude Code](https://claude.com/claude-code)**
