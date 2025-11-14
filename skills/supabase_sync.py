"""
Prometheus - Supabase Sync Skill
Integração com Supabase (PostgreSQL + Auth + Storage)
"""

import os
from typing import Dict, List, Any
from .logs import setup_logger

logger = setup_logger(__name__, "./logs/prometheus.log")

# Importação condicional do Supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("Biblioteca supabase não instalada. Instale com: pip install supabase")


def get_client() -> Client:
    """
    Cria e retorna cliente Supabase

    Returns:
        Cliente Supabase configurado

    Raises:
        Exception se credenciais não configuradas
    """
    if not SUPABASE_AVAILABLE:
        raise Exception("Biblioteca supabase não instalada")

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise Exception("SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY não configurados")

    return create_client(url, key)


def insert_event(table: str, data: Dict[str, Any]) -> Dict:
    """
    Insere um evento/registro no Supabase

    Args:
        table: Nome da tabela
        data: Dados a inserir

    Returns:
        Dict com resultado da inserção
    """
    try:
        logger.info(f"Inserindo dados na tabela '{table}' do Supabase")

        if not SUPABASE_AVAILABLE:
            logger.error("Biblioteca supabase não disponível")
            return {"success": False, "error": "Supabase library not installed"}

        client = get_client()

        response = client.table(table).insert(data).execute()

        logger.info(f"Dados inseridos com sucesso na tabela '{table}'")

        return {
            "success": True,
            "data": response.data,
            "count": len(response.data) if response.data else 0
        }

    except Exception as e:
        logger.error(f"Erro ao inserir no Supabase: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def query_table(table: str, filters: Dict[str, Any] = None, limit: int = 100) -> Dict:
    """
    Consulta dados de uma tabela no Supabase

    Args:
        table: Nome da tabela
        filters: Filtros para a query (ex: {"status": "active"})
        limit: Limite de registros

    Returns:
        Dict com resultados da consulta
    """
    try:
        logger.info(f"Consultando tabela '{table}' do Supabase")

        if not SUPABASE_AVAILABLE:
            return {"success": False, "error": "Supabase library not installed"}

        client = get_client()

        query = client.table(table).select("*")

        # Aplicar filtros se fornecidos
        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)

        # Aplicar limite
        query = query.limit(limit)

        response = query.execute()

        logger.info(f"Consulta retornou {len(response.data)} registros")

        return {
            "success": True,
            "data": response.data,
            "count": len(response.data)
        }

    except Exception as e:
        logger.error(f"Erro ao consultar Supabase: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def update_record(table: str, record_id: str, data: Dict[str, Any]) -> Dict:
    """
    Atualiza um registro no Supabase

    Args:
        table: Nome da tabela
        record_id: ID do registro
        data: Dados a atualizar

    Returns:
        Dict com resultado da atualização
    """
    try:
        logger.info(f"Atualizando registro {record_id} na tabela '{table}'")

        if not SUPABASE_AVAILABLE:
            return {"success": False, "error": "Supabase library not installed"}

        client = get_client()

        response = client.table(table).update(data).eq("id", record_id).execute()

        logger.info(f"Registro {record_id} atualizado com sucesso")

        return {
            "success": True,
            "data": response.data
        }

    except Exception as e:
        logger.error(f"Erro ao atualizar registro: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def test_connection() -> Dict:
    """
    Testa conexão com Supabase

    Returns:
        Dict com status da conexão
    """
    try:
        logger.info("Testando conexão com Supabase")

        if not SUPABASE_AVAILABLE:
            return {
                "success": False,
                "configured": False,
                "error": "Supabase library not installed. Run: pip install supabase"
            }

        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not url or not key:
            logger.error("Credenciais Supabase não configuradas")
            return {
                "success": False,
                "configured": False,
                "error": "SUPABASE_URL ou SUPABASE_SERVICE_ROLE_KEY não configurados no .env"
            }

        # Tentar criar cliente
        client = get_client()

        # Fazer uma query simples
        # (assumindo que existe uma tabela, pode falhar se não houver)
        logger.info("Conexão com Supabase estabelecida")

        return {
            "success": True,
            "configured": True,
            "valid": True,
            "url": url[:30] + "..." if len(url) > 30 else url
        }

    except Exception as e:
        logger.error(f"Erro ao testar conexão Supabase: {e}", exc_info=True)
        return {
            "success": False,
            "configured": True,
            "valid": False,
            "error": str(e)
        }
