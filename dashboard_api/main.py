"""
Prometheus Dashboard API
FastAPI backend para busca semântica no Knowledge Brain + Executor Local
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client
import openai

# Adicionar path do Prometheus ao sys.path
prometheus_path = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, prometheus_path)

from prometheus_v3.executor import LocalExecutor, BrowserExecutor, TaskManager, TaskLogger
from prometheus_v3.planner import TaskPlanner
from prometheus_v3.supervisor import CodeReviewer, ApprovalManager
from prometheus_v3.telemetry import metrics, health_checker, get_logger

# Load environment
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

# Initialize FastAPI
app = FastAPI(title="Prometheus Dashboard API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

# Initialize OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

# Initialize Executor components
local_executor = LocalExecutor()
task_manager = TaskManager()

# Initialize Browser Executor (lazy init - will initialize on first use)
browser_executor = None

# Initialize Planner
task_planner = TaskPlanner(
    supabase_client=supabase,
    openai_api_key=os.getenv('OPENAI_API_KEY')
)

# Initialize Supervisor components
code_reviewer = CodeReviewer(openai_api_key=os.getenv('OPENAI_API_KEY'))
approval_manager = ApprovalManager()


# Models
class SearchRequest(BaseModel):
    query: str
    limit: int = 10
    source_type: Optional[str] = None


class SearchResult(BaseModel):
    content: str
    similarity: float
    source_type: str
    created_at: str
    tokens: int


class StatsResponse(BaseModel):
    total_documents: int
    total_chunks: int
    claude_count: int
    gpt_count: int


# Endpoints
@app.get("/")
async def root():
    return {"status": "ok", "service": "Prometheus Dashboard API"}


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Retorna estatísticas do Knowledge Brain"""
    try:
        # Total documents
        docs_response = supabase.table('documents').select('id', count='exact').execute()
        total_documents = docs_response.count or 0

        # Total chunks
        chunks_response = supabase.table('document_chunks').select('id', count='exact').execute()
        total_chunks = chunks_response.count or 0

        # Claude count
        claude_response = supabase.table('documents').select('id', count='exact').eq('source_type', 'claude').execute()
        claude_count = claude_response.count or 0

        # GPT count
        gpt_response = supabase.table('documents').select('id', count='exact').eq('source_type', 'gpt').execute()
        gpt_count = gpt_response.count or 0

        return StatsResponse(
            total_documents=total_documents,
            total_chunks=total_chunks,
            claude_count=claude_count,
            gpt_count=gpt_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")


@app.post("/api/search")
async def semantic_search(request: SearchRequest):
    """Busca semântica no Knowledge Brain"""
    try:
        # Generate embedding for query (OpenAI v2.x syntax)
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        response = client.embeddings.create(
            input=request.query,
            model="text-embedding-ada-002"
        )
        query_embedding = response.data[0].embedding

        # Call Supabase match_documents function
        result = supabase.rpc(
            'match_documents',
            {
                'query_embedding': query_embedding,
                'match_threshold': 0.5,
                'match_count': request.limit
            }
        ).execute()

        results = []
        if result.data:
            for row in result.data:
                results.append({
                    'content': row['content'],
                    'similarity': row['similarity'],
                    'source_type': row['document_source'],  # changed from source_type
                    'created_at': '',  # not returned by function
                    'tokens': row['tokens']
                })

        return {'results': results, 'count': len(results)}

    except Exception as e:
        import traceback
        error_detail = f"Search error: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)  # Log to console
        raise HTTPException(status_code=500, detail=error_detail)


# ==================== EXECUTOR ENDPOINTS ====================

# Models for Executor
class ExecuteRequest(BaseModel):
    action: str
    params: Dict[str, Any] = {}

class CreateTaskRequest(BaseModel):
    action: str
    params: Dict[str, Any] = {}
    description: Optional[str] = None
    critical: bool = False

@app.get("/api/executor/actions")
async def get_available_actions():
    """Retorna lista de ações disponíveis do Executor"""
    return {
        "actions": local_executor.get_available_actions()
    }

@app.post("/api/executor/execute")
async def execute_action(request: ExecuteRequest):
    """Executa uma ação imediatamente (sem gerenciamento de tarefa)"""
    try:
        result = local_executor.execute(request.action, request.params)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/executor/task/create")
async def create_task(request: CreateTaskRequest):
    """Cria uma nova tarefa (não executa imediatamente)"""
    try:
        task_id = task_manager.create_task(
            action=request.action,
            params=request.params,
            description=request.description,
            critical=request.critical
        )

        task = task_manager.get_task(task_id)
        return {
            "success": True,
            "task_id": task_id,
            "task": task
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/executor/task/{task_id}/execute")
async def execute_task(task_id: str):
    """Executa uma tarefa criada"""
    try:
        task = task_manager.get_task(task_id)

        if not task:
            raise HTTPException(status_code=404, detail=f"Tarefa {task_id} não encontrada")

        if task['status'] != 'pending':
            raise HTTPException(status_code=400, detail=f"Tarefa {task_id} não está pendente (status: {task['status']})")

        # Marcar como running
        task_manager.update_task_status(task_id, 'running')
        task_manager.add_task_log(task_id, f"Iniciando execução de {task['action']}")

        # Executar
        result = local_executor.execute(task['action'], task['params'])

        # Atualizar status
        if result['success']:
            task_manager.update_task_status(task_id, 'completed', result=result['data'])
            task_manager.add_task_log(task_id, "Execução concluída com sucesso", level='success')
        else:
            task_manager.update_task_status(task_id, 'failed', error=result.get('error'))
            task_manager.add_task_log(task_id, f"Execução falhou: {result.get('error')}", level='error')

        return {
            "success": result['success'],
            "task": task_manager.get_task(task_id)
        }

    except HTTPException:
        raise
    except Exception as e:
        task_manager.update_task_status(task_id, 'failed', error=str(e))
        task_manager.add_task_log(task_id, f"Erro na execução: {str(e)}", level='error')
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/executor/tasks")
async def get_tasks(status: Optional[str] = None):
    """Retorna todas as tarefas"""
    try:
        tasks = task_manager.get_all_tasks(status=status)
        return {
            "tasks": tasks,
            "total": len(tasks)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/executor/task/{task_id}")
async def get_task(task_id: str):
    """Retorna uma tarefa específica"""
    task = task_manager.get_task(task_id)

    if not task:
        raise HTTPException(status_code=404, detail=f"Tarefa {task_id} não encontrada")

    return task

@app.get("/api/executor/stats")
async def get_executor_stats():
    """Retorna estatísticas do Executor"""
    try:
        stats = task_manager.get_task_stats()
        history = local_executor.get_execution_history(limit=10)

        return {
            "task_stats": stats,
            "recent_executions": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/executor/task/{task_id}")
async def cancel_task(task_id: str):
    """Cancela uma tarefa pendente"""
    try:
        task = task_manager.get_task(task_id)

        if not task:
            raise HTTPException(status_code=404, detail=f"Tarefa {task_id} não encontrada")

        if task['status'] not in ['pending']:
            raise HTTPException(status_code=400, detail=f"Apenas tarefas pendentes podem ser canceladas (status atual: {task['status']})")

        task_manager.update_task_status(task_id, 'cancelled')
        task_manager.add_task_log(task_id, "Tarefa cancelada pelo usuário", level='warning')

        return {
            "success": True,
            "task": task_manager.get_task(task_id)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== END EXECUTOR ENDPOINTS ====================


# ==================== PLANNER ENDPOINTS ====================

# Models for Planner
class PlanRequest(BaseModel):
    user_request: str
    context: Optional[Dict[str, Any]] = None
    max_knowledge_results: int = 5

class PlanToTasksRequest(BaseModel):
    plan_id: str

@app.post("/api/planner/create-plan")
async def create_plan(request: PlanRequest):
    """
    Cria um plano baseado em requisição do usuário
    Usa Knowledge Brain + IA para gerar plano estruturado
    """
    try:
        plan = task_planner.create_plan(
            user_request=request.user_request,
            context=request.context,
            max_knowledge_results=request.max_knowledge_results
        )

        return {
            "success": True,
            "plan": plan
        }
    except Exception as e:
        import traceback
        error_detail = f"Error creating plan: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=error_detail)

@app.post("/api/planner/plan-to-tasks")
async def plan_to_tasks(request: PlanToTasksRequest):
    """
    Converte um plano em tarefas executáveis
    Cria tarefas no TaskManager prontas para execução
    """
    try:
        # Buscar plano no histórico
        history = task_planner.get_planning_history(limit=100)
        plan = next((p for p in history if p['plan_id'] == request.plan_id), None)

        if not plan:
            raise HTTPException(status_code=404, detail=f"Plano {request.plan_id} não encontrado")

        # Converter plano em tarefas
        executor_tasks = task_planner.plan_to_executor_tasks(plan)

        # Criar tarefas no TaskManager
        created_tasks = []
        for task_spec in executor_tasks:
            task_id = task_manager.create_task(
                action=task_spec['action'],
                params=task_spec['params'],
                description=task_spec['description'],
                critical=task_spec.get('critical', False)
            )

            created_tasks.append({
                'task_id': task_id,
                'action': task_spec['action'],
                'description': task_spec['description']
            })

        return {
            "success": True,
            "plan_id": request.plan_id,
            "tasks_created": len(created_tasks),
            "tasks": created_tasks
        }
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Error converting plan to tasks: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=error_detail)

@app.get("/api/planner/history")
async def get_planning_history(limit: int = 10):
    """Retorna histórico de planejamentos"""
    try:
        history = task_planner.get_planning_history(limit=limit)
        return {
            "history": history,
            "total": len(history)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/planner/quick-plan-and-execute")
async def quick_plan_and_execute(request: PlanRequest):
    """
    Atalho: Cria plano + converte para tarefas + executa tudo

    Fluxo completo:
    1. Busca conhecimento relevante
    2. Gera plano com IA
    3. Converte plano em tarefas
    4. Cria e executa tarefas
    5. Retorna resultado
    """
    try:
        # Passo 1: Criar plano
        plan = task_planner.create_plan(
            user_request=request.user_request,
            context=request.context,
            max_knowledge_results=request.max_knowledge_results
        )

        # Passo 2: Converter para tarefas
        executor_tasks = task_planner.plan_to_executor_tasks(plan)

        # Passo 3: Executar cada tarefa
        executed_tasks = []
        for task_spec in executor_tasks:
            # Criar tarefa
            task_id = task_manager.create_task(
                action=task_spec['action'],
                params=task_spec['params'],
                description=task_spec['description'],
                critical=task_spec.get('critical', False)
            )

            # Executar tarefa
            task_manager.update_task_status(task_id, 'running')
            result = local_executor.execute(task_spec['action'], task_spec['params'])

            # Atualizar status
            if result['success']:
                task_manager.update_task_status(task_id, 'completed', result=result['data'])
            else:
                task_manager.update_task_status(task_id, 'failed', error=result.get('error'))

            executed_tasks.append({
                'task_id': task_id,
                'action': task_spec['action'],
                'success': result['success'],
                'result': result.get('data') if result['success'] else None,
                'error': result.get('error') if not result['success'] else None
            })

        return {
            "success": True,
            "plan": plan,
            "tasks_executed": len(executed_tasks),
            "tasks": executed_tasks
        }
    except Exception as e:
        import traceback
        error_detail = f"Error in quick plan and execute: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=error_detail)

# ==================== END PLANNER ENDPOINTS ====================


# ==================== BROWSER EXECUTOR ENDPOINTS ====================

# Models for Browser Executor
class BrowserInitRequest(BaseModel):
    config: Optional[Dict[str, Any]] = None

class BrowserExecuteRequest(BaseModel):
    action: str
    params: Dict[str, Any] = {}

@app.post("/api/browser/initialize")
async def initialize_browser(request: BrowserInitRequest):
    """Inicializa o navegador"""
    global browser_executor

    try:
        if browser_executor is None:
            browser_executor = BrowserExecutor(config=request.config)

        result = await browser_executor.initialize()
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/browser/execute")
async def execute_browser_action(request: BrowserExecuteRequest):
    """Executa uma ação de browser"""
    global browser_executor

    try:
        # Verificar se browser está inicializado
        if browser_executor is None:
            browser_executor = BrowserExecutor()
            init_result = await browser_executor.initialize()
            if not init_result['success']:
                return init_result

        result = await browser_executor.execute(request.action, request.params)
        return result

    except Exception as e:
        import traceback
        error_detail = f"Browser execution error: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=error_detail)

@app.get("/api/browser/actions")
async def get_browser_actions():
    """Retorna lista de ações de browser disponíveis"""
    global browser_executor

    try:
        if browser_executor is None:
            browser_executor = BrowserExecutor()

        return {
            "actions": browser_executor.get_available_actions()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/browser/status")
async def get_browser_status():
    """Retorna status do browser executor"""
    global browser_executor

    try:
        if browser_executor is None:
            return {
                "initialized": False,
                "browser_method": None,
                "config": None,
                "total_executions": 0
            }

        return browser_executor.get_status()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/browser/history")
async def get_browser_history(limit: int = 10):
    """Retorna histórico de execuções de browser"""
    global browser_executor

    try:
        if browser_executor is None:
            return {"history": [], "total": 0}

        history = browser_executor.get_execution_history(limit=limit)
        return {
            "history": history,
            "total": len(history)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/browser/close")
async def close_browser():
    """Fecha o navegador"""
    global browser_executor

    try:
        if browser_executor is not None:
            await browser_executor.close()
            browser_executor = None

        return {"success": True, "message": "Browser closed"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== END BROWSER EXECUTOR ENDPOINTS ====================


# ==================== SUPERVISOR ENDPOINTS ====================

# Models for Supervisor
class CodeReviewRequest(BaseModel):
    code: str
    language: str = "python"
    context: Optional[Dict[str, Any]] = None
    aspects: Optional[List[str]] = None

class ApprovalRequest(BaseModel):
    task_id: str
    task_description: str
    task_action: str
    task_params: Dict[str, Any]
    reason: str
    timeout_minutes: int = 60

class ApproveRejectRequest(BaseModel):
    approval_id: str
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None

@app.post("/api/supervisor/review-code")
async def review_code(request: CodeReviewRequest):
    """Revisa código usando IA"""
    try:
        review_result = code_reviewer.review_code(
            code=request.code,
            language=request.language,
            context=request.context,
            aspects=request.aspects
        )

        return {
            "success": True,
            "review": review_result
        }

    except Exception as e:
        import traceback
        error_detail = f"Code review error: {str(e)}\n{traceback.format_exc()}"
        print(error_detail)
        raise HTTPException(status_code=500, detail=error_detail)

@app.get("/api/supervisor/review-history")
async def get_review_history(limit: int = 10):
    """Retorna histórico de revisões de código"""
    try:
        history = code_reviewer.get_review_history(limit=limit)
        return {
            "history": history,
            "total": len(history)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/supervisor/review-stats")
async def get_review_stats():
    """Retorna estatísticas de revisões"""
    try:
        stats = code_reviewer.get_review_stats()
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/supervisor/request-approval")
async def request_approval(request: ApprovalRequest):
    """Solicita aprovação para tarefa crítica"""
    try:
        result = approval_manager.request_approval(
            task_id=request.task_id,
            task_description=request.task_description,
            task_action=request.task_action,
            task_params=request.task_params,
            reason=request.reason,
            timeout_minutes=request.timeout_minutes
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/supervisor/approve")
async def approve_task(request: ApproveRejectRequest):
    """Aprova uma tarefa crítica"""
    try:
        result = approval_manager.approve(
            approval_id=request.approval_id,
            notes=request.notes
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/supervisor/reject")
async def reject_task(request: ApproveRejectRequest):
    """Rejeita uma tarefa crítica"""
    try:
        if not request.rejection_reason:
            raise HTTPException(
                status_code=400,
                detail="rejection_reason é obrigatório para rejeitar uma tarefa"
            )

        result = approval_manager.reject(
            approval_id=request.approval_id,
            rejection_reason=request.rejection_reason
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/supervisor/pending-approvals")
async def get_pending_approvals():
    """Retorna aprovações pendentes"""
    try:
        pending = approval_manager.get_pending_approvals()
        return {
            "pending": pending,
            "total": len(pending)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/supervisor/approval/{approval_id}")
async def get_approval(approval_id: str):
    """Retorna detalhes de uma aprovação"""
    approval = approval_manager.get_approval(approval_id)

    if not approval:
        raise HTTPException(status_code=404, detail=f"Aprovação {approval_id} não encontrada")

    return approval

@app.get("/api/supervisor/approval-history")
async def get_approval_history(limit: int = 10, status: Optional[str] = None):
    """Retorna histórico de aprovações"""
    try:
        history = approval_manager.get_approval_history(limit=limit, status=status)
        return {
            "history": history,
            "total": len(history)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/supervisor/approval-stats")
async def get_approval_stats():
    """Retorna estatísticas de aprovações"""
    try:
        stats = approval_manager.get_approval_stats()
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== END SUPERVISOR ENDPOINTS ====================


# ==================== TELEMETRY & HEALTH ENDPOINTS ====================

@app.get("/health")
async def health_check():
    """Health check endpoint - rápido sem executar todos os checks"""
    return health_checker.get_last_results()

@app.get("/health/live")
async def liveness_check():
    """Liveness check - verifica se API está respondendo"""
    return {"status": "healthy", "service": "Prometheus API"}

@app.get("/health/ready")
async def readiness_check():
    """Readiness check - verifica se todos os componentes estão prontos"""
    results = await health_checker.run_all_checks()

    # Se algum check crítico falhou, retorna 503
    if results['status'] in ['unhealthy', 'degraded']:
        raise HTTPException(status_code=503, detail=results)

    return results

@app.get("/api/telemetry/metrics")
async def get_metrics():
    """Retorna todas as métricas do sistema"""
    try:
        all_metrics = metrics.get_all_metrics()
        return all_metrics

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/telemetry/metrics/summary")
async def get_metrics_summary():
    """Retorna resumo executivo das métricas"""
    try:
        summary = metrics.get_summary()
        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/telemetry/metrics/reset")
async def reset_metrics():
    """Reseta todas as métricas (usar com cuidado)"""
    try:
        metrics.reset_all()
        return {"success": True, "message": "Métricas resetadas"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ==================== END TELEMETRY & HEALTH ENDPOINTS ====================


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
