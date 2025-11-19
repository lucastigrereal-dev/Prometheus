# Prometheus Dashboard API

FastAPI backend para o Prometheus Command Center.

## Setup

```bash
# Instalar dependências
pip install -r requirements.txt

# Rodar servidor
python main.py
```

Servidor disponível em: http://localhost:8000

## Endpoints

### GET /api/stats
Retorna estatísticas do Knowledge Brain.

**Response:**
```json
{
  "total_documents": 117,
  "total_chunks": 2664,
  "claude_count": 2,
  "gpt_count": 115
}
```

### POST /api/search
Busca semântica no Knowledge Brain.

**Request:**
```json
{
  "query": "como implementar autenticação",
  "limit": 10
}
```

**Response:**
```json
{
  "results": [
    {
      "content": "...",
      "similarity": 0.85,
      "source_type": "claude",
      "created_at": "2025-11-18T10:30:00",
      "tokens": 450
    }
  ],
  "count": 10
}
```

## Arquitetura

- **FastAPI**: Framework web moderno e rápido
- **Supabase**: Database PostgreSQL com pgvector
- **OpenAI**: Embeddings para busca semântica
- **CORS**: Habilitado para Next.js frontend
