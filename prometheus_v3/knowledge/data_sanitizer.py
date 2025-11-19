# -*- coding: utf-8 -*-
"""
DATA SANITIZER - Remoção Profissional de Dados Sensíveis

Remove automaticamente:
- API Keys (OpenAI, Anthropic, etc)
- CPF/CNPJ
- E-mails
- Telefones
- Senhas
- Cartões de crédito
- Endereços IP
"""

import re
import logging
from typing import Tuple, List, Dict

logger = logging.getLogger(__name__)


class DataSanitizer:
    """Remove dados sensíveis antes de upload ao Supabase"""

    # Padrões regex para detecção
    PATTERNS = {
        # API Keys
        'api_key_openai': r'sk-[a-zA-Z0-9]{48,}',
        'api_key_anthropic': r'sk-ant-[a-zA-Z0-9\-]{95,}',
        'api_key_generic': r'api[_-]?key[\s:=]+["\']?([a-zA-Z0-9_\-]{20,})["\']?',

        # Documentos brasileiros
        'cpf': r'\d{3}\.?\d{3}\.?\d{3}-?\d{2}',
        'cnpj': r'\d{2}\.?\d{3}\.?\d{3}/?0001-?\d{2}',
        'rg': r'(RG|R\.G\.)[\s:]*([\d.]{8,12})',

        # Contatos
        'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}',
        'phone_br': r'(\(?\d{2}\)?\s?)?\d{4,5}-?\d{4}',
        'whatsapp': r'(whatsapp|wpp)[\s:]+\(?\d{2}\)?\s?\d{4,5}-?\d{4}',

        # Credenciais
        'password': r'(password|senha|pass|pwd)[\s:=]+["\']?([^\s"\']{6,})["\']?',
        'token': r'(token|bearer)[\s:=]+["\']?([a-zA-Z0-9_\-\.]{20,})["\']?',

        # Financeiro
        'credit_card': r'\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}',
        'pix_key': r'(chave pix|pix)[\s:]+([a-zA-Z0-9@.\-]{11,})',

        # Técnico
        'ip_address': r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
        'jwt': r'eyJ[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}',

        # URLs sensíveis
        'url_with_token': r'https?://[^\s]*[?&](token|key|api_key)=[a-zA-Z0-9_\-]{10,}',
    }

    def __init__(self, custom_patterns: Dict[str, str] = None):
        """
        Inicializa sanitizer

        Args:
            custom_patterns: Padrões adicionais personalizados
        """
        self.patterns = self.PATTERNS.copy()

        if custom_patterns:
            self.patterns.update(custom_patterns)
            logger.info(f"Added {len(custom_patterns)} custom patterns")

        self.stats = {
            'total_redactions': 0,
            'by_type': {}
        }

    def sanitize(self, text: str, preserve_structure: bool = True) -> Tuple[str, List[str]]:
        """
        Remove dados sensíveis e retorna texto limpo + lista de redações

        Args:
            text: Texto original
            preserve_structure: Se True, mantém tamanho similar com [REDACTED]

        Returns:
            (texto_limpo, ["API Key redacted (2x)", "CPF redacted (1x)"])
        """
        redacted = []
        cleaned_text = text

        for key, pattern in self.patterns.items():
            matches = re.findall(pattern, cleaned_text, re.IGNORECASE)

            if matches:
                count = len(matches)

                # Substituir por placeholder
                if preserve_structure:
                    replacement = f'[{key.upper()}_REDACTED]'
                else:
                    replacement = ''

                cleaned_text = re.sub(
                    pattern,
                    replacement,
                    cleaned_text,
                    flags=re.IGNORECASE
                )

                # Registrar redação
                redaction_msg = f"{key.upper()} redacted ({count}x)"
                redacted.append(redaction_msg)

                # Stats
                self.stats['total_redactions'] += count
                self.stats['by_type'][key] = self.stats['by_type'].get(key, 0) + count

                logger.info(f"Redacted {count} instances of {key}")

        return cleaned_text, redacted

    def is_safe(self, text: str) -> bool:
        """
        Verifica se texto não contém dados sensíveis

        Args:
            text: Texto a verificar

        Returns:
            True se seguro, False se encontrou dados sensíveis
        """
        for key, pattern in self.patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"Found sensitive data: {key}")
                return False

        return True

    def get_stats(self) -> Dict:
        """Retorna estatísticas de redações"""
        return self.stats.copy()

    def reset_stats(self):
        """Reseta estatísticas"""
        self.stats = {
            'total_redactions': 0,
            'by_type': {}
        }


# Exemplo de uso
if __name__ == "__main__":
    sanitizer = DataSanitizer()

    test_text = """
    Aqui está minha API key: sk-abc123def456ghi789
    Meu CPF é 123.456.789-10
    Email: usuario@exemplo.com
    Telefone: (11) 98765-4321
    Senha: minhasenha123
    """

    clean, redactions = sanitizer.sanitize(test_text)

    print("TEXTO LIMPO:")
    print(clean)
    print("\nREDAÇÕES:")
    for r in redactions:
        print(f"  - {r}")
