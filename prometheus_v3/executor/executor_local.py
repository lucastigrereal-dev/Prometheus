"""
Local Executor - Executa ações seguras no sistema local
PRINCÍPIOS:
- Apenas ações seguras e auditadas
- Tudo é logado
- Nenhuma ação destrutiva sem confirmação
- Sempre com fallback
"""

import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import subprocess
import json

class LocalExecutor:
    """Executor de ações locais seguras"""

    SAFE_ACTIONS = [
        'list_files',
        'organize_downloads',
        'get_system_info',
        'read_file_info',
        'create_directory'
    ]

    def __init__(self):
        self.execution_history = []

    def execute(self, action: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executa uma ação local de forma segura

        Args:
            action: Nome da ação a executar
            params: Parâmetros da ação

        Returns:
            Dict com resultado da execução
        """
        # Validar ação
        if action not in self.SAFE_ACTIONS:
            return {
                'success': False,
                'error': f'Ação "{action}" não está na lista de ações seguras',
                'safe_actions': self.SAFE_ACTIONS
            }

        # Log de início
        execution_id = f"exec_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.now()

        try:
            # Executar ação
            method = getattr(self, f'_action_{action}')
            result = method(params)

            # Log de sucesso
            execution_record = {
                'id': execution_id,
                'action': action,
                'params': params,
                'result': result,
                'success': True,
                'start_time': start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_ms': int((datetime.now() - start_time).total_seconds() * 1000)
            }

            self.execution_history.append(execution_record)

            return {
                'success': True,
                'execution_id': execution_id,
                'data': result,
                'duration_ms': execution_record['duration_ms']
            }

        except Exception as e:
            # Log de erro
            execution_record = {
                'id': execution_id,
                'action': action,
                'params': params,
                'success': False,
                'error': str(e),
                'start_time': start_time.isoformat(),
                'end_time': datetime.now().isoformat()
            }

            self.execution_history.append(execution_record)

            return {
                'success': False,
                'execution_id': execution_id,
                'error': str(e)
            }

    # ==================== AÇÕES SEGURAS ====================

    def _action_list_files(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Lista arquivos em um diretório (limitado a 100 arquivos)"""
        path = params.get('path', '.')
        max_files = min(params.get('max_files', 100), 1000)  # limite de segurança

        path_obj = Path(path).resolve()

        if not path_obj.exists():
            raise FileNotFoundError(f'Caminho não existe: {path}')

        if not path_obj.is_dir():
            raise ValueError(f'Caminho não é um diretório: {path}')

        files = []
        for item in list(path_obj.iterdir())[:max_files]:
            try:
                stat = item.stat()
                files.append({
                    'name': item.name,
                    'path': str(item),
                    'is_file': item.is_file(),
                    'is_dir': item.is_dir(),
                    'size': stat.st_size if item.is_file() else None,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except Exception as e:
                # Ignorar arquivos com erro de permissão
                continue

        return {
            'path': str(path_obj),
            'total_files': len(files),
            'files': files
        }

    def _action_organize_downloads(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Organiza a pasta Downloads em subpastas por tipo"""
        downloads_path = Path.home() / 'Downloads'
        dry_run = params.get('dry_run', True)  # Por padrão, apenas simula

        if not downloads_path.exists():
            raise FileNotFoundError('Pasta Downloads não encontrada')

        # Categorias de arquivos
        categories = {
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp'],
            'documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
            'spreadsheets': ['.xls', '.xlsx', '.csv', '.ods'],
            'videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv'],
            'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a'],
            'archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
            'code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.json'],
        }

        changes = []

        for file in downloads_path.iterdir():
            if file.is_file():
                ext = file.suffix.lower()

                # Encontrar categoria
                category = None
                for cat, extensions in categories.items():
                    if ext in extensions:
                        category = cat
                        break

                if category:
                    target_dir = downloads_path / category
                    target_path = target_dir / file.name

                    change = {
                        'file': file.name,
                        'from': str(file),
                        'to': str(target_path),
                        'category': category
                    }

                    if not dry_run:
                        # Criar diretório se não existir
                        target_dir.mkdir(exist_ok=True)

                        # Mover arquivo
                        shutil.move(str(file), str(target_path))
                        change['moved'] = True
                    else:
                        change['moved'] = False
                        change['dry_run'] = True

                    changes.append(change)

        return {
            'dry_run': dry_run,
            'total_changes': len(changes),
            'changes': changes,
            'message': 'Simulação concluída. Use dry_run=false para executar.' if dry_run else 'Organização concluída!'
        }

    def _action_get_system_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Retorna informações do sistema"""
        import platform
        import psutil

        return {
            'platform': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'processor': platform.processor(),
            'python_version': platform.python_version(),
            'cpu_count': psutil.cpu_count(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory': {
                'total': psutil.virtual_memory().total,
                'available': psutil.virtual_memory().available,
                'percent': psutil.virtual_memory().percent
            },
            'disk': {
                'total': psutil.disk_usage('/').total,
                'used': psutil.disk_usage('/').used,
                'free': psutil.disk_usage('/').free,
                'percent': psutil.disk_usage('/').percent
            }
        }

    def _action_read_file_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Lê informações sobre um arquivo (sem ler conteúdo)"""
        path = params.get('path')

        if not path:
            raise ValueError('Parâmetro "path" é obrigatório')

        path_obj = Path(path).resolve()

        if not path_obj.exists():
            raise FileNotFoundError(f'Arquivo não existe: {path}')

        stat = path_obj.stat()

        return {
            'name': path_obj.name,
            'path': str(path_obj),
            'size': stat.st_size,
            'is_file': path_obj.is_file(),
            'is_dir': path_obj.is_dir(),
            'extension': path_obj.suffix,
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'accessed': datetime.fromtimestamp(stat.st_atime).isoformat()
        }

    def _action_create_directory(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Cria um diretório (com confirmação)"""
        path = params.get('path')

        if not path:
            raise ValueError('Parâmetro "path" é obrigatório')

        path_obj = Path(path).resolve()

        # Validação de segurança: não permitir criação fora de certos diretórios
        allowed_base = Path.home()
        if not str(path_obj).startswith(str(allowed_base)):
            raise PermissionError(f'Criação de diretório permitida apenas dentro de: {allowed_base}')

        if path_obj.exists():
            return {
                'created': False,
                'message': 'Diretório já existe',
                'path': str(path_obj)
            }

        path_obj.mkdir(parents=True, exist_ok=True)

        return {
            'created': True,
            'path': str(path_obj),
            'message': 'Diretório criado com sucesso'
        }

    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retorna histórico de execuções"""
        return self.execution_history[-limit:]

    def get_available_actions(self) -> List[Dict[str, str]]:
        """Retorna lista de ações disponíveis com descrição"""
        return [
            {
                'action': 'list_files',
                'description': 'Lista arquivos em um diretório',
                'params': {'path': 'string', 'max_files': 'int (opcional)'}
            },
            {
                'action': 'organize_downloads',
                'description': 'Organiza Downloads por tipo de arquivo',
                'params': {'dry_run': 'bool (default: true)'}
            },
            {
                'action': 'get_system_info',
                'description': 'Retorna informações do sistema',
                'params': {}
            },
            {
                'action': 'read_file_info',
                'description': 'Lê metadados de um arquivo',
                'params': {'path': 'string'}
            },
            {
                'action': 'create_directory',
                'description': 'Cria um novo diretório',
                'params': {'path': 'string'}
            }
        ]
