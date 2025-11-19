-- ============================================
-- PROMETHEUS KNOWLEDGE BRAIN - SCHEMA SUPABASE
-- ============================================
--
-- INSTRUÇÕES DE USO:
-- 1. Acesse: https://app.supabase.com/project/nmjmllqcsyxjrrakyknb/editor/sql
-- 2. Copie e cole TODO este arquivo
-- 3. Clique em "RUN" ou F5
-- 4. Aguarde mensagem de sucesso
--
-- ============================================

-- Passo 1: Habilitar extensão pgvector (embeddings)
CREATE EXTENSION IF NOT EXISTS vector;

-- Passo 2: Tabela de documentos (arquivo completo)
CREATE TABLE IF NOT EXISTS documents (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  file_name TEXT NOT NULL,
  file_hash TEXT UNIQUE NOT NULL,              -- MD5 para deduplicação
  source_type TEXT NOT NULL,                     -- 'claude', 'gpt', 'perplexity'
  original_path TEXT,
  import_date TIMESTAMPTZ DEFAULT NOW(),
  total_chunks INTEGER DEFAULT 0,
  metadata JSONB DEFAULT '{}'::jsonb,            -- tags, categorias, etc
  relevance_count INTEGER DEFAULT 1,             -- quantas vezes foi importado
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Passo 3: Tabela de chunks (pedaços do documento)
CREATE TABLE IF NOT EXISTS document_chunks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
  chunk_index INTEGER NOT NULL,
  content TEXT NOT NULL,
  content_hash TEXT NOT NULL,                    -- deduplicação em nível de chunk
  embedding VECTOR(1536),                        -- OpenAI ada-002 = 1536 dimensões
  tokens INTEGER,
  metadata JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Passo 4: Índices para performance
CREATE INDEX IF NOT EXISTS idx_chunks_document
  ON document_chunks(document_id);

CREATE INDEX IF NOT EXISTS idx_chunks_embedding
  ON document_chunks USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);  -- otimizado para ~10K chunks

CREATE INDEX IF NOT EXISTS idx_documents_hash
  ON documents(file_hash);

CREATE INDEX IF NOT EXISTS idx_chunks_hash
  ON document_chunks(content_hash);

CREATE INDEX IF NOT EXISTS idx_documents_source
  ON documents(source_type);

CREATE INDEX IF NOT EXISTS idx_documents_date
  ON documents(import_date DESC);

-- Passo 5: Função de busca semântica (similaridade vetorial)
CREATE OR REPLACE FUNCTION match_documents(
  query_embedding VECTOR(1536),
  match_threshold FLOAT DEFAULT 0.7,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  id UUID,
  document_id UUID,
  content TEXT,
  similarity FLOAT,
  tokens INTEGER,
  metadata JSONB,
  document_name TEXT,
  document_source TEXT
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    dc.id,
    dc.document_id,
    dc.content,
    1 - (dc.embedding <=> query_embedding) AS similarity,
    dc.tokens,
    dc.metadata,
    d.file_name AS document_name,
    d.source_type AS document_source
  FROM document_chunks dc
  JOIN documents d ON d.id = dc.document_id
  WHERE 1 - (dc.embedding <=> query_embedding) > match_threshold
  ORDER BY dc.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;

-- Passo 6: Função para atualizar updated_at automaticamente
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_documents_updated_at
  BEFORE UPDATE ON documents
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Passo 7: RLS (Row Level Security) - Segurança básica
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

-- Permitir leitura pública (com anon key)
CREATE POLICY "Allow public read access on documents"
  ON documents FOR SELECT
  USING (true);

CREATE POLICY "Allow public read access on chunks"
  ON document_chunks FOR SELECT
  USING (true);

-- Permitir escrita apenas com service_role key
CREATE POLICY "Allow service role to insert documents"
  ON documents FOR INSERT
  WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'authenticated');

CREATE POLICY "Allow service role to update documents"
  ON documents FOR UPDATE
  USING (auth.role() = 'service_role' OR auth.role() = 'authenticated');

CREATE POLICY "Allow service role to insert chunks"
  ON document_chunks FOR INSERT
  WITH CHECK (auth.role() = 'service_role' OR auth.role() = 'authenticated');

-- ============================================
-- VALIDAÇÃO FINAL
-- ============================================

-- Testar se tudo foi criado corretamente
DO $$
DECLARE
  doc_count INTEGER;
  chunk_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO doc_count FROM documents;
  SELECT COUNT(*) INTO chunk_count FROM document_chunks;

  RAISE NOTICE '✅ Schema criado com sucesso!';
  RAISE NOTICE 'Documentos: %', doc_count;
  RAISE NOTICE 'Chunks: %', chunk_count;
  RAISE NOTICE 'Função match_documents: OK';
  RAISE NOTICE 'Índices: OK';
  RAISE NOTICE 'RLS: OK';
END $$;

-- ============================================
-- PRONTO!
-- ============================================
-- O banco está configurado e pronto para receber documentos.
-- Próximo passo: executar knowledge_ingest.py
