# 🧠 PROMETHEUS KNOWLEDGE BRAIN - TUTORIAL COMPLETO

## ✅ SETUP COMPLETO (FAÇA UMA VEZ)

### 1. Criar Schema no Supabase

1. Abra: https://supabase.com/dashboard/project/nmjmllqcsyxjrrakyknb/sql/new
2. Copie TODO o conteúdo de: `supabase_schema.sql`
3. Cole no editor SQL
4. Clique em **RUN** ou **F5**
5. Aguarde: ✅ "Schema criado com sucesso!"

### 2. Validar Credenciais

```bash
cd C:\Users\lucas\Prometheus
python check_credentials_v2.py
```

Deve mostrar:
```
✅ Supabase: Conexão OK
✅ OpenAI: Conexão OK (102 modelos)
🎉 TUDO PRONTO!
```

---

## 📥 IMPORTAR CONHECIMENTO

### Passo 1: Organizar Arquivos

Coloque seus exports do Claude/GPT/Perplexity em:

```
C:\Users\lucas\Prometheus\knowledge\inbox_raw\
├── claude/          ← Conversas do Claude aqui (.txt, .md, .json)
├── gpt/             ← Conversas do ChatGPT aqui
└── perplexity/      ← Pesquisas do Perplexity aqui
```

### Passo 2: Executar Importação

**Teste primeiro (dry-run):**
```bash
python knowledge_ingest.py --dry-run
```

**Importar de verdade:**
```bash
python knowledge_ingest.py
```

**Importar só Claude:**
```bash
python knowledge_ingest.py --source claude
```

### O que acontece:

```
📄 conversas_claude_2025.txt
   🔒 Sanitized: 3 types (API keys, emails removidos)
   📦 15 chunks (avg 450 tokens)
   🧠 Generating embeddings... OK
   💰 Cost: $0.0067
   ☁️  Uploading... OK (15 new)
   ✅ Moved to cleaned/2025-11-18/

📊 SUMMARY
Files processed: 1
Chunks created: 15
Total cost: $0.0067
```

---

## 🔍 BUSCAR CONHECIMENTO

### Busca Básica

```bash
python knowledge_search.py "configurar RD Station para clínica"
```

### Busca com Mais Resultados

```bash
python knowledge_search.py "automação de marketing" --limit 20
```

### Busca Mais Precisa

```bash
python knowledge_search.py "FastAPI endpoints" --threshold 0.8
```

### Ver Estatísticas

```bash
python knowledge_search.py --stats
```

**Exemplo de output:**

```
🔍 PROMETHEUS KNOWLEDGE SEARCH
======================================================================

Query: configurar RD Station para clínica
Limit: 10 results

🧠 Generating query embedding... OK
📚 Searching knowledge base...

✅ Found 8 results:

======================================================================

#1 - Score: 0.892 (89.2%)
Source: CLAUDE / conversas_marketing_2025.txt
Tokens: 423
----------------------------------------------------------------------
Para configurar o RD Station na clínica, você precisa:
1. Criar conta no RD Station
2. Gerar API Token em Integrações
3. Configurar webhooks para...

#2 - Score: 0.854 (85.4%)
Source: GPT / setup_rdstation.txt
...
```

---

## 💻 USAR NO CÓDIGO PYTHON

```python
from prometheus_v3.knowledge.supabase_client import PrometheusSupabaseClient
from prometheus_v3.knowledge.chunk_processor import ChunkProcessor

# Buscar conhecimento
client = PrometheusSupabaseClient()
chunker = ChunkProcessor()

# Gerar embedding da pergunta
query_embedding = await chunker.generate_embedding(
    "como integrar WhatsApp com CRM?"
)

# Buscar chunks relevantes
results = await client.semantic_search(
    query_embedding,
    limit=5,
    threshold=0.7
)

# Usar resultados
for result in results:
    print(f"Relevância: {result['similarity']:.2f}")
    print(result['content'])
```

---

## 📊 ESTRUTURA DE ARQUIVOS

```
C:\Users\lucas\Prometheus\
│
├── knowledge/
│   ├── inbox_raw/          ← VOCÊ COLOCA AQUIVOS AQUI
│   │   ├── claude/
│   │   ├── gpt/
│   │   └── perplexity/
│   ├── cleaned/            ← Processados vão pra cá (auto)
│   ├── backups/            ← Backups automáticos
│   └── logs/               ← Logs de processamento
│
├── prometheus_v3/knowledge/
│   ├── supabase_client.py     ← Conexão Supabase
│   ├── data_sanitizer.py      ← Remove dados sensíveis
│   ├── chunk_processor.py     ← Quebra + embeddings
│   └── ...
│
├── knowledge_ingest.py        ← SCRIPT DE IMPORTAÇÃO
├── knowledge_search.py        ← SCRIPT DE BUSCA
├── supabase_schema.sql        ← SQL do banco
└── .env                       ← Credenciais
```

---

## 🔒 SEGURANÇA AUTOMÁTICA

O sistema **remove automaticamente** antes de subir:

✅ API Keys (OpenAI, Anthropic, etc)
✅ CPF/CNPJ
✅ E-mails
✅ Telefones
✅ Senhas
✅ Cartões de crédito
✅ Tokens/JWT

Exemplo:
```
ANTES: "Minha API key é sk-abc123def456"
DEPOIS: "Minha API key é [API_KEY_OPENAI_REDACTED]"
```

---

## 💰 CUSTOS

### Setup Inicial
- 10,000 mensagens × 500 palavras = ~8,333 chunks
- Embeddings: **~$1.25 uma vez**

### Uso Mensal
- 500 mensagens/mês × 500 palavras = ~417 chunks
- Embeddings: **~$0.06/mês**

### Supabase
- Plano atual: **Pro** (você já tem!)
- Banco usado: ~100MB (cabe no free tier folgado)
- **$0/mês adicional**

**TOTAL: ~$1.25 setup + $0.06/mês = praticamente grátis!**

---

## 🆘 TROUBLESHOOTING

### "Invalid API key" no Supabase

1. Verifique credenciais em `.env`
2. Confirme que rodou o SQL no Supabase
3. Teste: `python check_credentials_v2.py`

### "Empty file, skipping"

- Arquivo está vazio ou corrompido
- Tente outro formato (.txt, .md, .json)

### "Embedding error"

- Verifique OPENAI_API_KEY no `.env`
- Confirme que tem créditos na OpenAI
- Teste: `python check_credentials_v2.py`

### Busca não retorna resultados

- Threshold muito alto (tente `--threshold 0.5`)
- Banco vazio (rode `knowledge_ingest.py` primeiro)
- Query muito específica (tente termos mais gerais)

---

## 🎯 WORKFLOW COMPLETO

### 1️⃣ Baixar Exports
- Claude: Settings → Export conversations
- ChatGPT: Settings → Data controls → Export
- Perplexity: Copiar e colar em arquivo .txt

### 2️⃣ Organizar
```bash
# Cole arquivos em:
C:\Users\lucas\Prometheus\knowledge\inbox_raw\claude\
C:\Users\lucas\Prometheus\knowledge\inbox_raw\gpt\
```

### 3️⃣ Importar
```bash
cd C:\Users\lucas\Prometheus
python knowledge_ingest.py
```

### 4️⃣ Buscar
```bash
python knowledge_search.py "sua pergunta aqui"
```

### 5️⃣ Usar no Jarvis
```python
# O Jarvis automaticamente consulta o Knowledge Brain
# antes de chamar GPT/Claude!
await jarvis.process_command("configurar RD Station")
```

---

## ✅ CHECKLIST DE VALIDAÇÃO

- [ ] Schema criado no Supabase
- [ ] Credenciais validadas (`check_credentials_v2.py`)
- [ ] Diretórios criados (`knowledge/inbox_raw/...`)
- [ ] Arquivo de teste importado
- [ ] Busca funcionando
- [ ] Stats mostrando documentos

---

## 📞 SUPORTE

**Documentação Completa:**
- `GUIA_CREDENCIAIS.md` - Como pegar credenciais
- `supabase_schema.sql` - Schema do banco
- Código: `prometheus_v3/knowledge/`

**Logs:**
```bash
# Logs de importação
C:\Users\lucas\Prometheus\knowledge\logs\

# Ver último log
cat knowledge/logs/ingest_*.json
```

---

🎉 **SISTEMA PRONTO PARA USO!**

Qualquer dúvida, execute:
```bash
python knowledge_search.py --help
python knowledge_ingest.py --help
```
