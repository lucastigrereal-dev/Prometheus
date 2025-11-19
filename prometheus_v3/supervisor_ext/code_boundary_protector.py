"""
Code Boundary Protector
Protetor de limites de código - impede alterações não autorizadas
"""

import re
import ast
from pathlib import Path
from typing import Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

logger = logging.getLogger("prometheus.boundary_protector")


@dataclass
class BoundaryViolation:
    """
    Violação de limite de código
    """
    file_path: str
    violation_type: str  # protected_zone, forbidden_pattern, syntax_error, import_violation
    severity: str  # warning, error, critical
    line_number: Optional[int] = None
    description: str = ""
    code_snippet: Optional[str] = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class CodeBoundaryProtector:
    """
    Protetor de limites de código

    Funcionalidades:
    - Detecção de zonas protegidas
    - Validação de sintaxe Python
    - Detecção de padrões proibidos
    - Verificação de imports
    - Análise AST básica
    """

    def __init__(self):
        self.protected_zones = self._init_protected_zones()
        self.forbidden_patterns = self._init_forbidden_patterns()
        self.forbidden_imports = self._init_forbidden_imports()
        logger.info("CodeBoundaryProtector inicializado")

    def _init_protected_zones(self) -> dict[str, list[str]]:
        """
        Inicializa zonas protegidas por tipo de arquivo

        Returns:
            Dict de zonas protegidas
        """
        return {
            "python": [
                r"# PROTECTED ZONE START",
                r"# DO NOT MODIFY",
                r"# CRITICAL SECTION",
            ],
            "config": [
                r"# PROTECTED CONFIG",
                r"# SYSTEM CRITICAL",
            ]
        }

    def _init_forbidden_patterns(self) -> list[dict[str, str]]:
        """
        Inicializa padrões de código proibidos

        Returns:
            Lista de padrões proibidos
        """
        return [
            {
                "pattern": r"eval\s*\(",
                "description": "Uso de eval() é proibido por segurança",
                "severity": "critical"
            },
            {
                "pattern": r"exec\s*\(",
                "description": "Uso de exec() é proibido por segurança",
                "severity": "critical"
            },
            {
                "pattern": r"__import__\s*\(",
                "description": "Uso de __import__ direto não é recomendado",
                "severity": "warning"
            },
            {
                "pattern": r"os\.system\s*\(",
                "description": "Uso de os.system() é inseguro",
                "severity": "error"
            },
        ]

    def _init_forbidden_imports(self) -> list[str]:
        """
        Inicializa lista de imports proibidos

        Returns:
            Lista de módulos proibidos
        """
        return [
            # Adicionar imports específicos se necessário
            # Exemplo: "telnetlib", "ftplib"
        ]

    def validate_file(self, file_path: str | Path) -> list[BoundaryViolation]:
        """
        Valida arquivo completo

        Args:
            file_path: Caminho do arquivo

        Returns:
            Lista de violações encontradas
        """
        violations = []
        path = Path(file_path)

        if not path.exists():
            return [BoundaryViolation(
                file_path=str(path),
                violation_type="file_not_found",
                severity="error",
                description="Arquivo não encontrado"
            )]

        try:
            content = path.read_text(encoding='utf-8', errors='ignore')

            # Validar sintaxe Python
            if path.suffix == '.py':
                syntax_violations = self._validate_python_syntax(content, str(path))
                violations.extend(syntax_violations)

                # Se há erros de sintaxe, não continuar outras validações
                if syntax_violations:
                    return violations

                # Validar imports
                import_violations = self._validate_imports(content, str(path))
                violations.extend(import_violations)

            # Validar padrões proibidos
            pattern_violations = self._validate_forbidden_patterns(content, str(path))
            violations.extend(pattern_violations)

            # Validar zonas protegidas
            zone_violations = self._validate_protected_zones(content, str(path))
            violations.extend(zone_violations)

            if violations:
                logger.warning(f"{len(violations)} violações encontradas em {path}")
            else:
                logger.info(f"Arquivo validado com sucesso: {path}")

            return violations

        except Exception as e:
            logger.error(f"Erro ao validar arquivo: {e}")
            return [BoundaryViolation(
                file_path=str(path),
                violation_type="validation_error",
                severity="error",
                description=str(e)
            )]

    def validate_content(self, content: str, file_type: str = "python") -> list[BoundaryViolation]:
        """
        Valida conteúdo em memória

        Args:
            content: Conteúdo a validar
            file_type: Tipo de arquivo (python, config)

        Returns:
            Lista de violações
        """
        violations = []

        if file_type == "python":
            violations.extend(self._validate_python_syntax(content, "content"))
            violations.extend(self._validate_imports(content, "content"))

        violations.extend(self._validate_forbidden_patterns(content, "content"))
        violations.extend(self._validate_protected_zones(content, "content"))

        return violations

    def _validate_python_syntax(self, content: str, file_path: str) -> list[BoundaryViolation]:
        """
        Valida sintaxe Python usando AST

        Args:
            content: Conteúdo Python
            file_path: Path para identificação

        Returns:
            Lista de violações de sintaxe
        """
        violations = []

        try:
            ast.parse(content)
        except SyntaxError as e:
            violations.append(BoundaryViolation(
                file_path=file_path,
                violation_type="syntax_error",
                severity="critical",
                line_number=e.lineno,
                description=f"Erro de sintaxe: {e.msg}",
                code_snippet=e.text
            ))
        except Exception as e:
            violations.append(BoundaryViolation(
                file_path=file_path,
                violation_type="parse_error",
                severity="error",
                description=f"Erro ao fazer parse: {str(e)}"
            ))

        return violations

    def _validate_imports(self, content: str, file_path: str) -> list[BoundaryViolation]:
        """
        Valida imports do código

        Args:
            content: Conteúdo Python
            file_path: Path para identificação

        Returns:
            Lista de violações de import
        """
        violations = []

        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in self.forbidden_imports:
                            violations.append(BoundaryViolation(
                                file_path=file_path,
                                violation_type="import_violation",
                                severity="error",
                                line_number=node.lineno,
                                description=f"Import proibido: {alias.name}"
                            ))

                elif isinstance(node, ast.ImportFrom):
                    if node.module in self.forbidden_imports:
                        violations.append(BoundaryViolation(
                            file_path=file_path,
                            violation_type="import_violation",
                            severity="error",
                            line_number=node.lineno,
                            description=f"Import proibido: {node.module}"
                        ))

        except Exception as e:
            logger.error(f"Erro ao validar imports: {e}")

        return violations

    def _validate_forbidden_patterns(self, content: str, file_path: str) -> list[BoundaryViolation]:
        """
        Valida padrões de código proibidos

        Args:
            content: Conteúdo
            file_path: Path para identificação

        Returns:
            Lista de violações de padrão
        """
        violations = []
        lines = content.split('\n')

        for pattern_def in self.forbidden_patterns:
            pattern = pattern_def["pattern"]

            for line_num, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    violations.append(BoundaryViolation(
                        file_path=file_path,
                        violation_type="forbidden_pattern",
                        severity=pattern_def["severity"],
                        line_number=line_num,
                        description=pattern_def["description"],
                        code_snippet=line.strip()
                    ))

        return violations

    def _validate_protected_zones(self, content: str, file_path: str) -> list[BoundaryViolation]:
        """
        Valida se zonas protegidas foram modificadas

        Args:
            content: Conteúdo
            file_path: Path para identificação

        Returns:
            Lista de violações de zona protegida
        """
        # Por enquanto, apenas detecta presença de marcadores
        # Implementação futura: comparar com versão original
        violations = []

        # Esta é uma validação básica
        # A lógica completa requer comparação com estado anterior

        return violations

    def is_safe_to_modify(self, file_path: str | Path) -> tuple[bool, list[BoundaryViolation]]:
        """
        Verifica se é seguro modificar arquivo

        Args:
            file_path: Caminho do arquivo

        Returns:
            Tupla (is_safe, violations)
        """
        violations = self.validate_file(file_path)

        # Considerar crítico se houver violações críticas
        has_critical = any(v.severity == "critical" for v in violations)

        is_safe = not has_critical

        return is_safe, violations
