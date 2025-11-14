# ============================================================================
# Prometheus Setup Script - PowerShell Version
# ============================================================================
# Este script configura o ambiente Prometheus:
# - Verifica pré-requisitos (Docker, Python)
# - Cria ambiente virtual Python
# - Instala OpenInterpreter e dependências
# - Inicia n8n via Docker
# ============================================================================

param(
    [switch]$SkipDocker,
    [switch]$SkipPython,
    [switch]$Force
)

$ErrorActionPreference = "Stop"

# Cores para output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Error { Write-Host $args -ForegroundColor Red }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }

Write-Info "============================================================"
Write-Info "PROMETHEUS SETUP - Configuracao Automatica"
Write-Info "============================================================"
Write-Host ""

# ============================================================================
# 1. VERIFICAR PRÉ-REQUISITOS
# ============================================================================

Write-Info "[1/6] Verificando pre-requisitos..."

# Verificar Docker
if (-not $SkipDocker) {
    try {
        $dockerVersion = docker --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "  [OK] Docker: $dockerVersion"
        } else {
            throw "Docker nao encontrado"
        }
    } catch {
        Write-Error "  [ERRO] Docker nao esta instalado ou nao esta no PATH."
        Write-Error "  Por favor, instale o Docker Desktop: https://www.docker.com/products/docker-desktop"
        exit 1
    }

    # Verificar se Docker está rodando
    try {
        docker ps > $null 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Error "  [ERRO] Docker esta instalado mas nao esta rodando."
            Write-Error "  Por favor, inicie o Docker Desktop."
            exit 1
        }
    } catch {
        Write-Error "  [ERRO] Docker nao esta rodando. Inicie o Docker Desktop."
        exit 1
    }
}

# Verificar Python
if (-not $SkipPython) {
    try {
        $pythonVersion = python --version 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "  [OK] Python: $pythonVersion"
        } else {
            throw "Python nao encontrado"
        }
    } catch {
        Write-Error "  [ERRO] Python nao esta instalado ou nao esta no PATH."
        Write-Error "  Por favor, instale Python 3.8+: https://www.python.org/downloads/"
        exit 1
    }
}

Write-Host ""

# ============================================================================
# 2. CARREGAR VARIÁVEIS DE AMBIENTE
# ============================================================================

Write-Info "[2/6] Carregando variaveis de ambiente..."

if (Test-Path ".env") {
    Write-Info "  Carregando .env..."
    Get-Content .env | ForEach-Object {
        if ($_ -match '^([^#][^=]+)=(.*)$') {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            Set-Item -Path "env:$name" -Value $value
            Write-Host "    $name definido"
        }
    }
} else {
    Write-Warning "  Arquivo .env nao encontrado. Usando valores padrao."
    if (Test-Path ".env.example") {
        Write-Info "  Copiando .env.example para .env..."
        Copy-Item ".env.example" ".env"
    }
}

# Definir valores padrão
$N8N_USER = if ($env:N8N_BASIC_AUTH_USER) { $env:N8N_BASIC_AUTH_USER } else { "prometheus" }
$N8N_PASS = if ($env:N8N_BASIC_AUTH_PASSWORD) { $env:N8N_BASIC_AUTH_PASSWORD } else { "password123" }
$TZ = if ($env:TZ) { $env:TZ } else { "America/Sao_Paulo" }

Write-Host ""

# ============================================================================
# 3. CRIAR/ATIVAR AMBIENTE VIRTUAL PYTHON
# ============================================================================

Write-Info "[3/6] Configurando ambiente virtual Python..."

if (Test-Path ".venv") {
    Write-Success "  [OK] Ambiente virtual ja existe em .venv"
} else {
    Write-Info "  Criando ambiente virtual..."
    python -m venv .venv
    if ($LASTEXITCODE -eq 0) {
        Write-Success "  [OK] Ambiente virtual criado"
    } else {
        Write-Error "  [ERRO] Falha ao criar ambiente virtual"
        exit 1
    }
}

# Ativar ambiente virtual
$venvPython = Join-Path $PWD ".venv\Scripts\python.exe"
$venvPip = Join-Path $PWD ".venv\Scripts\pip.exe"

Write-Host ""

# ============================================================================
# 4. INSTALAR DEPENDÊNCIAS PYTHON
# ============================================================================

Write-Info "[4/6] Instalando dependencias Python..."

# Atualizar pip
Write-Info "  Atualizando pip..."
& $venvPip install --upgrade pip --quiet
if ($LASTEXITCODE -eq 0) {
    Write-Success "  [OK] pip atualizado"
}

# Instalar dependências do requirements.txt
if (Test-Path "requirements.txt") {
    Write-Info "  Instalando pacotes do requirements.txt..."
    & $venvPip install -r requirements.txt
    if ($LASTEXITCODE -eq 0) {
        Write-Success "  [OK] Dependencias instaladas"
    } else {
        Write-Warning "  [AVISO] Algumas dependencias falharam (normal se faltarem compiladores)"
    }
} else {
    Write-Info "  requirements.txt nao encontrado. Instalando open-interpreter..."
    & $venvPip install open-interpreter
    if ($LASTEXITCODE -eq 0) {
        Write-Success "  [OK] open-interpreter instalado"
    }
}

Write-Host ""

# ============================================================================
# 5. CONFIGURAR E INICIAR N8N (DOCKER)
# ============================================================================

if (-not $SkipDocker) {
    Write-Info "[5/6] Configurando n8n..."

    # Parar container existente se houver
    $existingContainer = docker ps -a -q -f name=n8n_instance 2>$null
    if ($existingContainer) {
        Write-Info "  Parando container n8n existente..."
        docker stop n8n_instance 2>&1 | Out-Null
        docker rm n8n_instance 2>&1 | Out-Null
    }

    # Iniciar n8n via docker-compose se existir
    if (Test-Path "docker-compose.yml") {
        Write-Info "  Iniciando n8n via docker-compose..."
        docker-compose up -d
        if ($LASTEXITCODE -eq 0) {
            Write-Success "  [OK] n8n iniciado via docker-compose"
        } else {
            Write-Error "  [ERRO] Falha ao iniciar n8n"
        }
    } else {
        # Iniciar n8n manualmente
        Write-Info "  Iniciando n8n container..."
        $n8nData = Join-Path $env:USERPROFILE ".n8n"
        New-Item -ItemType Directory -Force -Path $n8nData | Out-Null

        docker run -d `
            --name n8n_instance `
            -p 5678:5678 `
            -v "${n8nData}:/home/node/.n8n" `
            -e N8N_BASIC_AUTH_USER="$N8N_USER" `
            -e N8N_BASIC_AUTH_PASSWORD="$N8N_PASS" `
            -e TZ="$TZ" `
            n8nio/n8n:latest | Out-Null

        if ($LASTEXITCODE -eq 0) {
            Write-Success "  [OK] n8n container iniciado"
        } else {
            Write-Error "  [ERRO] Falha ao iniciar container n8n"
        }
    }
} else {
    Write-Warning "[5/6] Pulando configuracao do Docker (--SkipDocker)"
}

Write-Host ""

# ============================================================================
# 6. VERIFICAR INSTALAÇÃO
# ============================================================================

Write-Info "[6/6] Verificando instalacao..."

# Verificar OpenInterpreter
$interpreterPath = Join-Path $PWD ".venv\Scripts\interpreter.exe"
if (Test-Path $interpreterPath) {
    Write-Success "  [OK] OpenInterpreter instalado"
} else {
    Write-Warning "  [AVISO] OpenInterpreter nao encontrado em Scripts"
}

# Verificar n8n
if (-not $SkipDocker) {
    Start-Sleep -Seconds 2
    $n8nRunning = docker ps -q -f name=n8n_instance 2>$null
    if ($n8nRunning) {
        Write-Success "  [OK] n8n rodando"
    } else {
        Write-Warning "  [AVISO] n8n nao esta rodando"
    }
}

Write-Host ""

# ============================================================================
# RESUMO FINAL
# ============================================================================

Write-Success "============================================================"
Write-Success "INSTALACAO CONCLUIDA!"
Write-Success "============================================================"
Write-Host ""

Write-Info "Ambiente Python:"
Write-Host "  Localizacao: $(Join-Path $PWD '.venv')"
Write-Host "  Python: $venvPython"
Write-Host ""

if (-not $SkipDocker) {
    Write-Info "n8n:"
    Write-Host "  URL: http://localhost:5678"
    Write-Host "  Usuario: $N8N_USER"
    Write-Host "  Senha: $N8N_PASS"
    Write-Host ""
}

Write-Info "Proximos passos:"
Write-Host ""
Write-Host "1. Ativar ambiente virtual:"
Write-Host "   .\.venv\Scripts\Activate.ps1"
Write-Host ""
Write-Host "2. Iniciar OpenInterpreter:"
Write-Host "   interpreter"
Write-Host ""
Write-Host "3. Acessar n8n:"
Write-Host "   http://localhost:5678"
Write-Host ""

Write-Success "Pronto para usar! 🚀"
