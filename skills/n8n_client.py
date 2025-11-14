"""
Prometheus - n8n Client Skill
Integração com n8n para automação de workflows
"""

import os
import requests
from typing import Dict, Any
from .logs import setup_logger

logger = setup_logger(__name__, "./logs/prometheus.log")


def trigger_workflow(webhook_url: str = None, payload: Dict[Any, Any] = None) -> Dict:
    """
    Dispara um workflow no n8n via webhook

    Args:
        webhook_url: URL do webhook do n8n (se None, usa N8N_WEBHOOK_URL do .env)
        payload: Dados a enviar para o workflow

    Returns:
        Dict com resposta do n8n
    """
    try:
        # Usar URL do .env se não fornecida
        if webhook_url is None:
            webhook_url = os.getenv("N8N_WEBHOOK_URL")

        if not webhook_url:
            logger.error("N8N_WEBHOOK_URL não configurada")
            return {"success": False, "error": "Webhook URL not configured"}

        logger.info(f"Disparando workflow n8n: {webhook_url}")

        # Preparar payload
        if payload is None:
            payload = {}

        # Adicionar timestamp
        import datetime
        payload["timestamp"] = datetime.datetime.now().isoformat()
        payload["source"] = "prometheus"

        # Fazer requisição
        response = requests.post(
            webhook_url,
            json=payload,
            timeout=10
        )

        response.raise_for_status()

        logger.info(f"Workflow disparado com sucesso. Status: {response.status_code}")

        return {
            "success": True,
            "status_code": response.status_code,
            "response": response.json() if response.content else {}
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao disparar workflow n8n: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Erro inesperado: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def check_n8n_health() -> Dict:
    """
    Verifica se n8n está rodando

    Returns:
        Dict com status do n8n
    """
    try:
        logger.info("Verificando saúde do n8n")

        n8n_url = os.getenv("N8N_URL", "http://localhost:5678")

        response = requests.get(f"{n8n_url}/healthz", timeout=5)

        is_healthy = response.status_code == 200

        logger.info(f"n8n status: {'saudável' if is_healthy else 'com problemas'}")

        return {
            "success": True,
            "healthy": is_healthy,
            "status_code": response.status_code
        }

    except requests.exceptions.ConnectionError:
        logger.warning("n8n não está acessível")
        return {"success": False, "healthy": False, "error": "Connection refused"}
    except Exception as e:
        logger.error(f"Erro ao verificar n8n: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def get_workflows_list() -> Dict:
    """
    Lista workflows disponíveis no n8n (requer autenticação)

    Returns:
        Dict com lista de workflows
    """
    try:
        logger.info("Listando workflows do n8n")

        n8n_url = os.getenv("N8N_URL", "http://localhost:5678")
        n8n_user = os.getenv("N8N_BASIC_AUTH_USER", "prometheus")
        n8n_pass = os.getenv("N8N_BASIC_AUTH_PASSWORD", "password123")

        response = requests.get(
            f"{n8n_url}/api/v1/workflows",
            auth=(n8n_user, n8n_pass),
            timeout=5
        )

        response.raise_for_status()

        workflows = response.json()

        logger.info(f"Encontrados {len(workflows.get('data', []))} workflows")

        return {
            "success": True,
            "count": len(workflows.get('data', [])),
            "workflows": workflows.get('data', [])
        }

    except Exception as e:
        logger.error(f"Erro ao listar workflows: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
