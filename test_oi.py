#!/usr/bin/env python3
"""Teste rapido do OpenInterpreter"""

try:
    import open_interpreter
    print("=" * 60)
    print("TESTE DO OPENINTERPRETER")
    print("=" * 60)
    print(f"Versao: {open_interpreter.__version__}")
    print("Status: OK - Pronto para usar!")
    print("")
    print("Para iniciar o OpenInterpreter, execute:")
    print("  python -m open_interpreter")
    print("=" * 60)
except ImportError as e:
    print(f"ERRO: {e}")
    print("OpenInterpreter nao esta instalado corretamente")
