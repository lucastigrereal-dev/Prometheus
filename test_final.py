try:
    import interpreter
    print("=" * 60)
    print("SUCCESS! OpenInterpreter esta instalado!")
    print("=" * 60)
    print(f"Modulo: interpreter")
    print(f"Localização: {interpreter.__file__}")
    print("")
    print("Para iniciar o OpenInterpreter:")
    print("  python -m interpreter")
    print("  ou")
    print("  interpreter")
    print("=" * 60)
except Exception as e:
    print(f"ERRO: {e}")
