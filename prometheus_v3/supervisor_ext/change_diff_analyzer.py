"""
Change Diff Analyzer
Analisa diferenças entre versões de arquivos
"""

import difflib
from pathlib import Path
from typing import Optional, Any
from datetime import datetime
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger("prometheus.diff_analyzer")


@dataclass
class DiffResult:
    """
    Resultado de análise de diferença
    """
    file_path: str
    has_changes: bool
    lines_added: int
    lines_removed: int
    lines_modified: int
    total_changes: int
    diff_text: str
    diff_html: Optional[str] = None
    change_summary: str = ""
    timestamp: str = None
    risk_level: str = "low"  # low, medium, high, critical

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class ChangeDiffAnalyzer:
    """
    Analisador de diferenças entre versões de arquivos

    Funcionalidades:
    - Comparação line-by-line
    - Geração de unified diff
    - Análise de impacto de mudanças
    - Detecção de mudanças de risco
    - Geração de relatórios de mudança
    """

    def __init__(self):
        self.context_lines = 3  # Linhas de contexto no diff
        logger.info("ChangeDiffAnalyzer inicializado")

    def analyze_file_change(
        self,
        original_path: str | Path,
        modified_path: str | Path,
        file_label: Optional[str] = None
    ) -> DiffResult:
        """
        Analisa mudanças entre duas versões de arquivo

        Args:
            original_path: Caminho do arquivo original
            modified_path: Caminho do arquivo modificado
            file_label: Label para identificação

        Returns:
            DiffResult com análise de mudanças
        """
        try:
            original = Path(original_path)
            modified = Path(modified_path)

            if not original.exists():
                return self._create_error_result(
                    str(original_path),
                    "Arquivo original não encontrado"
                )

            if not modified.exists():
                return self._create_error_result(
                    str(modified_path),
                    "Arquivo modificado não encontrado"
                )

            # Ler conteúdo
            original_lines = original.read_text(encoding='utf-8', errors='ignore').splitlines(keepends=True)
            modified_lines = modified.read_text(encoding='utf-8', errors='ignore').splitlines(keepends=True)

            # Gerar diff
            diff_text = self._generate_unified_diff(
                original_lines,
                modified_lines,
                str(original),
                str(modified)
            )

            # Analisar mudanças
            stats = self._analyze_diff_stats(diff_text)

            # Determinar nível de risco
            risk_level = self._assess_risk_level(stats, str(original))

            # Gerar resumo
            summary = self._generate_change_summary(stats, str(original))

            result = DiffResult(
                file_path=file_label or str(modified),
                has_changes=stats['has_changes'],
                lines_added=stats['lines_added'],
                lines_removed=stats['lines_removed'],
                lines_modified=stats['lines_modified'],
                total_changes=stats['total_changes'],
                diff_text=diff_text,
                change_summary=summary,
                risk_level=risk_level
            )

            logger.info(
                f"Diff analisado: {result.file_path} "
                f"(+{result.lines_added}/-{result.lines_removed}, risk={risk_level})"
            )

            return result

        except Exception as e:
            logger.error(f"Erro ao analisar diff: {e}")
            return self._create_error_result(str(original_path), str(e))

    def analyze_content_change(
        self,
        original_content: str,
        modified_content: str,
        file_path: str = "unknown"
    ) -> DiffResult:
        """
        Analisa mudanças entre dois conteúdos em memória

        Args:
            original_content: Conteúdo original
            modified_content: Conteúdo modificado
            file_path: Path para identificação

        Returns:
            DiffResult com análise
        """
        try:
            original_lines = original_content.splitlines(keepends=True)
            modified_lines = modified_content.splitlines(keepends=True)

            diff_text = self._generate_unified_diff(
                original_lines,
                modified_lines,
                f"{file_path} (original)",
                f"{file_path} (modified)"
            )

            stats = self._analyze_diff_stats(diff_text)
            risk_level = self._assess_risk_level(stats, file_path)
            summary = self._generate_change_summary(stats, file_path)

            return DiffResult(
                file_path=file_path,
                has_changes=stats['has_changes'],
                lines_added=stats['lines_added'],
                lines_removed=stats['lines_removed'],
                lines_modified=stats['lines_modified'],
                total_changes=stats['total_changes'],
                diff_text=diff_text,
                change_summary=summary,
                risk_level=risk_level
            )

        except Exception as e:
            logger.error(f"Erro ao analisar diff de conteúdo: {e}")
            return self._create_error_result(file_path, str(e))

    def _generate_unified_diff(
        self,
        original_lines: list[str],
        modified_lines: list[str],
        original_label: str,
        modified_label: str
    ) -> str:
        """
        Gera unified diff entre duas versões

        Args:
            original_lines: Linhas do original
            modified_lines: Linhas do modificado
            original_label: Label do original
            modified_label: Label do modificado

        Returns:
            Texto do diff
        """
        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=original_label,
            tofile=modified_label,
            lineterm='',
            n=self.context_lines
        )

        return '\n'.join(diff)

    def _analyze_diff_stats(self, diff_text: str) -> dict[str, Any]:
        """
        Analisa estatísticas do diff

        Args:
            diff_text: Texto do diff

        Returns:
            Dict com estatísticas
        """
        lines = diff_text.split('\n')

        added = 0
        removed = 0

        for line in lines:
            if line.startswith('+') and not line.startswith('+++'):
                added += 1
            elif line.startswith('-') and not line.startswith('---'):
                removed += 1

        # Modificações são consideradas quando há adição e remoção
        modified = min(added, removed)

        return {
            'has_changes': added > 0 or removed > 0,
            'lines_added': added,
            'lines_removed': removed,
            'lines_modified': modified,
            'total_changes': added + removed
        }

    def _assess_risk_level(self, stats: dict, file_path: str) -> str:
        """
        Avalia nível de risco da mudança

        Args:
            stats: Estatísticas do diff
            file_path: Caminho do arquivo

        Returns:
            Nível de risco (low, medium, high, critical)
        """
        total_changes = stats['total_changes']

        # Arquivos críticos
        critical_files = ['prometheus.yaml', '.env', 'main.py', '__init__.py']
        is_critical_file = any(cf in file_path for cf in critical_files)

        # Arquivos de código
        is_code = file_path.endswith(('.py', '.js', '.ts', '.tsx'))

        # Lógica de risco
        if is_critical_file and total_changes > 10:
            return "critical"
        elif is_critical_file and total_changes > 0:
            return "high"
        elif is_code and total_changes > 100:
            return "high"
        elif is_code and total_changes > 50:
            return "medium"
        elif total_changes > 20:
            return "medium"
        else:
            return "low"

    def _generate_change_summary(self, stats: dict, file_path: str) -> str:
        """
        Gera resumo legível das mudanças

        Args:
            stats: Estatísticas do diff
            file_path: Caminho do arquivo

        Returns:
            String com resumo
        """
        if not stats['has_changes']:
            return "Nenhuma mudança detectada"

        parts = []

        if stats['lines_added'] > 0:
            parts.append(f"{stats['lines_added']} linhas adicionadas")

        if stats['lines_removed'] > 0:
            parts.append(f"{stats['lines_removed']} linhas removidas")

        if stats['lines_modified'] > 0:
            parts.append(f"{stats['lines_modified']} linhas modificadas")

        summary = ", ".join(parts)

        file_name = Path(file_path).name
        return f"{file_name}: {summary}"

    def _create_error_result(self, file_path: str, error: str) -> DiffResult:
        """
        Cria DiffResult de erro

        Args:
            file_path: Caminho do arquivo
            error: Mensagem de erro

        Returns:
            DiffResult com erro
        """
        return DiffResult(
            file_path=file_path,
            has_changes=False,
            lines_added=0,
            lines_removed=0,
            lines_modified=0,
            total_changes=0,
            diff_text=f"ERRO: {error}",
            change_summary=f"Erro ao analisar: {error}",
            risk_level="unknown"
        )

    def compare_with_backup(
        self,
        current_file: str | Path,
        backup_file: str | Path
    ) -> DiffResult:
        """
        Compara arquivo atual com backup

        Args:
            current_file: Arquivo atual
            backup_file: Arquivo de backup

        Returns:
            DiffResult
        """
        return self.analyze_file_change(
            original_path=backup_file,
            modified_path=current_file,
            file_label=str(current_file)
        )

    def generate_html_diff(self, diff_result: DiffResult) -> str:
        """
        Gera visualização HTML do diff

        Args:
            diff_result: Resultado do diff

        Returns:
            HTML do diff
        """
        try:
            # Parse diff text
            lines = diff_result.diff_text.split('\n')

            html_parts = ['<div class="diff-viewer">']

            for line in lines:
                if line.startswith('+++') or line.startswith('---'):
                    html_parts.append(f'<div class="diff-header">{line}</div>')
                elif line.startswith('+'):
                    html_parts.append(f'<div class="diff-added">{line}</div>')
                elif line.startswith('-'):
                    html_parts.append(f'<div class="diff-removed">{line}</div>')
                elif line.startswith('@@'):
                    html_parts.append(f'<div class="diff-hunk">{line}</div>')
                else:
                    html_parts.append(f'<div class="diff-context">{line}</div>')

            html_parts.append('</div>')

            return '\n'.join(html_parts)

        except Exception as e:
            logger.error(f"Erro ao gerar HTML diff: {e}")
            return f"<pre>{diff_result.diff_text}</pre>"
