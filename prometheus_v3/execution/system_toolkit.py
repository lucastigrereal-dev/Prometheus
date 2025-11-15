# -*- coding: utf-8 -*-
"""
SYSTEM TOOLKIT - Execução Segura de Comandos de Sistema

Camadas de Segurança:
1. Whitelist de comandos seguros
2. Blacklist de padrões perigosos
3. Sandbox path (isolamento)
4. Confirmação do usuário para comandos críticos
"""

import asyncio
import logging
import subprocess
import shlex
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    """Resultado de execução de comando"""
    success: bool
    output: str
    error: str = ""
    exit_code: int = 0
    duration: float = 0.0


class SecurityError(Exception):
    """Erro de segurança"""
    pass


class SystemToolkit:
    """
    Toolkit para execução segura de comandos de sistema

    Segurança através de:
    - Whitelist de comandos aprovados
    - Blacklist de padrões perigosos
    - Sandbox path para isolamento
    - Confirmação para comandos críticos
    """

    # Comandos seguros (whitelist)
    SAFE_COMMANDS = [
        'pytest',
        'python',
        'pip',
        'npm',
        'node',
        'git',
        'ls',
        'dir',
        'pwd',
        'echo',
        'cat',
        'grep',
        'find'
    ]

    # Padrões perigosos (blacklist)
    DANGEROUS_PATTERNS = [
        'rm -rf',
        'del /f',
        'format',
        'mkfs',
        'dd if=',
        '> /dev/',
        'chmod 777',
        'chmod -R 777',
        'curl', '| sh',
        'wget | sh',
        'eval',
        'exec',
        'shutdown',
        'reboot',
        'init 0'
    ]

    # Comandos que sempre requerem confirmação
    CRITICAL_COMMANDS = [
        'rm',
        'del',
        'git push',
        'npm publish',
        'docker rm',
        'docker rmi'
    ]

    def __init__(
        self,
        sandbox_path: Path = None,
        allow_outside_sandbox: bool = False,
        require_confirmation: bool = True
    ):
        """
        Args:
            sandbox_path: Caminho do sandbox (padrão: prometheus/workspace)
            allow_outside_sandbox: Se True, permite comandos fora do sandbox (com confirmação)
            require_confirmation: Se True, pede confirmação para comandos críticos
        """
        if sandbox_path is None:
            sandbox_path = Path.home() / 'prometheus' / 'workspace'

        self.sandbox_path = Path(sandbox_path)
        self.allow_outside_sandbox = allow_outside_sandbox
        self.require_confirmation = require_confirmation

        # Cria sandbox se não existe
        self.sandbox_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"SystemToolkit initialized: sandbox={self.sandbox_path}")

    async def execute_command(
        self,
        command: str,
        cwd: Path = None,
        timeout: int = 30
    ) -> CommandResult:
        """
        Executa comando com validações de segurança

        Args:
            command: Comando a executar
            cwd: Diretório de trabalho (None = sandbox)
            timeout: Timeout em segundos

        Returns:
            CommandResult

        Raises:
            SecurityError se comando for bloqueado
        """
        logger.info(f"Executing command: {command}")

        # 1. Validação de segurança
        if not self._is_safe_command(command):
            raise SecurityError(f"Command blocked by security policy: {command}")

        # 2. Verifica se é crítico
        if self._is_critical_command(command):
            if self.require_confirmation:
                if not await self._confirm_command(command):
                    logger.info("Command cancelled by user")
                    return CommandResult(
                        success=False,
                        output="",
                        error="Cancelled by user"
                    )

        # 3. Define working directory
        if cwd is None:
            cwd = self.sandbox_path
        else:
            cwd = Path(cwd)

            # Valida se está dentro do sandbox
            if not self.allow_outside_sandbox:
                if not self._is_in_sandbox(cwd):
                    raise SecurityError(f"Path outside sandbox: {cwd}")

        # 4. Executa comando
        return await self._run_command(command, cwd, timeout)

    def _is_safe_command(self, command: str) -> bool:
        """
        Verifica se comando é seguro

        Returns:
            True se seguro, False se bloqueado
        """
        command_lower = command.lower()

        # Check blacklist (precedência sobre whitelist)
        for pattern in self.DANGEROUS_PATTERNS:
            if pattern.lower() in command_lower:
                logger.warning(f"Command blocked by blacklist: {pattern}")
                return False

        # Check whitelist
        command_parts = command.split()
        if not command_parts:
            return False

        base_command = command_parts[0]

        # Remove path se houver
        if '/' in base_command or '\\' in base_command:
            base_command = Path(base_command).name

        # Verifica whitelist
        for safe_cmd in self.SAFE_COMMANDS:
            if base_command.lower().startswith(safe_cmd.lower()):
                return True

        # Comando não está na whitelist
        logger.warning(f"Command not in whitelist: {base_command}")
        return False

    def _is_critical_command(self, command: str) -> bool:
        """Verifica se comando é crítico"""
        command_lower = command.lower()

        for critical in self.CRITICAL_COMMANDS:
            if critical.lower() in command_lower:
                return True

        return False

    def _is_in_sandbox(self, path: Path) -> bool:
        """Verifica se path está dentro do sandbox"""
        try:
            path = path.resolve()
            sandbox = self.sandbox_path.resolve()
            return str(path).startswith(str(sandbox))
        except Exception:
            return False

    async def _run_command(
        self,
        command: str,
        cwd: Path,
        timeout: int
    ) -> CommandResult:
        """Executa comando no sistema"""
        import time
        start_time = time.time()

        try:
            # Usa subprocess
            result = await asyncio.wait_for(
                asyncio.create_subprocess_shell(
                    command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(cwd)
                ),
                timeout=timeout
            )

            stdout, stderr = await result.communicate()

            duration = time.time() - start_time

            return CommandResult(
                success=result.returncode == 0,
                output=stdout.decode('utf-8', errors='ignore'),
                error=stderr.decode('utf-8', errors='ignore'),
                exit_code=result.returncode,
                duration=duration
            )

        except asyncio.TimeoutError:
            duration = time.time() - start_time
            return CommandResult(
                success=False,
                output="",
                error=f"Command timed out after {timeout}s",
                exit_code=-1,
                duration=duration
            )

        except Exception as e:
            duration = time.time() - start_time
            return CommandResult(
                success=False,
                output="",
                error=str(e),
                exit_code=-1,
                duration=duration
            )

    async def _confirm_command(self, command: str) -> bool:
        """
        Pede confirmação do usuário

        TODO: Implementar UI de confirmação real
        Por ora, retorna True (auto-approve)
        """
        logger.info(f"Auto-approving critical command: {command}")
        return True

    async def open_vscode(self, file_path: str) -> CommandResult:
        """Abre arquivo no VSCode"""
        path = Path(file_path)

        if not path.exists():
            return CommandResult(
                success=False,
                output="",
                error=f"File not found: {file_path}"
            )

        command = f"code {file_path}"
        return await self.execute_command(command)

    async def run_tests(self, test_path: str = None) -> CommandResult:
        """Roda testes com pytest"""
        if test_path:
            command = f"pytest {test_path} -v"
        else:
            command = "pytest -v"

        return await self.execute_command(command)

    async def run_python_script(self, script_path: str, args: str = "") -> CommandResult:
        """Executa script Python"""
        command = f"python {script_path} {args}".strip()
        return await self.execute_command(command)

    def get_safe_commands(self) -> List[str]:
        """Retorna lista de comandos seguros"""
        return self.SAFE_COMMANDS.copy()

    def get_dangerous_patterns(self) -> List[str]:
        """Retorna lista de padrões perigosos"""
        return self.DANGEROUS_PATTERNS.copy()
