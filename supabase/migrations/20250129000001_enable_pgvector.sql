-- Enable pgvector for RAG embeddings (used later by Edge Functions)
CREATE EXTENSION IF NOT EXISTS vector;

-- Optional: table for document chunks and embeddings (defer until Edge Functions use it)
-- Uncomment when you add vector search in agent-chat/agent-scan
/*
CREATE TABLE IF NOT EXISTS public.document_embeddings (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  entity_id text NOT NULL,
  entity_type text NOT NULL DEFAULT 'Accounts',
  content text NOT NULL,
  embedding vector(384),
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS document_embeddings_entity
  ON public.document_embeddings (entity_type, entity_id);
CREATE INDEX IF NOT EXISTS document_embeddings_embedding
  ON public.document_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
*/
