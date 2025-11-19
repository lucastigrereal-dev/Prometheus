"""
File Mutation Checker
Sistema de detecção de mutações em arquivos
"""

import json
from pathlib import Path
from typing import Optional, Any, Callable
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger("prometheus.mutation_checker")


@dataclass
class MutationEvent:
    """
    Evento de mutação de arquivo
    """
    timestamp: str
    file_path: str
    mutation_type: str  # created, modified, deleted, renamed
    old_hash: Optional[str] = None
    new_hash: Optional[str] = None
    detected_by: str = "mutation_checker"
    authorized: bool = False
    metadata: dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class FileMutationChecker:
    """
    Detector de mutações em arquivos

    Funcionalidades:
    - Verificação sob demanda (não real-time)
    - Comparação de estado vs índice
    - Detecção de criação/modificação/deleção
    - Registro de eventos de mutação
    - Callback para notificações
    """

    def __init__(
        self,
        integrity_service: Any,
        mutation_log_path: str | Path = "runtime/mutations.log",
        on_mutation: Optional[Callable] = None
    ):
        self.integrity_service = integrity_service
        self.mutation_log_path = Path(mutation_log_path)
        self.mutation_log_path.parent.mkdir(parents=True, exist_ok=True)
        self.on_mutation = on_mutation
        logger.info("FileMutationChecker inicializado")

    def check_for_mutations(self) -> list[MutationEvent]:
        """
        Verifica todos os arquivos indexados por mutações

        Returns:
            Lista de MutationEvent detectados
        """
        logger.info("Iniciando verificação de mutações...")

        mutations = []

        # Verificar todos os arquivos indexados
        all_files = self.integrity_service.index.list_files()

        for record in all_files:
            try:
                path = Path(record.path)

                # Verificar se arquivo foi deletado
                if not path.exists():
                    if record.status != "deleted":
                        event = self._create_mutation_event(
                            file_path=record.path,
                            mutation_type="deleted",
                            old_hash=record.hash,
                            new_hash=None
                        )
                        mutations.append(event)
                        self._log_mutation(event)
                    continue

                # Calcular hash atual
                current_hash = self.integrity_service.hasher.hash_file(path)

                if current_hash is None:
                    continue

                # Comparar hashes
                if current_hash != record.hash:
                    event = self._create_mutation_event(
                        file_path=record.path,
                        mutation_type="modified",
                        old_hash=record.hash,
                        new_hash=current_hash
                    )
                    mutations.append(event)
                    self._log_mutation(event)

            except Exception as e:
                logger.error(f"Erro ao verificar {record.path}: {e}")

        # Detectar arquivos novos (não indexados)
        new_files = self._detect_new_files()
        for new_file in new_files:
            event = self._create_mutation_event(
                file_path=new_file,
                mutation_type="created",
                old_hash=None,
                new_hash=self.integrity_service.hasher.hash_file(new_file)
            )
            mutations.append(event)
            self._log_mutation(event)

        if mutations:
            logger.warning(f"{len(mutations)} mutações detectadas")

            # Chamar callback se configurado
            if self.on_mutation:
                try:
                    self.on_mutation(mutations)
                except Exception as e:
                    logger.error(f"Erro no callback de mutação: {e}")
        else:
            logger.info("Nenhuma mutação detectada")

        return mutations

    def check_file(self, file_path: str | Path) -> Optional[MutationEvent]:
        """
        Verifica mutação em arquivo específico

        Args:
            file_path: Caminho do arquivo

        Returns:
            MutationEvent se houver mutação, None caso contrário
        """
        path_str = str(file_path)
        record = self.integrity_service.index.get_file(path_str)

        if not record:
            # Arquivo não indexado
            if Path(file_path).exists():
                return self._create_mutation_event(
                    file_path=path_str,
                    mutation_type="created",
                    new_hash=self.integrity_service.hasher.hash_file(file_path)
                )
            return None

        path = Path(file_path)

        # Verificar deleção
        if not path.exists():
            return self._create_mutation_event(
                file_path=path_str,
                mutation_type="deleted",
                old_hash=record.hash
            )

        # Verificar modificação
        current_hash = self.integrity_service.hasher.hash_file(path)

        if current_hash != record.hash:
            return self._create_mutation_event(
                file_path=path_str,
                mutation_type="modified",
                old_hash=record.hash,
                new_hash=current_hash
            )

        return None

    def _create_mutation_event(
        self,
        file_path: str,
        mutation_type: str,
        old_hash: Optional[str] = None,
        new_hash: Optional[str] = None
    ) -> MutationEvent:
        """
        Cria evento de mutação

        Args:
            file_path: Caminho do arquivo
            mutation_type: Tipo de mutação
            old_hash: Hash antigo
            new_hash: Hash novo

        Returns:
            MutationEvent
        """
        return MutationEvent(
            timestamp=datetime.now().isoformat(),
            file_path=file_path,
            mutation_type=mutation_type,
            old_hash=old_hash,
            new_hash=new_hash,
            authorized=False
        )

    def _log_mutation(self, event: MutationEvent):
        """
        Registra evento de mutação no log

        Args:
            event: MutationEvent
        """
        try:
            with open(self.mutation_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(event.to_dict()) + '\n')

            logger.warning(f"Mutação registrada: {event.mutation_type} - {event.file_path}")

        except Exception as e:
            logger.error(f"Erro ao registrar mutação: {e}")

    def _detect_new_files(self) -> list[str]:
        """
        Detecta arquivos novos (não indexados)

        Returns:
            Lista de caminhos de arquivos novos
        """
        # Por enquanto, retorna lista vazia
        # Implementação futura: escanear diretórios monitorados
        return []

    def get_recent_mutations(self, limit: int = 100) -> list[MutationEvent]:
        """
        Busca mutações recentes

        Args:
            limit: Número máximo de eventos

        Returns:
            Lista de MutationEvent
        """
        try:
            if not self.mutation_log_path.exists():
                return []

            events = []

            with open(self.mutation_log_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        event_data = json.loads(line.strip())
                        event = MutationEvent(**event_data)
                        events.append(event)
                    except:
                        continue

            return events[-limit:][::-1]

        except Exception as e:
            logger.error(f"Erro ao buscar mutações: {e}")
            return []

    def get_mutations_for_file(self, file_path: str) -> list[MutationEvent]:
        """
        Busca mutações de arquivo específico

        Args:
            file_path: Caminho do arquivo

        Returns:
            Lista de MutationEvent do arquivo
        """
        all_mutations = self.get_recent_mutations(limit=1000)
        return [m for m in all_mutations if m.file_path == file_path]

    def authorize_mutation(self, file_path: str) -> bool:
        """
        Autoriza mutação de arquivo (atualiza índice)

        Args:
            file_path: Caminho do arquivo

        Returns:
            True se autorizado com sucesso
        """
        try:
            success = self.integrity_service.approve_modification(file_path)

            if success:
                logger.info(f"Mutação autorizada: {file_path}")

            return success

        except Exception as e:
            logger.error(f"Erro ao autorizar mutação: {e}")
            return False

    def get_unauthorized_mutations(self) -> list[MutationEvent]:
        """
        Lista mutações não autorizadas

        Returns:
            Lista de MutationEvent não autorizados
        """
        recent = self.get_recent_mutations(limit=1000)
        return [m for m in recent if not m.authorized]
