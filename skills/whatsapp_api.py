"""
Prometheus - WhatsApp API Skill
Integração com WhatsApp Cloud API
"""

import os
import requests
from typing import Dict
from .logs import setup_logger

logger = setup_logger(__name__, "./logs/prometheus.log")


def send_text_message(phone: str, message: str) -> Dict:
    """
    Envia mensagem de texto via WhatsApp Cloud API

    Args:
        phone: Número de telefone (formato: 5511999999999)
        message: Texto da mensagem

    Returns:
        Dict com resultado do envio
    """
    try:
        logger.info(f"Enviando mensagem WhatsApp para: {phone}")

        # Ler credenciais do .env
        phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")

        if not phone_number_id or not access_token:
            logger.error("Credenciais WhatsApp não configuradas")
            return {
                "success": False,
                "error": "WHATSAPP_PHONE_NUMBER_ID ou WHATSAPP_ACCESS_TOKEN não configurados"
            }

        # URL da API
        url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"

        # Headers
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # Payload
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "text",
            "text": {
                "body": message
            }
        }

        # Fazer requisição
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=10
        )

        response.raise_for_status()

        result = response.json()

        logger.info(f"Mensagem WhatsApp enviada com sucesso para {phone}")

        return {
            "success": True,
            "message_id": result.get("messages", [{}])[0].get("id"),
            "response": result
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Erro ao enviar mensagem WhatsApp: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
    except Exception as e:
        logger.error(f"Erro inesperado: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def send_template_message(phone: str, template_name: str, language: str = "pt_BR") -> Dict:
    """
    Envia mensagem template aprovada via WhatsApp Cloud API

    Args:
        phone: Número de telefone
        template_name: Nome do template aprovado
        language: Código do idioma (padrão: pt_BR)

    Returns:
        Dict com resultado do envio
    """
    try:
        logger.info(f"Enviando template WhatsApp '{template_name}' para: {phone}")

        phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")

        if not phone_number_id or not access_token:
            logger.error("Credenciais WhatsApp não configuradas")
            return {"success": False, "error": "Credenciais não configuradas"}

        url = f"https://graph.facebook.com/v18.0/{phone_number_id}/messages"

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language
                }
            }
        }

        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()

        result = response.json()

        logger.info(f"Template WhatsApp enviado com sucesso")

        return {
            "success": True,
            "message_id": result.get("messages", [{}])[0].get("id"),
            "response": result
        }

    except Exception as e:
        logger.error(f"Erro ao enviar template WhatsApp: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def get_media_url(media_id: str) -> Dict:
    """
    Obtém URL de mídia recebida via WhatsApp

    Args:
        media_id: ID da mídia

    Returns:
        Dict com URL da mídia
    """
    try:
        logger.info(f"Obtendo URL de mídia: {media_id}")

        access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")

        if not access_token:
            return {"success": False, "error": "Access token não configurado"}

        url = f"https://graph.facebook.com/v18.0/{media_id}"

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        result = response.json()

        logger.info("URL de mídia obtida com sucesso")

        return {
            "success": True,
            "url": result.get("url"),
            "mime_type": result.get("mime_type"),
            "file_size": result.get("file_size")
        }

    except Exception as e:
        logger.error(f"Erro ao obter URL de mídia: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
