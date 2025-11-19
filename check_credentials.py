# -*- coding: utf-8 -*-
"""
VERIFICADOR DE CREDENCIAIS - Prometheus Knowledge Brain

Testa se você tem tudo configurado para começar:
- SUPABASE_URL
- SUPABASE_ANON_KEY
- OPENAI_API_KEY

Uso:
    python check_credentials.py
"""

import os
import sys
import io

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from dotenv import load_dotenv

# Cores para terminal
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header():
    print("=" * 70)
    print(f"{BLUE}🔍 PROMETHEUS KNOWLEDGE BRAIN - CREDENTIAL CHECKER{RESET}")
    print("=" * 70)
    print()

def check_env_var(name: str, required: bool = True) -> tuple[bool, str]:
    """Verifica se variável de ambiente existe"""
    value = os.getenv(name)

    if value:
        # Mostra apenas primeiros/últimos caracteres (segurança)
        masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
        return True, masked
    else:
        return False, None

def test_supabase_connection(url: str, key: str) -> bool:
    """Testa conexão com Supabase"""
    try:
        from supabase import create_client
        client = create_client(url, key)
        # Tenta uma query simples
        result = client.table('documents').select("count", count='exact').execute()
        return True
    except ImportError:
        print(f"{YELLOW}   ⚠️  Biblioteca 'supabase' não instalada{RESET}")
        print(f"{YELLOW}      Execute: pip install supabase{RESET}")
        return False
    except Exception as e:
        print(f"{YELLOW}   ⚠️  Erro ao conectar: {str(e)[:50]}...{RESET}")
        return False

def test_openai_connection(api_key: str) -> bool:
    """Testa conexão com OpenAI"""
    try:
        import openai
        openai.api_key = api_key
        # Testa com uma requisição mínima
        models = openai.Model.list()
        return True
    except ImportError:
        print(f"{YELLOW}   ⚠️  Biblioteca 'openai' não instalada{RESET}")
        print(f"{YELLOW}      Execute: pip install openai{RESET}")
        return False
    except Exception as e:
        print(f"{YELLOW}   ⚠️  Erro ao conectar: {str(e)[:50]}...{RESET}")
        return False

def show_where_to_find(service: str):
    """Mostra onde encontrar as credenciais"""
    guides = {
        'supabase': f"""
{BLUE}📍 ONDE ENCONTRAR CREDENCIAIS DO SUPABASE:{RESET}

1. Acesse: https://app.supabase.com
2. Faça login na sua conta
3. Selecione seu projeto (ou crie um novo - é grátis!)
4. No menu lateral, clique em ⚙️ Settings
5. Clique em "API"
6. Você verá:

   📋 Project URL → Essa é sua SUPABASE_URL
   Exemplo: https://abcdefghijk.supabase.co

   🔑 anon/public key → Essa é sua SUPABASE_ANON_KEY
   Exemplo: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

7. Copie e cole no arquivo .env do Prometheus:

{YELLOW}SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...{RESET}
""",
        'openai': f"""
{BLUE}📍 ONDE ENCONTRAR API KEY DA OPENAI:{RESET}

1. Acesse: https://platform.openai.com/api-keys
2. Faça login (ou crie conta se não tiver)
3. Clique em "+ Create new secret key"
4. Dê um nome (ex: "Prometheus Knowledge")
5. Copie a key (começa com sk-...)

   ⚠️  IMPORTANTE: Você só vê a key UMA VEZ!
   Guarde em lugar seguro.

6. Cole no arquivo .env do Prometheus:

{YELLOW}OPENAI_API_KEY=sk-proj-abcdefghijk...{RESET}

💰 CUSTO: ~$0.06/mês para embeddings (praticamente grátis)
"""
    }

    print(guides.get(service, ""))

def main():
    print_header()

    # Carregar .env
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_file):
        load_dotenv(env_file)
        print(f"{GREEN}✅ Arquivo .env encontrado: {env_file}{RESET}\n")
    else:
        print(f"{YELLOW}⚠️  Arquivo .env NÃO encontrado{RESET}")
        print(f"{YELLOW}   Criando em: {env_file}{RESET}\n")
        with open(env_file, 'w') as f:
            f.write("# Prometheus Knowledge Brain - Credenciais\n\n")
            f.write("# Supabase\n")
            f.write("SUPABASE_URL=\n")
            f.write("SUPABASE_ANON_KEY=\n\n")
            f.write("# OpenAI\n")
            f.write("OPENAI_API_KEY=\n")

    all_ok = True

    # Verificar Supabase
    print(f"{BLUE}1. SUPABASE{RESET}")
    print("-" * 70)

    has_url, url_value = check_env_var('SUPABASE_URL')
    has_key, key_value = check_env_var('SUPABASE_ANON_KEY')

    if has_url:
        print(f"{GREEN}✅ SUPABASE_URL encontrada: {url_value}{RESET}")
    else:
        print(f"{RED}❌ SUPABASE_URL NÃO encontrada{RESET}")
        all_ok = False

    if has_key:
        print(f"{GREEN}✅ SUPABASE_ANON_KEY encontrada: {key_value}{RESET}")
    else:
        print(f"{RED}❌ SUPABASE_ANON_KEY NÃO encontrada{RESET}")
        all_ok = False

    if has_url and has_key:
        print(f"\n{BLUE}   Testando conexão...{RESET}")
        if test_supabase_connection(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_ANON_KEY')):
            print(f"{GREEN}   ✅ Conexão com Supabase OK!{RESET}")
        else:
            print(f"{RED}   ❌ Falha na conexão com Supabase{RESET}")
            all_ok = False
    else:
        show_where_to_find('supabase')

    print()

    # Verificar OpenAI
    print(f"{BLUE}2. OPENAI{RESET}")
    print("-" * 70)

    has_openai, openai_value = check_env_var('OPENAI_API_KEY')

    if has_openai:
        print(f"{GREEN}✅ OPENAI_API_KEY encontrada: {openai_value}{RESET}")
        print(f"\n{BLUE}   Testando conexão...{RESET}")
        if test_openai_connection(os.getenv('OPENAI_API_KEY')):
            print(f"{GREEN}   ✅ Conexão com OpenAI OK!{RESET}")
        else:
            print(f"{RED}   ❌ Falha na conexão com OpenAI{RESET}")
            all_ok = False
    else:
        print(f"{RED}❌ OPENAI_API_KEY NÃO encontrada{RESET}")
        show_where_to_find('openai')
        all_ok = False

    print()
    print("=" * 70)

    # Resultado final
    if all_ok:
        print(f"{GREEN}🎉 TUDO PRONTO! Você pode começar a implementação.{RESET}")
        print(f"\n{BLUE}Próximo passo:{RESET}")
        print(f"   python knowledge_ingest.py --dry-run")
        return 0
    else:
        print(f"{YELLOW}⚠️  CONFIGURAÇÃO INCOMPLETA{RESET}")
        print(f"\n{BLUE}O que fazer:{RESET}")
        print(f"   1. Preencha as credenciais faltantes no arquivo .env")
        print(f"   2. Execute novamente: python check_credentials.py")
        print(f"   3. Quando tudo estiver OK, comece a implementação!")
        return 1

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Verificação cancelada.{RESET}")
        sys.exit(1)
