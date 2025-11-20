# Prometheus Tools

Scripts utilitários para manutenção e desenvolvimento do Prometheus.

## Estrutura

### utilities/
Scripts de utilidades gerais:
- `check_credentials*.py` - Validação de credenciais API
- `analyze_integration.py` - Análise de integrações
- `generate_report.py` - Geração de relatórios

### fixes/
Scripts de correção e manutenção:
- `fix_*.py` - Scripts de correção diversos
- `clean_*.py` - Scripts de limpeza

### converters/
Scripts de conversão de dados:
- `convert_*.py` - Conversores diversos
- `json_to_text_converter.py` - Conversor JSON→TXT
- `split_*.py` - Scripts de divisão de arquivos
- `decode_jwt.py` - Decodificador JWT

## Uso

Estes scripts **NÃO fazem parte do sistema principal**.

Use conforme necessário para tarefas administrativas e de desenvolvimento.

### Exemplos

```bash
# Verificar credenciais
python tools/utilities/check_credentials.py

# Converter JSON para texto
python tools/converters/json_to_text_converter.py input.json

# Limpar arquivos temporários
python tools/fixes/clean_decorative_text.py
```

## Nota

Scripts mantidos para referência e uso administrativo.
Não são carregados pelo Prometheus Supreme.

---

**Organizados em**: 2025-11-20
**Consolidação**: Fase 3 de 10
