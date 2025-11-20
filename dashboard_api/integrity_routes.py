Integrity API Routes
Rotas FastAPI para sistema de integridade de arquivos

INTEGRAÇÃO:
No arquivo dashboard_api/main.py existente, adicionar:

    from integrity_routes import router as integrity_router
    app.include_router(integrity_router, prefix="/api/integrity", tags=["integrity"])
"""

from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, Any
from datetime import datetime
from pathlib import Path
import logging

# Imports dos módulos de integridade
import sys
sys.path.append(str(Path(__file__).parent.parent))

from file_integrity.file_integrity_service import FileIntegrityService
from file_integrity.file_audit import FileAudit
from safe_write.safe_write import SafeWriter, WriteOperation, WriteMode
from safe_write.safe_write_logger import SafeWriteLogger
from supervisor.change_diff_analyzer import ChangeDiffAnalyzer
from supervisor.file_mutation_checker import FileMutationChecker
from supervisor.code_boundary_protector import CodeBoundaryProtector
from supervisor.config_watcher import ConfigWatcher

logger = logging.getLogger("prometheus.integrity_api")

# Router
router = APIRouter()

# Inicialização de serviços (singleton pattern)
_services = {}


def get_services():
    """
    Inicializa e retorna serviços de integridade (singleton)

    Returns:
        Dict com instâncias dos serviços
    """
    if not _services:
        logger.info("Inicializando serviços de integridade...")

        # File Integrity Service
        integrity_service = FileIntegrityService(
            index_path="runtime/file_index.json",
            auto_save=True
        )

        # File Audit
        audit_logger = FileAudit(
            audit_log_path="runtime/integrity_audit.log"
        )

        # Safe Writer
        safe_writer = SafeWriter(
            backup_dir="runtime/backups",
            integrity_service=integrity_service,
            audit_logger=audit_logger,
            dry_run=False
        )

        # Safe Write Logger
        safe_write_logger = SafeWriteLogger(
            log_path="runtime/safe_write.log"
        )

        # Change Diff Analyzer
        diff_analyzer = ChangeDiffAnalyzer()

        # File Mutation Checker
        mutation_checker = FileMutationChecker(
            integrity_service=integrity_service,
            mutation_log_path="runtime/mutations.log"
        )

        # Code Boundary Protector
        boundary_protector = CodeBoundaryProtector()

        # Config Watcher
        config_watcher = ConfigWatcher(
            state_path="runtime/supervisor_state.json"
        )

        _services.update({
            "integrity_service": integrity_service,
            "audit_logger": audit_logger,
            "safe_writer": safe_writer,
            "safe_write_logger": safe_write_logger,
            "diff_analyzer": diff_analyzer,
            "mutation_checker": mutation_checker,
            "boundary_protector": boundary_protector,
            "config_watcher": config_watcher
        })

        logger.info("Serviços de integridade inicializados")

    return _services


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class StatusResponse(BaseModel):
    """Resposta de status geral"""
    status: str = Field(..., description="Status do sistema")
    message: str = Field(..., description="Mensagem descritiva")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    data: Optional[dict[str, Any]] = None


class FileRegistrationRequest(BaseModel):
    """Request para registrar arquivo"""
    file_path: str = Field(..., description="Caminho do arquivo")
    category: str = Field(default="unknown", description="Categoria (code, config, data, log)")
    protected: bool = Field(default=False, description="Se arquivo é protegido/crítico")
    metadata: Optional[dict[str, Any]] = Field(default=None, description="Metadados adicionais")


class FileVerificationRequest(BaseModel):
    """Request para verificar arquivo"""
    file_path: str = Field(..., description="Caminho do arquivo")


class FileApprovalRequest(BaseModel):
    """Request para aprovar modificação"""
    file_path: str = Field(..., description="Caminho do arquivo")
    approved_by: str = Field(default="user", description="Quem aprovou")


class SafeWriteRequest(BaseModel):
    """Request para escrita segura"""
    target_path: str = Field(..., description="Caminho do arquivo")
    content: str = Field(..., description="Conteúdo a escrever")
    mode: str = Field(default="create", description="Modo: create, overwrite, append")
    encoding: str = Field(default="utf-8", description="Encoding do arquivo")
    create_backup: bool = Field(default=True, description="Criar backup antes de sobrescrever")
    verify_after: bool = Field(default=True, description="Verificar conteúdo após escrita")
    dry_run: bool = Field(default=False, description="Simular operação sem executar")


class DiffAnalysisRequest(BaseModel):
    """Request para análise de diff"""
    original_path: str = Field(..., description="Caminho do arquivo original")
    modified_path: str = Field(..., description="Caminho do arquivo modificado")


class CodeValidationRequest(BaseModel):
    """Request para validação de código"""
    file_path: Optional[str] = Field(None, description="Caminho do arquivo (ou content)")
    content: Optional[str] = Field(None, description="Conteúdo em memória (ou file_path)")
    file_type: str = Field(default="python", description="Tipo de arquivo")


class ConfigRegistrationRequest(BaseModel):
    """Request para registrar config"""
    config_path: str = Field(..., description="Caminho do arquivo de config")


# ============================================================================
# ROUTES: STATUS & HEALTH
# ============================================================================

@router.get("/status", response_model=StatusResponse)
async def get_integrity_status():
    """
    **Status geral do sistema de integridade**

    Retorna estatísticas e saúde do sistema.
    """
    try:
        services = get_services()
        integrity_service = services["integrity_service"]

        stats = integrity_service.get_stats()

        # Determinar status baseado em modificações
        modified_count = stats["by_status"].get("modified", 0)
        corrupted_count = stats["by_status"].get("corrupted", 0)

        if corrupted_count > 0:
            status = "critical"
            message = f"{corrupted_count} arquivos corrompidos detectados"
        elif modified_count > 0:
            status = "warning"
            message = f"{modified_count} arquivos modificados não aprovados"
        else:
            status = "healthy"
            message = "Sistema de integridade operacional"

        return StatusResponse(
            status=status,
            message=message,
            data={
                "statistics": stats,
                "services_active": True
            }
        )

    except Exception as e:
        logger.error(f"Erro ao obter status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    **Health check simples**

    Verifica se API está respondendo.
    """
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


# ============================================================================
# ROUTES: FILE INTEGRITY
# ============================================================================

@router.get("/files")
async def list_files(
    status: Optional[str] = Query(None, description="Filtrar por status (valid, modified, deleted, corrupted)"),
    category: Optional[str] = Query(None, description="Filtrar por categoria (code, config, data, log)"),
    protected: Optional[bool] = Query(None, description="Filtrar por proteção"),
    limit: int = Query(100, ge=1, le=1000, description="Limite de resultados")
):
    """
    **Lista arquivos indexados**

    Retorna lista de arquivos monitorados com filtros opcionais.
    """
    try:
        services = get_services()
        integrity_service = services["integrity_service"]

        records = integrity_service.index.list_files(
            status=status,
            category=category,
            protected=protected
        )

        # Limitar resultados
        records = records[:limit]

        # Converter para dict
        files = [
            {
                "path": r.path,
                "hash": r.hash,
                "size_bytes": r.size_bytes,
                "modified_at": r.modified_at,
                "indexed_at": r.indexed_at,
                "status": r.status,
                "category": r.category,
                "protected": r.protected,
                "last_verified": r.last_verified,
                "backup_path": r.backup_path
            }
            for r in records
        ]

        return {
            "total": len(files),
            "files": files
        }

    except Exception as e:
        logger.error(f"Erro ao listar arquivos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/register", response_model=StatusResponse)
async def register_file(request: FileRegistrationRequest):
    """
    **Registra novo arquivo no índice de integridade**

    Adiciona arquivo ao sistema de monitoramento.
    """
    try:
        services = get_services()
        integrity_service = services["integrity_service"]

        success = integrity_service.register_file(
            file_path=request.file_path,
            category=request.category,
            protected=request.protected,
            metadata=request.metadata
        )

        if success:
            return StatusResponse(
                status="success",
                message=f"Arquivo registrado: {request.file_path}",
                data={"file_path": request.file_path}
            )
        else:
            raise HTTPException(status_code=400, detail="Falha ao registrar arquivo")

    except Exception as e:
        logger.error(f"Erro ao registrar arquivo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/verify")
async def verify_file(request: FileVerificationRequest):
    """
    **Verifica integridade de arquivo específico**

    Compara hash atual com hash indexado.
    """
    try:
        services = get_services()
        integrity_service = services["integrity_service"]

        result = integrity_service.verify_file(request.file_path)

        return {
            "file_path": request.file_path,
            "verification_result": result,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Erro ao verificar arquivo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/verify-all")
async def verify_all_files():
    """
    **Verifica integridade de todos os arquivos indexados**

    Executa verificação completa do sistema.
    """
    try:
        services = get_services()
        integrity_service = services["integrity_service"]

        result = integrity_service.verify_all()

        return {
            "summary": result.to_dict(),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Erro ao verificar arquivos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/files/approve", response_model=StatusResponse)
async def approve_modification(request: FileApprovalRequest):
    """
    **Aprova modificação de arquivo**

    Atualiza hash no índice para refletir mudança autorizada.
    """
    try:
        services = get_services()
        integrity_service = services["integrity_service"]
        audit_logger = services["audit_logger"]

        success = integrity_service.approve_modification(request.file_path)

        if success:
            # Registrar aprovação
            audit_logger.log_approval(
                file_path=request.file_path,
                approved_by=request.approved_by
            )

            return StatusResponse(
                status="success",
                message=f"Modificação aprovada: {request.file_path}",
                data={
                    "file_path": request.file_path,
                    "approved_by": request.approved_by
                }
            )
        else:
            raise HTTPException(status_code=400, detail="Falha ao aprovar modificação")

    except Exception as e:
        logger.error(f"Erro ao aprovar modificação: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/protected")
async def get_protected_files():
    """
    **Lista arquivos protegidos/críticos**

    Retorna apenas arquivos marcados como protegidos.
    """
    try:
        services = get_services()
        integrity_service = services["integrity_service"]

        records = integrity_service.get_protected_files()

        files = [
            {
                "path": r.path,
                "category": r.category,
                "status": r.status,
                "last_verified": r.last_verified
            }
            for r in records
        ]

        return {
            "total": len(files),
            "protected_files": files
        }

    except Exception as e:
        logger.error(f"Erro ao listar arquivos protegidos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files/modified")
async def get_modified_files():
    """
    **Lista arquivos modificados não aprovados**

    Retorna arquivos que foram alterados mas não aprovados.
    """
    try:
        services = get_services()
        integrity_service = services["integrity_service"]

        records = integrity_service.get_modified_files()

        files = [
            {
                "path": r.path,
                "category": r.category,
                "protected": r.protected,
                "last_verified": r.last_verified
            }
            for r in records
        ]

        return {
            "total": len(files),
            "modified_files": files
        }

    except Exception as e:
        logger.error(f"Erro ao listar arquivos modificados: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ROUTES: SAFE WRITE
# ============================================================================

@router.post("/safe-write")
async def safe_write_file(request: SafeWriteRequest):
    """
    **Executa escrita segura de arquivo**

    Pipeline: temp → verify → commit → index → log
    """
    try:
        services = get_services()
        safe_writer = services["safe_writer"]

        # Converter mode string para enum
        mode_map = {
            "create": WriteMode.CREATE,
            "overwrite": WriteMode.OVERWRITE,
            "append": WriteMode.APPEND
        }

        mode = mode_map.get(request.mode.lower(), WriteMode.CREATE)

        # Dry run temporário se solicitado
        if request.dry_run:
            safe_writer.dry_run = True

        # Executar escrita
        operation = WriteOperation(
            target_path=request.target_path,
            content=request.content,
            mode=mode,
            encoding=request.encoding,
            create_backup=request.create_backup,
            verify_after=request.verify_after
        )

        result = safe_writer.write(operation)

        # Restaurar dry_run
        if request.dry_run:
            safe_writer.dry_run = False

        return {
            "write_result": result.to_dict(),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Erro na escrita segura: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/safe-write/operations")
async def get_safe_write_operations(
    limit: int = Query(100, ge=1, le=1000, description="Limite de resultados")
):
    """
    **Lista operações de escrita recentes**

    Retorna histórico de operações do Safe-Write Engine.
    """
    try:
        services = get_services()
        safe_write_logger = services["safe_write_logger"]

        operations = safe_write_logger.get_recent_operations(limit=limit)

        return {
            "total": len(operations),
            "operations": operations
        }

    except Exception as e:
        logger.error(f"Erro ao listar operações: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/safe-write/stats")
async def get_safe_write_stats():
    """
    **Estatísticas de escrita segura**

    Retorna métricas de operações de escrita.
    """
    try:
        services = get_services()
        safe_write_logger = services["safe_write_logger"]

        stats = safe_write_logger.get_stats()

        return {
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/safe-write/backups/{file_path:path}")
async def get_file_backups(file_path: str):
    """
    **Lista backups de arquivo específico**

    Retorna histórico de backups criados.
    """
    try:
        services = get_services()
        safe_writer = services["safe_writer"]

        backups = safe_writer.get_backup_files(file_path)

        backup_list = [
            {
                "path": str(b),
                "name": b.name,
                "size_bytes": b.stat().st_size,
                "created_at": datetime.fromtimestamp(b.stat().st_ctime).isoformat()
            }
            for b in backups
        ]

        return {
            "file_path": file_path,
            "total_backups": len(backup_list),
            "backups": backup_list
        }

    except Exception as e:
        logger.error(f"Erro ao listar backups: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ROUTES: SUPERVISOR
# ============================================================================

@router.post("/supervisor/diff")
async def analyze_diff(request: DiffAnalysisRequest):
    """
    **Analisa diferenças entre duas versões de arquivo**

    Gera unified diff e análise de impacto.
    """
    try:
        services = get_services()
        diff_analyzer = services["diff_analyzer"]

        result = diff_analyzer.analyze_file_change(
            original_path=request.original_path,
            modified_path=request.modified_path
        )

        return {
            "diff_analysis": result.to_dict(),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Erro ao analisar diff: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/supervisor/check-mutations")
async def check_mutations():
    """
    **Verifica mutações em arquivos monitorados**

    Detecta criação/modificação/deleção não autorizada.
    """
    try:
        services = get_services()
        mutation_checker = services["mutation_checker"]

        mutations = mutation_checker.check_for_mutations()

        mutation_list = [m.to_dict() for m in mutations]

        return {
            "total_mutations": len(mutation_list),
            "mutations": mutation_list,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Erro ao verificar mutações: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/supervisor/mutations")
async def get_recent_mutations(
    limit: int = Query(100, ge=1, le=1000, description="Limite de resultados")
):
    """
    **Lista mutações recentes**

    Retorna histórico de mutações detectadas.
    """
    try:
        services = get_services()
        mutation_checker = services["mutation_checker"]

        mutations = mutation_checker.get_recent_mutations(limit=limit)

        mutation_list = [m.to_dict() for m in mutations]

        return {
            "total": len(mutation_list),
            "mutations": mutation_list
        }

    except Exception as e:
        logger.error(f"Erro ao listar mutações: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/supervisor/validate-code")
async def validate_code(request: CodeValidationRequest):
    """
    **Valida código Python**

    Verifica sintaxe, imports, padrões proibidos.
    """
    try:
        services = get_services()
        boundary_protector = services["boundary_protector"]

        if request.file_path:
            violations = boundary_protector.validate_file(request.file_path)
        elif request.content:
            violations = boundary_protector.validate_content(
                content=request.content,
                file_type=request.file_type
            )
        else:
            raise HTTPException(status_code=400, detail="Forneça file_path ou content")

        violation_list = [v.to_dict() for v in violations]

        has_critical = any(v.severity == "critical" for v in violations)

        return {
            "is_valid": not has_critical,
            "total_violations": len(violation_list),
            "violations": violation_list,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Erro ao validar código: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/supervisor/register-config")
async def register_config(request: ConfigRegistrationRequest):
    """
    **Registra arquivo de configuração para monitoramento**

    Cria snapshot para detecção de mudanças.
    """
    try:
        services = get_services()
        config_watcher = services["config_watcher"]

        success = config_watcher.register_config(request.config_path)

        if success:
            return {
                "status": "success",
                "message": f"Config registrado: {request.config_path}",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail="Falha ao registrar config")

    except Exception as e:
        logger.error(f"Erro ao registrar config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/supervisor/check-config/{config_path:path}")
async def check_config_changes(config_path: str):
    """
    **Verifica mudanças em arquivo de configuração**

    Compara com snapshot registrado.
    """
    try:
        services = get_services()
        config_watcher = services["config_watcher"]

        changes = config_watcher.check_config_changes(config_path)

        change_list = [c.to_dict() for c in changes]

        return {
            "config_path": config_path,
            "total_changes": len(change_list),
            "changes": change_list,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Erro ao verificar mudanças: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ROUTES: AUDIT
# ============================================================================

@router.get("/audit/events")
async def get_audit_events(
    limit: int = Query(100, ge=1, le=1000, description="Limite de resultados")
):
    """
    **Lista eventos de auditoria recentes**

    Retorna histórico de operações no sistema de integridade.
    """
    try:
        services = get_services()
        audit_logger = services["audit_logger"]

        events = audit_logger.get_recent_events(limit=limit)

        return {
            "total": len(events),
            "events": events
        }

    except Exception as e:
        logger.error(f"Erro ao listar eventos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/events/{file_path:path}")
async def get_file_audit_events(file_path: str, limit: int = Query(50, ge=1, le=500)):
    """
    **Lista eventos de auditoria de arquivo específico**

    Retorna histórico de operações em arquivo.
    """
    try:
        services = get_services()
        audit_logger = services["audit_logger"]

        events = audit_logger.get_events_for_file(file_path, limit=limit)

        return {
            "file_path": file_path,
            "total": len(events),
            "events": events
        }

    except Exception as e:
        logger.error(f"Erro ao listar eventos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/audit/critical")
async def get_critical_events(limit: int = Query(50, ge=1, le=500)):
    """
    **Lista eventos críticos de auditoria**

    Retorna apenas eventos de severidade crítica.
    """
    try:
        services = get_services()
        audit_logger = services["audit_logger"]

        events = audit_logger.get_critical_events(limit=limit)

        return {
            "total": len(events),
            "critical_events": events
        }

    except Exception as e:
        logger.error(f"Erro ao listar eventos críticos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STARTUP EVENT
# ============================================================================

@router.on_event("startup")
async def startup_event():
    """
    Evento de startup para inicializar serviços
    """
    logger.info("Inicializando rotas de integridade...")
    get_services()  # Força inicialização
    logger.info("Rotas de integridade prontas")
