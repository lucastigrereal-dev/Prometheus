# -*- coding: utf-8 -*-
"""
CHECKPOINT MANAGER - Sistema de Checkpoints e Rollback

Permite criar snapshots do sistema antes de operações críticas
e fazer rollback se algo falhar
"""

import asyncio
import logging
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import uuid

logger = logging.getLogger(__name__)


@dataclass
class Checkpoint:
    """Snapshot do sistema em um ponto específico"""
    id: str
    timestamp: datetime
    description: str
    files_backed_up: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    backup_path: Optional[Path] = None


class CheckpointManager:
    """
    Gerencia checkpoints e rollback

    Funcionalidades:
    - Criar checkpoints automáticos
    - Backup de arquivos modificados
    - Rollback para checkpoint anterior
    - Limpeza de checkpoints antigos
    """

    def __init__(self, checkpoints_dir: Path = None, max_checkpoints: int = 10):
        """
        Args:
            checkpoints_dir: Diretório para armazenar checkpoints
            max_checkpoints: Número máximo de checkpoints a manter
        """
        if checkpoints_dir is None:
            checkpoints_dir = Path(__file__).parent.parent.parent / 'data' / 'checkpoints'

        self.checkpoints_dir = Path(checkpoints_dir)
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)

        self.max_checkpoints = max_checkpoints
        self.checkpoints: List[Checkpoint] = []

        # Carrega checkpoints existentes
        self._load_checkpoints()

        logger.info(f"CheckpointManager initialized: {len(self.checkpoints)} checkpoints loaded")

    def _load_checkpoints(self):
        """Carrega checkpoints salvos"""
        manifest_file = self.checkpoints_dir / 'manifest.json'

        if not manifest_file.exists():
            return

        try:
            with open(manifest_file, 'r') as f:
                data = json.load(f)

            for cp_data in data:
                checkpoint = Checkpoint(
                    id=cp_data['id'],
                    timestamp=datetime.fromisoformat(cp_data['timestamp']),
                    description=cp_data['description'],
                    files_backed_up=cp_data.get('files_backed_up', []),
                    metadata=cp_data.get('metadata', {}),
                    backup_path=Path(cp_data['backup_path']) if cp_data.get('backup_path') else None
                )
                self.checkpoints.append(checkpoint)

        except Exception as e:
            logger.error(f"Error loading checkpoints: {e}")

    def _save_manifest(self):
        """Salva manifest de checkpoints"""
        manifest_file = self.checkpoints_dir / 'manifest.json'

        try:
            data = []
            for cp in self.checkpoints:
                data.append({
                    'id': cp.id,
                    'timestamp': cp.timestamp.isoformat(),
                    'description': cp.description,
                    'files_backed_up': cp.files_backed_up,
                    'metadata': cp.metadata,
                    'backup_path': str(cp.backup_path) if cp.backup_path else None
                })

            with open(manifest_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            logger.error(f"Error saving manifest: {e}")

    async def create_checkpoint(
        self,
        description: str = "Auto checkpoint",
        files_to_backup: List[Path] = None
    ) -> Checkpoint:
        """
        Cria um checkpoint

        Args:
            description: Descrição do checkpoint
            files_to_backup: Lista de arquivos para fazer backup

        Returns:
            Checkpoint criado
        """
        checkpoint_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now()

        logger.info(f"Creating checkpoint: {checkpoint_id} - {description}")

        # Cria diretório de backup
        backup_dir = self.checkpoints_dir / checkpoint_id
        backup_dir.mkdir(exist_ok=True)

        # Backup de arquivos
        backed_up_files = []

        if files_to_backup:
            for file_path in files_to_backup:
                try:
                    file_path = Path(file_path)

                    if file_path.exists():
                        # Preserva estrutura de diretórios
                        relative_path = file_path.name
                        backup_file = backup_dir / relative_path

                        shutil.copy2(file_path, backup_file)
                        backed_up_files.append(str(file_path))

                        logger.debug(f"Backed up: {file_path}")

                except Exception as e:
                    logger.error(f"Error backing up {file_path}: {e}")

        # Cria checkpoint
        checkpoint = Checkpoint(
            id=checkpoint_id,
            timestamp=timestamp,
            description=description,
            files_backed_up=backed_up_files,
            backup_path=backup_dir
        )

        # Adiciona à lista
        self.checkpoints.append(checkpoint)

        # Salva manifest
        self._save_manifest()

        # Limpa checkpoints antigos se necessário
        await self._cleanup_old_checkpoints()

        logger.info(f"Checkpoint created: {checkpoint_id} ({len(backed_up_files)} files)")

        return checkpoint

    async def rollback_to(self, checkpoint: Checkpoint) -> bool:
        """
        Faz rollback para um checkpoint

        Args:
            checkpoint: Checkpoint para restaurar

        Returns:
            True se sucesso
        """
        logger.info(f"Rolling back to checkpoint: {checkpoint.id}")

        try:
            if not checkpoint.backup_path or not checkpoint.backup_path.exists():
                logger.error(f"Backup path not found: {checkpoint.backup_path}")
                return False

            # Restaura arquivos
            restored = 0

            for file_path_str in checkpoint.files_backed_up:
                try:
                    original_path = Path(file_path_str)
                    backup_file = checkpoint.backup_path / original_path.name

                    if backup_file.exists():
                        shutil.copy2(backup_file, original_path)
                        restored += 1
                        logger.debug(f"Restored: {original_path}")

                except Exception as e:
                    logger.error(f"Error restoring {file_path_str}: {e}")

            logger.info(f"Rollback complete: {restored}/{len(checkpoint.files_backed_up)} files restored")

            return restored > 0

        except Exception as e:
            logger.error(f"Error during rollback: {e}")
            return False

    async def rollback_all(self, checkpoints: List[Checkpoint]) -> bool:
        """
        Faz rollback de múltiplos checkpoints (do mais recente para o mais antigo)

        Args:
            checkpoints: Lista de checkpoints

        Returns:
            True se todos foram bem-sucedidos
        """
        logger.info(f"Rolling back {len(checkpoints)} checkpoints...")

        # Ordena do mais recente para mais antigo
        sorted_checkpoints = sorted(checkpoints, key=lambda cp: cp.timestamp, reverse=True)

        all_success = True

        for checkpoint in sorted_checkpoints:
            success = await self.rollback_to(checkpoint)
            if not success:
                all_success = False

        return all_success

    async def cleanup_checkpoints(self, checkpoints: List[Checkpoint]):
        """
        Remove checkpoints específicos

        Args:
            checkpoints: Lista de checkpoints para remover
        """
        for checkpoint in checkpoints:
            try:
                # Remove diretório de backup
                if checkpoint.backup_path and checkpoint.backup_path.exists():
                    shutil.rmtree(checkpoint.backup_path)

                # Remove da lista
                if checkpoint in self.checkpoints:
                    self.checkpoints.remove(checkpoint)

                logger.debug(f"Cleaned up checkpoint: {checkpoint.id}")

            except Exception as e:
                logger.error(f"Error cleaning up checkpoint {checkpoint.id}: {e}")

        # Salva manifest atualizado
        self._save_manifest()

    async def _cleanup_old_checkpoints(self):
        """Remove checkpoints antigos se exceder max_checkpoints"""
        if len(self.checkpoints) <= self.max_checkpoints:
            return

        # Ordena por timestamp (mais antigo primeiro)
        sorted_checkpoints = sorted(self.checkpoints, key=lambda cp: cp.timestamp)

        # Calcula quantos remover
        to_remove = len(self.checkpoints) - self.max_checkpoints

        # Remove os mais antigos
        for checkpoint in sorted_checkpoints[:to_remove]:
            await self.cleanup_checkpoints([checkpoint])

        logger.info(f"Cleaned up {to_remove} old checkpoints")

    def get_checkpoints(self) -> List[Checkpoint]:
        """Retorna lista de checkpoints (mais recente primeiro)"""
        return sorted(self.checkpoints, key=lambda cp: cp.timestamp, reverse=True)

    def get_checkpoint_by_id(self, checkpoint_id: str) -> Optional[Checkpoint]:
        """Busca checkpoint por ID"""
        for checkpoint in self.checkpoints:
            if checkpoint.id == checkpoint_id:
                return checkpoint
        return None

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas"""
        if not self.checkpoints:
            return {
                'total_checkpoints': 0,
                'oldest': None,
                'newest': None,
                'total_files_backed_up': 0
            }

        sorted_checkpoints = sorted(self.checkpoints, key=lambda cp: cp.timestamp)

        return {
            'total_checkpoints': len(self.checkpoints),
            'oldest': sorted_checkpoints[0].timestamp.isoformat(),
            'newest': sorted_checkpoints[-1].timestamp.isoformat(),
            'total_files_backed_up': sum(len(cp.files_backed_up) for cp in self.checkpoints)
        }
