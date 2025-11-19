# -*- coding: utf-8 -*-
"""
JSON to Text Converter - Converte conversas JSON do Claude para formato texto

USO:
    python json_to_text_converter.py --input conversations.json --output claude_conversations.txt
"""

import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


def extract_text_from_message(message: Dict[str, Any]) -> str:
    """
    Extrai texto de uma mensagem Claude (múltiplos formatos possíveis)

    Args:
        message: Dict com dados da mensagem

    Returns:
        Texto extraído
    """
    text_parts = []

    # Formato 1: content direto (string)
    if isinstance(message.get('content'), str):
        text_parts.append(message['content'])

    # Formato 2: content como lista de objetos
    elif isinstance(message.get('content'), list):
        for item in message['content']:
            if isinstance(item, dict):
                # Text block
                if item.get('type') == 'text' and item.get('text'):
                    text_parts.append(item['text'])
                # Outros tipos (pode ter code_block, etc)
                elif 'text' in item:
                    text_parts.append(item['text'])

    # Formato 3: text direto
    elif message.get('text'):
        text_parts.append(message['text'])

    return '\n'.join(text_parts).strip()


def format_conversation(conversation: Dict[str, Any], index: int) -> str:
    """
    Formata uma conversa completa para texto

    Args:
        conversation: Dict com dados da conversa
        index: Índice da conversa

    Returns:
        Texto formatado
    """
    lines = []

    # Header
    lines.append("="*80)
    lines.append(f"CONVERSATION {index + 1}")
    lines.append("="*80)

    # Metadados
    if conversation.get('name'):
        lines.append(f"Title: {conversation['name']}")

    if conversation.get('created_at'):
        try:
            timestamp = conversation['created_at']
            # Se for timestamp Unix
            if isinstance(timestamp, (int, float)):
                dt = datetime.fromtimestamp(timestamp)
            # Se for ISO string
            else:
                dt = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
            lines.append(f"Created: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        except:
            lines.append(f"Created: {conversation['created_at']}")

    if conversation.get('updated_at'):
        try:
            timestamp = conversation['updated_at']
            if isinstance(timestamp, (int, float)):
                dt = datetime.fromtimestamp(timestamp)
            else:
                dt = datetime.fromisoformat(str(timestamp).replace('Z', '+00:00'))
            lines.append(f"Updated: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        except:
            lines.append(f"Updated: {conversation['updated_at']}")

    lines.append("")

    # Mensagens
    chat_messages = conversation.get('chat_messages', [])

    if not chat_messages:
        lines.append("(No messages)")
    else:
        for i, message in enumerate(chat_messages):
            # Role (user ou assistant)
            sender = message.get('sender', 'unknown')
            role = "USER" if sender == "human" else "ASSISTANT"

            lines.append(f"--- {role} ---")

            # Extrair e adicionar texto
            text = extract_text_from_message(message)
            if text:
                lines.append(text)
            else:
                lines.append("(Empty message)")

            lines.append("")

    lines.append("")
    return '\n'.join(lines)


def convert_json_to_text(
    input_path: Path,
    output_path: Path,
    max_conversations: int = None,
    show_progress: bool = True
):
    """
    Converte arquivo JSON de conversas para texto

    Args:
        input_path: Caminho do arquivo JSON
        output_path: Caminho do arquivo de saída TXT
        max_conversations: Limite de conversas (None = todas)
        show_progress: Se True, mostra progresso
    """
    print(f"Reading {input_path.name}...")

    # Ler JSON
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Pode ser uma lista direta ou um objeto com chave 'conversations'
    if isinstance(data, list):
        conversations = data
    elif isinstance(data, dict) and 'conversations' in data:
        conversations = data['conversations']
    elif isinstance(data, dict):
        # Pode ser um único objeto de conversa
        conversations = [data]
    else:
        raise ValueError(f"Formato JSON não reconhecido: {type(data)}")

    total = len(conversations)
    if max_conversations:
        conversations = conversations[:max_conversations]

    print(f"Found {total} conversations")
    if max_conversations:
        print(f"Processing first {max_conversations}...")

    # Converter cada conversa
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, conversation in enumerate(conversations):
            if show_progress and (i + 1) % 100 == 0:
                print(f"  Processed {i + 1}/{len(conversations)}...")

            text = format_conversation(conversation, i)
            f.write(text)
            f.write('\n\n')

    print(f"[OK] Saved to {output_path}")
    print(f"  Total conversations: {len(conversations)}")

    # Estatísticas
    output_size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"  Output size: {output_size_mb:.2f} MB")


def main():
    parser = argparse.ArgumentParser(description='Convert Claude JSON to text')
    parser.add_argument('--input', required=True, help='Input JSON file')
    parser.add_argument('--output', required=True, help='Output TXT file')
    parser.add_argument('--max', type=int, help='Max conversations to process')
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Error: {input_path} not found")
        return

    convert_json_to_text(
        input_path,
        output_path,
        max_conversations=args.max
    )


if __name__ == '__main__':
    main()
