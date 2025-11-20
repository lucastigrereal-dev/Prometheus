# -*- coding: utf-8 -*-
"""
Divide arquivo grande do Claude em partes menores
Garante que não quebra no meio de conversas (sempre em ====)
"""

import os
import sys
import io
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def split_file(input_path, output_dir, num_parts=4):
    """Divide arquivo em N partes respeitando separadores de conversa"""

    print(f"📄 Lendo arquivo: {input_path.name}")

    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    print(f"   Tamanho: {len(content) / 1024 / 1024:.1f} MB")

    # Dividir por conversas (separador é ====)
    conversations = content.split('\n' + '='*70 + '\n')
    total_convs = len(conversations)

    print(f"   Total conversas: {total_convs}")

    # Calcular quantas conversas por parte
    convs_per_part = total_convs // num_parts

    print(f"\n📦 Dividindo em {num_parts} partes ({convs_per_part} conversas cada)...")

    # Criar diretório de saída
    output_dir.mkdir(parents=True, exist_ok=True)

    parts_info = []

    for i in range(num_parts):
        # Índices de início e fim
        start_idx = i * convs_per_part

        # Última parte pega tudo que sobrou
        if i == num_parts - 1:
            end_idx = total_convs
        else:
            end_idx = (i + 1) * convs_per_part

        # Juntar conversas desta parte
        part_conversations = conversations[start_idx:end_idx]
        part_content = ('\n' + '='*70 + '\n').join(part_conversations)

        # Nome do arquivo
        part_filename = f"claude_part_{i+1}_of_{num_parts}.txt"
        part_path = output_dir / part_filename

        # Salvar
        with open(part_path, 'w', encoding='utf-8') as f:
            f.write(part_content)

        size_mb = len(part_content) / 1024 / 1024
        parts_info.append({
            'file': part_filename,
            'conversations': len(part_conversations),
            'size_mb': size_mb
        })

        print(f"   ✅ Parte {i+1}: {part_filename} ({len(part_conversations)} convs, {size_mb:.1f} MB)")

    print(f"\n" + "="*70)
    print("✅ DIVISÃO COMPLETA!")
    print("="*70)
    print(f"\nArquivos salvos em: {output_dir}")
    print("\nPróximos passos:")
    print("1. Mova cada parte para: knowledge/inbox_raw/claude/")
    print("2. Rode: python knowledge_ingest.py")
    print("3. Aguarde ~10-15 min por parte")
    print("4. Repita para próxima parte")
    print("="*70)

    return parts_info


if __name__ == '__main__':
    # Caminhos
    input_file = Path("C:/Users/lucas/Desktop/EXPORTS_IA_TEMP/claude_all_conversations.txt")
    output_dir = Path("C:/Users/lucas/Desktop/EXPORTS_IA_TEMP/claude_parts")

    if not input_file.exists():
        print(f"❌ Arquivo não encontrado: {input_file}")
        sys.exit(1)

    # Dividir em 4 partes
    split_file(input_file, output_dir, num_parts=4)
