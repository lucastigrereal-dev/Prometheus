"""
Prometheus - System Control Skill
Controle do sistema operacional, arquivos e processos
"""

import os
import subprocess
import platform
from pathlib import Path
from typing import List, Dict
from .logs import setup_logger

logger = setup_logger(__name__, "./logs/prometheus.log")


def list_files(path: str = ".") -> List[str]:
    """
    Lista arquivos em um diretório

    Args:
        path: Caminho do diretório

    Returns:
        Lista de nomes de arquivos
    """
    try:
        logger.info(f"Listando arquivos em: {path}")
        path_obj = Path(path).resolve()

        if not path_obj.exists():
            logger.error(f"Caminho não existe: {path}")
            return []

        if not path_obj.is_dir():
            logger.error(f"Caminho não é um diretório: {path}")
            return []

        files = [item.name for item in path_obj.iterdir()]
        logger.info(f"Encontrados {len(files)} itens em {path}")
        return files

    except Exception as e:
        logger.error(f"Erro ao listar arquivos: {e}", exc_info=True)
        return []


def open_folder(path: str) -> bool:
    """
    Abre uma pasta no explorador de arquivos

    Args:
        path: Caminho da pasta

    Returns:
        True se sucesso, False caso contrário
    """
    try:
        logger.info(f"Abrindo pasta: {path}")
        path_obj = Path(path).resolve()

        if not path_obj.exists():
            logger.error(f"Pasta não existe: {path}")
            return False

        if platform.system() == "Windows":
            os.startfile(str(path_obj))
        elif platform.system() == "Darwin":  # macOS
            subprocess.run(["open", str(path_obj)])
        else:  # Linux
            subprocess.run(["xdg-open", str(path_obj)])

        logger.info(f"Pasta aberta com sucesso: {path}")
        return True

    except Exception as e:
        logger.error(f"Erro ao abrir pasta: {e}", exc_info=True)
        return False


def run_command(cmd: str, shell: bool = True, capture_output: bool = True) -> Dict:
    """
    Executa um comando do sistema

    Args:
        cmd: Comando a executar
        shell: Executar através do shell
        capture_output: Capturar stdout/stderr

    Returns:
        Dict com status, stdout, stderr
    """
    try:
        logger.info(f"Executando comando: {cmd}")

        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=capture_output,
            text=True,
            timeout=30
        )

        output = {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout if capture_output else "",
            "stderr": result.stderr if capture_output else ""
        }

        if output["success"]:
            logger.info(f"Comando executado com sucesso")
        else:
            logger.warning(f"Comando falhou com código {result.returncode}")

        return output

    except subprocess.TimeoutExpired:
        logger.error(f"Comando excedeu timeout de 30s")
        return {"success": False, "error": "Timeout"}
    except Exception as e:
        logger.error(f"Erro ao executar comando: {e}", exc_info=True)
        return {"success": False, "error": str(e)}


def get_system_info() -> Dict:
    """
    Retorna informações do sistema

    Returns:
        Dict com informações do sistema
    """
    try:
        logger.info("Coletando informações do sistema")

        info = {
            "platform": platform.system(),
            "platform_version": platform.version(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "hostname": platform.node()
        }

        logger.info("Informações do sistema coletadas")
        return info

    except Exception as e:
        logger.error(f"Erro ao coletar informações: {e}", exc_info=True)
        return {}


def organize_downloads(downloads_path: str = None) -> Dict:
    """
    Organiza arquivos da pasta Downloads por tipo

    Args:
        downloads_path: Caminho da pasta Downloads (opcional)

    Returns:
        Dict com resultado da organização
    """
    try:
        if downloads_path is None:
            downloads_path = str(Path.home() / "Downloads")

        logger.info(f"Organizando Downloads: {downloads_path}")

        downloads = Path(downloads_path)
        if not downloads.exists():
            logger.error("Pasta Downloads não encontrada")
            return {"success": False, "error": "Downloads folder not found"}

        # Categorias
        categories = {
            "Documentos": [".pdf", ".doc", ".docx", ".txt", ".xlsx", ".xls", ".ppt", ".pptx"],
            "Imagens": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".ico"],
            "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv"],
            "Musicas": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
            "Compactados": [".zip", ".rar", ".7z", ".tar", ".gz"],
            "Executaveis": [".exe", ".msi", ".bat", ".sh"],
            "Codigo": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".json", ".xml"]
        }

        moved_files = []

        for file in downloads.iterdir():
            if file.is_file():
                ext = file.suffix.lower()

                # Encontrar categoria
                category = "Outros"
                for cat, extensions in categories.items():
                    if ext in extensions:
                        category = cat
                        break

                # Criar pasta da categoria
                category_folder = downloads / category
                category_folder.mkdir(exist_ok=True)

                # Mover arquivo
                destination = category_folder / file.name

                # Se arquivo já existe, adicionar número
                counter = 1
                while destination.exists():
                    destination = category_folder / f"{file.stem}_{counter}{file.suffix}"
                    counter += 1

                file.rename(destination)
                moved_files.append(f"{file.name} -> {category}/")

        logger.info(f"Organizados {len(moved_files)} arquivos")
        return {
            "success": True,
            "files_moved": len(moved_files),
            "details": moved_files
        }

    except Exception as e:
        logger.error(f"Erro ao organizar Downloads: {e}", exc_info=True)
        return {"success": False, "error": str(e)}
