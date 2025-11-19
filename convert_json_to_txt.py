# -*- coding: utf-8 -*-
"""
Conversor Rápido: JSON → TXT
Extrai conversas do Claude e GPT para formato texto limpo
"""

import json
import sys
import io
from pathlib import Path

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def convert_gpt_json(json_path, output_dir):
    """Converte conversations.json do GPT para TXT"""
    print(f"\n📄 Convertendo GPT: {json_path.name}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"   Total conversas: {len(data)}")

    # Criar um TXT por conversa (ou um único grande)
    all_text = []

    for i, conv in enumerate(data):
        title = conv.get('name', f'Conversa {i+1}')
        summary = conv.get('summary', '')

        # Extrair mensagens
        messages = conv.get('messages', [])

        text = f"# {title}\n\n"
        if summary:
            text += f"**Resumo:** {summary}\n\n"

        for msg in messages:
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            text += f"**{role.upper()}:** {content}\n\n"

        text += "\n" + "="*70 + "\n\n"
        all_text.append(text)

    # Salvar tudo em um arquivo
    output_file = output_dir / "gpt_all_conversations.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(all_text))

    print(f"   ✅ Salvo: {output_file.name} ({len(all_text)} conversas)")
    return len(all_text)

def convert_claude_json(json_path, output_dir):
    """Converte conversations.json do Claude para TXT"""
    print(f"\n📄 Convertendo Claude: {json_path.name}")

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    print(f"   Total conversas: {len(data)}")

    all_text = []

    for i, conv in enumerate(data):
        title = conv.get('title', f'Conversa {i+1}')

        text = f"# {title}\n\n"

        # Extrair mensagens do mapping
        mapping = conv.get('mapping', {})

        for node_id, node in mapping.items():
            message = node.get('message')
            if message and message.get('content'):
                role = message.get('author', {}).get('role', 'unknown')

                content_data = message.get('content', {})
                if isinstance(content_data, dict):
                    parts = content_data.get('parts', [])
                    content = '\n'.join(str(p) for p in parts if p)
                else:
                    content = str(content_data)

                if content and content.strip():
                    text += f"**{role.upper()}:** {content}\n\n"

        text += "\n" + "="*70 + "\n\n"
        all_text.append(text)

        # Progress
        if (i + 1) % 100 == 0:
            print(f"   Processando: {i+1}/{len(data)}...")

    # Salvar
    output_file = output_dir / "claude_all_conversations.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(all_text))

    print(f"   ✅ Salvo: {output_file.name} ({len(all_text)} conversas)")
    return len(all_text)

def main():
    print("="*70)
    print("🔄 CONVERSOR JSON → TXT")
    print("="*70)

    base = Path("C:/Users/lucas/Prometheus/knowledge/inbox_raw")

    # GPT
    gpt_json = base / "gpt" / "conversations_gpt.json"
    if gpt_json.exists():
        count = convert_gpt_json(gpt_json, base / "gpt")
        # Remove JSON original
        gpt_json.unlink()
        print(f"   🗑️  JSON original removido")

    # Claude
    claude_json = base / "claude" / "conversations_claude.json"
    if claude_json.exists():
        count = convert_claude_json(claude_json, base / "claude")
        # Remove JSON original
        claude_json.unlink()
        print(f"   🗑️  JSON original removido")

    print("\n" + "="*70)
    print("✅ CONVERSÃO COMPLETA!")
    print("="*70)
    print("\nPróximo passo:")
    print("  python knowledge_ingest.py --dry-run")

if __name__ == '__main__':
    main()
