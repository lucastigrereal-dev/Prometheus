import sys

# Tentar diferentes formas de importar
try:
    import interpreter
    print("✓ Modulo 'interpreter' importado com sucesso!")
    print(f"  Versao: {interpreter.__version__ if hasattr(interpreter, '__version__') else 'N/A'}")
except ImportError as e:
    print(f"✗ 'interpreter': {e}")

try:
    import open_interpreter
    print("✓ Modulo 'open_interpreter' importado com sucesso!")
except ImportError as e:
    print(f"✗ 'open_interpreter': {e}")

# Verificar o que está disponível
import os
site_packages = os.path.join(sys.prefix, 'Lib', 'site-packages')
print(f"\nSite-packages: {site_packages}")

# Listar diretórios que começam com 'inter' ou 'open'
if os.path.exists(site_packages):
    items = [d for d in os.listdir(site_packages) if 'inter' in d.lower() or 'open' in d.lower()]
    print(f"\nPacotes relacionados encontrados:")
    for item in sorted(items)[:10]:
        print(f"  - {item}")
