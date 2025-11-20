# -*- coding: utf-8 -*-
"""
VERIFICADOR DE CREDENCIAIS V2 - Atualizado para APIs modernas
"""

import os
import sys
import io
from dotenv import load_dotenv

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_supabase():
    """Testa conexão com Supabase"""
    try:
        from supabase import create_client, Client

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")

        if not url or not key:
            return False, "Credenciais faltando"

        # Tenta criar cliente
        client: Client = create_client(url, key)

        # Testa conexão básica (lista tabelas)
        # Se não houver tabelas, vai retornar lista vazia (OK!)
        try:
            result = client.table('_test_').select("count", count='exact').execute()
        except Exception as e:
            # Erro esperado se tabela não existe - mas conexão funcionou!
            error_msg = str(e).lower()
            if 'relation' in error_msg or 'not found' in error_msg or 'does not exist' in error_msg:
                return True, "Conexão OK (tabelas ainda não criadas)"
            else:
                return False, str(e)[:100]

        return True, "Conexão OK"

    except ImportError:
        return False, "Biblioteca 'supabase' não instalada"
    except Exception as e:
        return False, str(e)[:100]

def test_openai():
    """Testa conexão com OpenAI (v1.0+ API)"""
    try:
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            return False, "API key faltando"

        if not api_key.startswith('sk-'):
            return False, "API key inválida (deve começar com sk-)"

        # Tenta criar cliente
        client = OpenAI(api_key=api_key)

        # Testa com uma chamada mínima (lista modelos)
        try:
            models = client.models.list()
            return True, f"Conexão OK ({len(list(models.data))} modelos disponíveis)"
        except Exception as e:
            error_msg = str(e).lower()
            if 'api key' in error_msg or 'authentication' in error_msg:
                return False, "API key inválida"
            else:
                return False, str(e)[:100]

    except ImportError:
        return False, "Biblioteca 'openai' não instalada"
    except Exception as e:
        return False, str(e)[:100]

def main():
    print("="*70)
    print("🔍 PROMETHEUS KNOWLEDGE BRAIN - CREDENTIAL CHECKER V2")
    print("="*70)
    print()

    # Carregar .env
    env_file = os.path.join(os.path.dirname(__file__), '.env')
    load_dotenv(env_file)
    print(f"✅ Arquivo .env carregado: {env_file}\n")

    all_ok = True

    # Test Supabase
    print("1. SUPABASE")
    print("-" * 70)
    success, message = test_supabase()

    if success:
        print(f"✅ Supabase: {message}")
        print(f"   URL: {os.getenv('SUPABASE_URL')}")
    else:
        print(f"❌ Supabase: {message}")
        all_ok = False

    print()

    # Test OpenAI
    print("2. OPENAI")
    print("-" * 70)
    success, message = test_openai()

    if success:
        print(f"✅ OpenAI: {message}")
        api_key = os.getenv('OPENAI_API_KEY')
        print(f"   Key: {api_key[:15]}...{api_key[-10:]}")
    else:
        print(f"❌ OpenAI: {message}")
        all_ok = False

    print()
    print("="*70)

    if all_ok:
        print("🎉 TUDO PRONTO! Podemos começar a implementação.")
        print()
        print("PRÓXIMOS PASSOS:")
        print("  1. Criar schema SQL no Supabase")
        print("  2. Implementar componentes Python")
        print("  3. Testar ingestão de documentos")
        print("="*70)
        return 0
    else:
        print("⚠️  Corrija os erros acima antes de continuar")
        print("="*70)
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nVerificação cancelada.")
        sys.exit(1)
