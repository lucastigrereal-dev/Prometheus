"""
Prometheus - RD Station Client Skill
Integração com RD Station CRM/Marketing
"""

import os
import requests
from typing import Dict, Any
from .logs import setup_logger

logger = setup_logger(__name__, "./logs/prometheus.log")


def create_or_update_lead(email: str, data: Dict[str, Any] = None) -> Dict:
    """
    Cria ou atualiza um lead no RD Station

    Args:
        email: Email do lead (obrigatório)
        data: Dados adicionais do lead (nome, telefone, etc.)

    Returns:
        Dict com resultado da operação
    """
    try:
        logger.info(f"Criando/atualizando lead no RD Station: {email}")

        # Ler token do .env
        api_token = os.getenv("RDSTATION_API_TOKEN")

        if not api_token:
            logger.error("RDSTATION_API_TOKEN não configurado")
            return {"success": False, "error": "API token não configurado"}

        # URL da API
        url = "https://api.rd.services/platform/conversions"

        # Headers
        headers = {
            "Content-Type": "application/json"
        }

        # Preparar payload base
        payload = {
            "event_type": "CONVERSION",
            "event_family": "CDP",
            "payload": {
                "conversion_identifier": "prometheus_lead",
                "email": email
            }
        }

        # Adicionar dados extras se fornecidos
        if data:
            payload["payload"].update(data)

        # Adicionar token ao payload
        payload["api_key"] = api_token

        # Fazer requisição
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=10
        )

        response.raise_for_status()

        result = response.json() if response.content else {}

        logger.info(f"Lead criado/atualizado com sucesso: {email}")

        return {
            "success": True,
            "status_code": response.status_code,
            "response": result
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao criar/atualizar lead: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Erro inesperado: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def get_lead(email: str) -> Dict:
    """
    Busca informações de um lead no RD Station

    Args:
        email: Email do lead

    Returns:
        Dict com dados do lead
    """
    try:
        logger.info(f"Buscando lead no RD Station: {email}")

        api_token = os.getenv("RDSTATION_API_TOKEN")

        if not api_token:
            logger.error("RDSTATION_API_TOKEN não configurado")
            return {"success": False, "error": "API token não configurado"}

        # URL da API (usando API de contatos)
        url = f"https://api.rd.services/platform/contacts/email:{email}"

        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 404:
            logger.warning(f"Lead não encontrado: {email}")
            return {"success": False, "error": "Lead not found"}

        response.raise_for_status()

        result = response.json()

        logger.info(f"Lead encontrado: {email}")

        return {
            "success": True,
            "lead": result
        }

    except Exception as e:
        logger.error(f"Erro ao buscar lead: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def test_connection() -> Dict:
    """
    Testa conexão com RD Station API

    Returns:
        Dict com status da conexão
    """
    try:
        logger.info("Testando conexão com RD Station")

        api_token = os.getenv("RDSTATION_API_TOKEN")

        if not api_token:
            logger.error("RDSTATION_API_TOKEN não configurado")
            return {
                "success": False,
                "configured": False,
                "error": "API token não configurado no .env"
            }

        # Tentar listar campos (endpoint simples para testar)
        url = "https://api.rd.services/platform/contacts/fields"

        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

        response = requests.get(url, headers=headers, timeout=10)

        is_valid = response.status_code == 200

        if is_valid:
            logger.info("Conexão com RD Station OK")
        else:
            logger.warning(f"Conexão com RD Station falhou: {response.status_code}")

        return {
            "success": True,
            "configured": True,
            "valid": is_valid,
            "status_code": response.status_code
        }

    except Exception as e:
        logger.error(f"Erro ao testar conexão: {e}", exc_info=True)
        return {
            "success": False,
            "configured": True,
            "valid": False,
            "error": str(e)
        }
