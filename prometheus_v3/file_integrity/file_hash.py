"""
File Hash Generator
Gera hashes SHA-256 de arquivos para detecção de mutações
"""

import hashlib
from pathlib import Path
from typing import Optional
from datetime import datetime
import json


class FileHasher:
    """
    Gerenciador de hashes de arquivos para detecção de integridade
    """

    CHUNK_SIZE = 8192  # 8KB chunks para arquivos grandes

    def __init__(self):
        self.algorithm = "sha256"

    def hash_file(self, file_path: str | Path) -> Optional[str]:
        """
        Gera hash SHA-256 de um arquivo

        Args:
            file_path: Caminho do arquivo

        Returns:
            Hash SHA-256 em hexadecimal ou None se erro

        Example:
            >>> hasher = FileHasher()
            >>> hash_val = hasher.hash_file("executor/browser_executor.py")
            >>> print(f"Hash: {hash_val}")
        """
        try:
            path = Path(file_path)

            if not path.exists():
                return None

            if not path.is_file():
                return None

            sha256_hash = hashlib.sha256()

            with open(path, "rb") as f:
                # Ler em chunks para suportar arquivos grandes
                for chunk in iter(lambda: f.read(self.CHUNK_SIZE), b""):
                    sha256_hash.update(chunk)

            return sha256_hash.hexdigest()

        except Exception as e:
            print(f"[FileHasher] Erro ao gerar hash de {file_path}: {e}")
            return None

    def hash_content(self, content: str | bytes) -> str:
        """
        Gera hash de conteúdo em memória

        Args:
            content: String ou bytes para gerar hash

        Returns:
            Hash SHA-256 em hexadecimal
        """
        if isinstance(content, str):
            content = content.encode('utf-8')

        return hashlib.sha256(content).hexdigest()

    def verify_file(self, file_path: str | Path, expected_hash: str) -> bool:
        """
        Verifica se hash atual do arquivo corresponde ao esperado

        Args:
            file_path: Caminho do arquivo
            expected_hash: Hash esperado

        Returns:
            True se hash corresponde, False caso contrário
        """
        current_hash = self.hash_file(file_path)

        if current_hash is None:
            return False

        return current_hash == expected_hash

    def batch_hash(self, file_paths: list[str | Path]) -> dict[str, Optional[str]]:
        """
        Gera hashes de múltiplos arquivos

        Args:
            file_paths: Lista de caminhos de arquivos

        Returns:
            Dicionário {caminho: hash}
        """
        results = {}

        for file_path in file_paths:
            path_str = str(file_path)
            results[path_str] = self.hash_file(file_path)

        return results

    def hash_with_metadata(self, file_path: str | Path) -> dict:
        """
        Gera hash com metadados do arquivo

        Args:
            file_path: Caminho do arquivo

        Returns:
            Dict com hash, size, modified_at, etc.
        """
        path = Path(file_path)

        if not path.exists():
            return {
                "error": "File not found",
                "path": str(file_path)
            }

        stat = path.stat()
        file_hash = self.hash_file(path)

        return {
            "path": str(path),
            "hash": file_hash,
            "size_bytes": stat.st_size,
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "algorithm": self.algorithm,
            "timestamp": datetime.now().isoformat()
        }


# Função helper para uso rápido
def quick_hash(file_path: str | Path) -> Optional[str]:
    """
    Hash rápido de arquivo (função utilitária)

    Args:
        file_path: Caminho do arquivo

    Returns:
        Hash SHA-256 ou None
    """
    hasher = FileHasher()
    return hasher.hash_file(file_path)
