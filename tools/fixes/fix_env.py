# -*- coding: utf-8 -*-
"""
Script para adicionar SUPABASE_ANON_KEY ao .env
"""

import os
import sys
import io
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def fix_env():
    env_path = Path("C:/Users/lucas/Prometheus/.env")

    # Ler conteúdo atual
    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Verificar se SUPABASE_ANON_KEY já existe
    has_anon_key = any('SUPABASE_ANON_KEY' in line for line in lines)

    if has_anon_key:
        print("✅ SUPABASE_ANON_KEY já existe no .env")
        return

    # Adicionar SUPABASE_ANON_KEY logo após SUPABASE_URL
    new_lines = []
    for line in lines:
        new_lines.append(line)
        if 'SUPABASE_URL=' in line:
            # Adiciona linha nova após SUPABASE_URL
            new_lines.append('SUPABASE_ANON_KEY=your_supabase_anon_key_here\n')

    # Salvar de volta
    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)

    print("✅ SUPABASE_ANON_KEY adicionada ao .env!")
    print("\nAgora edite o arquivo .env e preencha:")
    print("  - SUPABASE_URL")
    print("  - SUPABASE_ANON_KEY (NOVO!)")
    print("  - SUPABASE_SERVICE_ROLE_KEY")
    print("  - OPENAI_API_KEY")
    print("\nDepois execute: python check_credentials.py")

if __name__ == '__main__':
    fix_env()
