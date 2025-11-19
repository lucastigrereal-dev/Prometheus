"""
Knowledge Query - Busca contexto relevante no Knowledge Brain
"""

from typing import List, Dict, Any, Optional
import os

class KnowledgeQuery:
    """Interface para buscar conhecimento no Supabase"""

    def __init__(self, supabase_client=None):
        self.supabase = supabase_client

        # Se não passou client, criar um
        if not self.supabase:
            from dotenv import load_dotenv
            from supabase import create_client

            load_dotenv()

            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

            if supabase_url and supabase_key:
                self.supabase = create_client(supabase_url, supabase_key)

    def search_relevant_knowledge(
        self,
        query: str,
        limit: int = 5,
        similarity_threshold: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Busca conhecimento relevante para a query

        Args:
            query: Texto da busca
            limit: Quantos resultados retornar
            similarity_threshold: Threshold mínimo de similaridade

        Returns:
            Lista de chunks relevantes
        """
        if not self.supabase:
            return []

        try:
            # Gerar embedding da query
            from openai import OpenAI
            client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

            response = client.embeddings.create(
                input=query,
                model="text-embedding-ada-002"
            )
            query_embedding = response.data[0].embedding

            # Buscar no Supabase
            result = self.supabase.rpc(
                'match_documents',
                {
                    'query_embedding': query_embedding,
                    'match_threshold': similarity_threshold,
                    'match_count': limit
                }
            ).execute()

            # Formatar resultados
            knowledge_results = []

            if result.data:
                for row in result.data:
                    knowledge_results.append({
                        'content': row['content'],
                        'similarity': row['similarity'],
                        'source_type': row['document_source'],
                        'tokens': row['tokens'],
                        'metadata': row.get('metadata', {})
                    })

            return knowledge_results

        except Exception as e:
            print(f"Erro ao buscar conhecimento: {e}")
            return []

    def get_conversation_context(
        self,
        topic: str,
        source_type: Optional[str] = None
    ) -> str:
        """
        Retorna contexto de conversas sobre um tópico específico

        Args:
            topic: Tópico a buscar
            source_type: Filtrar por fonte (claude, gpt, perplexity)

        Returns:
            String com contexto agregado
        """
        results = self.search_relevant_knowledge(topic, limit=3)

        if not results:
            return "Nenhum conhecimento prévio encontrado sobre este tópico."

        # Agregar contexto
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[Contexto {i} - Similaridade: {result['similarity']:.0%}]\n"
                f"{result['content'][:500]}..."  # Limitar tamanho
            )

        return "\n\n".join(context_parts)
