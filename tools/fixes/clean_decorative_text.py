#!/usr/bin/env python
"""Remove texto decorativo dos arquivos v3.5"""

import re
from pathlib import Path

files_to_clean = [
    "prometheus_v3/safe_write/safe_write_test.py",
    "prometheus_v3/supervisor_ext/config_watcher.py",
    "prometheus_v3/tests/test_supervisor.py"
]

for file_path in files_to_clean:
    path = Path(file_path)
    if not path.exists():
        print(f"[SKIP] {file_path} não existe")
        continue
    
    content = path.read_text(encoding='utf-8')
    lines = content.split('\n')
    
    # Encontrar linha onde começa texto decorativo (emoji ou CHECKPOINT sem indent)
    clean_lines = []
    for i, line in enumerate(lines):
        # Se linha começa sem indent e tem emoji/CHECKPOINT, para aqui
        if line and not line[0].isspace() and not line.startswith('#'):
            # Verifica se tem caracteres Unicode altos (emojis)
            if any(ord(c) > 127 for c in line):
                print(f"[CLEAN] {file_path} - removendo de linha {i+1}")
                break
        clean_lines.append(line)
    
    # Escrever conteúdo limpo
    path.write_text('\n'.join(clean_lines), encoding='utf-8')
    print(f"[OK] {file_path} limpo")

print("\nConcluído!")
