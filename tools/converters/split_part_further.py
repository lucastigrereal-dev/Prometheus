# -*- coding: utf-8 -*-
"""
Divide uma parte do Claude em sub-partes ainda menores
Para processar mais rápido (200 conversas = ~2000 chunks = 3-5 min)
"""

import os
import sys
import io
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def split_part(input_path, output_dir, convs_per_subpart=200):
    """Divide uma parte em sub-partes menores"""

    print(f"📄 Lendo: {input_path.name}")

    with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    size_mb = len(content) / 1024 / 1024
    print(f"   Tamanho: {size_mb:.1f} MB")

    # Dividir por conversas
    conversations = content.split('\n' + '='*70 + '\n')
    total_convs = len(conversations)

    print(f"   Conversas: {total_convs}")

    # Calcular quantas sub-partes
    num_subparts = (total_convs + convs_per_subpart - 1) // convs_per_subpart

    print(f"\n📦 Dividindo em {num_subparts} sub-partes ({convs_per_subpart} conversas cada)...")

    # Criar diretório
    output_dir.mkdir(parents=True, exist_ok=True)

    # Extrair número da parte (ex: "part_1_of_4" -> "1")
    part_num = input_path.stem.split('_')[2]

    for i in range(num_subparts):
        start_idx = i * convs_per_subpart
        end_idx = min((i + 1) * convs_per_subpart, total_convs)

        subpart_conversations = conversations[start_idx:end_idx]
        subpart_content = ('\n' + '='*70 + '\n').join(subpart_conversations)

        # Nome: claude_p1_s1.txt, claude_p1_s2.txt, etc
        subpart_filename = f"claude_p{part_num}_s{i+1}.txt"
        subpart_path = output_dir / subpart_filename

        with open(subpart_path, 'w', encoding='utf-8') as f:
            f.write(subpart_content)

        size_mb = len(subpart_content) / 1024 / 1024
        print(f"   ✅ Sub-parte {i+1}: {subpart_filename} ({len(subpart_conversations)} convs, {size_mb:.1f} MB)")

    print(f"\n" + "="*70)
    print("✅ DIVISÃO COMPLETA!")
    print("="*70)
    print(f"\nArquivos em: {output_dir}")
    print("\nPróximo passo:")
    print(f"1. Copie {output_dir.name}/claude_p{part_num}_s1.txt para inbox_raw/claude/")
    print("2. Rode: python knowledge_ingest.py")
    print("3. Aguarde ~3-5 min")
    print("="*70)


if __name__ == '__main__':
    # Pega a Parte 1
    input_file = Path("C:/Users/lucas/Desktop/EXPORTS_IA_TEMP/claude_parts/claude_part_1_of_4.txt")
    output_dir = Path("C:/Users/lucas/Desktop/EXPORTS_IA_TEMP/claude_subparts")

    if not input_file.exists():
        print(f"❌ Arquivo não encontrado: {input_file}")
        sys.exit(1)

    # Dividir em sub-partes de 200 conversas
    split_part(input_file, output_dir, convs_per_subpart=200)
