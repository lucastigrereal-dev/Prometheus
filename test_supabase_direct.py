# -*- coding: utf-8 -*-
"""Teste direto do Supabase com ambas as keys"""

import os
import sys
import io
from dotenv import load_dotenv

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

load_dotenv()

from supabase import create_client

url = os.getenv("SUPABASE_URL")
anon_key = os.getenv("SUPABASE_ANON_KEY")
service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

print("="*70)
print("TESTE DIRETO SUPABASE")
print("="*70)
print()

# Teste 1: ANON KEY
print("1. Testando ANON_KEY...")
try:
    client_anon = create_client(url, anon_key)
    # Tenta listar tabelas
    response = client_anon.table('_test').select("*").limit(1).execute()
    print(f"   ✅ ANON_KEY funcionou!")
except Exception as e:
    print(f"   ❌ ANON_KEY erro: {str(e)[:150]}")

print()

# Teste 2: SERVICE_ROLE KEY
print("2. Testando SERVICE_ROLE_KEY...")
try:
    client_service = create_client(url, service_key)
    # Tenta listar tabelas
    response = client_service.table('_test').select("*").limit(1).execute()
    print(f"   ✅ SERVICE_ROLE_KEY funcionou!")
except Exception as e:
    error_str = str(e)
    if 'relation' in error_str.lower() or 'not exist' in error_str.lower():
        print(f"   ✅ SERVICE_ROLE_KEY OK (tabela não existe ainda - normal!)")
    else:
        print(f"   ❌ SERVICE_ROLE_KEY erro: {error_str[:150]}")

print()

# Teste 3: Verificar projeto
print("3. Verificando configuração do projeto...")
print(f"   URL: {url}")
print(f"   Projeto ID: {url.split('//')[1].split('.')[0]}")

print()
print("="*70)
print("CONCLUSÃO:")
print("Se SERVICE_ROLE_KEY deu OK, podemos prosseguir!")
print("="*70)
