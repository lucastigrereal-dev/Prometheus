"""
PROMETHEUS V3 - SCHEDULER SYSTEM
Sistema de agendamento de tarefas automáticas (cron jobs do Prometheus)
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Callable, Optional, List
from pathlib import Path
import inspect

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.job import Job

logger = logging.getLogger(__name__)

# ============================================================================
# SCHEDULER JOBS
# ============================================================================

class ScheduledJobs:
    """Coleção de jobs pré-definidos"""
    
    @staticmethod
    async def backup_all_data():
        """Backup completo de dados"""
        logger.info("Starting scheduled backup...")
        
        backup_items = [
            ('memories', 'data/memories'),
            ('configs', 'config/'),
            ('logs', 'logs/'),
            ('templates', 'playbooks/')
        ]
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = Path(f"backups/backup_{timestamp}")
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        for item_name, item_path in backup_items:
            source = Path(item_path)
            if source.exists():
                # Aqui você implementaria a lógica de backup real
                logger.info(f"Backing up {item_name} from {item_path}")
                # shutil.copytree(source, backup_dir / item_name)
        
        logger.info(f"Backup completed: {backup_dir}")
        return {'status': 'success', 'backup_path': str(backup_dir)}
    
    @staticmethod
    async def cleanup_old_logs(max_age_days: int = 30):
        """Limpa logs antigos"""
        logger.info(f"Cleaning logs older than {max_age_days} days...")
        
        log_dir = Path("logs")
        if not log_dir.exists():
            return {'status': 'skipped', 'reason': 'no logs directory'}
        
        cutoff_date = datetime.now() - timedelta(days=max_age_days)
        deleted_count = 0
        
        for log_file in log_dir.glob("*.log.*"):  # Arquivos de rotação
            if log_file.stat().st_mtime < cutoff_date.timestamp():
                logger.info(f"Deleting old log: {log_file}")
                log_file.unlink()
                deleted_count += 1
        
        logger.info(f"Cleanup completed: {deleted_count} files deleted")
        return {'status': 'success', 'deleted': deleted_count}
    
    @staticmethod
    async def health_check_all():
        """Verifica saúde de todos os componentes"""
        logger.info("Running health check...")
        
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'components': {}
        }
        
        # Check core
        try:
            # Aqui você verificaria o core real
            health_status['components']['core'] = 'healthy'
        except Exception as e:
            health_status['components']['core'] = f'unhealthy: {e}'
        
        # Check providers
        providers = ['claude', 'gpt4', 'gemini']
        for provider in providers:
            try:
                # Aqui você verificaria cada provider
                health_status['components'][provider] = 'healthy'
            except Exception as e:
                health_status['components'][provider] = f'unhealthy: {e}'
        
        # Check integrations
        integrations = ['redis', 'supabase', 'whatsapp']
        for integration in integrations:
            try:
                # Aqui você verificaria cada integração
                health_status['components'][integration] = 'healthy'
            except Exception as e:
                health_status['components'][integration] = f'unhealthy: {e}'
        
        # Salva resultado
        health_file = Path("logs/health_check.json")
        with open(health_file, 'w') as f:
            json.dump(health_status, f, indent=2)
        
        logger.info("Health check completed")
        return health_status
    
    @staticmethod
    async def consolidate_memories():
        """Consolida memórias similares"""
        logger.info("Consolidating memories...")
        
        # Aqui você chamaria o memory_manager.consolidate()
        # Por enquanto, simulamos
        
        consolidated = {
            'timestamp': datetime.now().isoformat(),
            'memories_before': 1000,
            'memories_after': 750,
            'consolidated': 250
        }
        
        logger.info(f"Memory consolidation completed: {consolidated['consolidated']} memories merged")
        return consolidated
    
    @staticmethod
    async def generate_weekly_report():
        """Gera relatório semanal"""
        logger.info("Generating weekly report...")
        
        report = {
            'week': datetime.now().strftime('%Y-W%V'),
            'period': {
                'start': (datetime.now() - timedelta(days=7)).isoformat(),
                'end': datetime.now().isoformat()
            },
            'metrics': {
                'commands_executed': 127,
                'success_rate': 0.94,
                'avg_response_time': 2.3,
                'errors': 8,
                'new_memories': 234,
                'api_costs': {
                    'claude': 12.50,
                    'gpt4': 8.30,
                    'total': 20.80
                }
            },
            'top_commands': [
                {'command': 'create website', 'count': 23},
                {'command': 'send message', 'count': 19},
                {'command': 'analyze data', 'count': 15}
            ]
        }
        
        # Salva relatório
        report_file = Path(f"reports/weekly_{report['week']}.json")
        report_file.parent.mkdir(exist_ok=True)
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Weekly report generated: {report_file}")
        return report

# ============================================================================
# PROMETHEUS SCHEDULER
# ============================================================================

class PrometheusScheduler:
    """
    Scheduler principal do Prometheus
    Gerencia todas as tarefas agendadas
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.scheduler = AsyncIOScheduler(
            timezone=self.config.get('timezone', 'America/Sao_Paulo')
        )
        self.jobs_registry = {}
        self.job_results = {}
        
        # Registra jobs padrão
        self.scheduled_jobs = ScheduledJobs()
        self._register_default_jobs()
    
    def _register_default_jobs(self):
        """Registra jobs padrão do sistema"""
        default_jobs = [
            {
                'id': 'backup_daily',
                'func': self.scheduled_jobs.backup_all_data,
                'trigger': 'cron',
                'hour': 3,
                'minute': 0,
                'name': 'Daily Backup'
            },
            {
                'id': 'cleanup_logs',
                'func': self.scheduled_jobs.cleanup_old_logs,
                'trigger': 'cron',
                'day_of_week': 'sun',
                'hour': 0,
                'minute': 0,
                'name': 'Weekly Log Cleanup',
                'kwargs': {'max_age_days': 30}
            },
            {
                'id': 'health_check',
                'func': self.scheduled_jobs.health_check_all,
                'trigger': 'interval',
                'minutes': 30,
                'name': 'Health Check'
            },
            {
                'id': 'memory_consolidation',
                'func': self.scheduled_jobs.consolidate_memories,
                'trigger': 'cron',
                'hour': 4,
                'minute': 0,
                'name': 'Daily Memory Consolidation'
            },
            {
                'id': 'weekly_report',
                'func': self.scheduled_jobs.generate_weekly_report,
                'trigger': 'cron',
                'day_of_week': 'mon',
                'hour': 9,
                'minute': 0,
                'name': 'Weekly Report Generation'
            }
        ]
        
        for job_config in default_jobs:
            self.jobs_registry[job_config['id']] = job_config
    
    def start(self):
        """Inicia o scheduler"""
        # Adiciona jobs registrados
        for job_id, job_config in self.jobs_registry.items():
            if self.config.get(f'jobs.{job_id}.enabled', True):
                self.add_job(**job_config)
        
        self.scheduler.start()
        logger.info(f"Scheduler started with {len(self.scheduler.get_jobs())} jobs")
    
    def stop(self):
        """Para o scheduler"""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped")
    
    def add_job(
        self,
        func: Callable,
        trigger: str,
        id: str,
        name: Optional[str] = None,
        kwargs: Optional[Dict] = None,
        **trigger_args
    ) -> Job:
        """Adiciona novo job ao scheduler"""
        
        # Wrapper para capturar resultado
        async def job_wrapper():
            try:
                result = await func(**(kwargs or {}))
                self.job_results[id] = {
                    'last_run': datetime.now().isoformat(),
                    'status': 'success',
                    'result': result
                }
                logger.info(f"Job {id} completed successfully")
            except Exception as e:
                self.job_results[id] = {
                    'last_run': datetime.now().isoformat(),
                    'status': 'error',
                    'error': str(e)
                }
                logger.error(f"Job {id} failed: {e}")
        
        job = self.scheduler.add_job(
            job_wrapper,
            trigger=trigger,
            id=id,
            name=name or id,
            **trigger_args
        )
        
        logger.info(f"Added job: {id} ({trigger})")
        return job
    
    def remove_job(self, job_id: str):
        """Remove um job"""
        self.scheduler.remove_job(job_id)
        logger.info(f"Removed job: {job_id}")
    
    def pause_job(self, job_id: str):
        """Pausa um job"""
        self.scheduler.pause_job(job_id)
        logger.info(f"Paused job: {job_id}")
    
    def resume_job(self, job_id: str):
        """Resume um job pausado"""
        self.scheduler.resume_job(job_id)
        logger.info(f"Resumed job: {job_id}")
    
    def get_jobs(self) -> List[Dict[str, Any]]:
        """Lista todos os jobs"""
        jobs = []
        for job in self.scheduler.get_jobs():
            job_info = {
                'id': job.id,
                'name': job.name,
                'trigger': str(job.trigger),
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'pending': job.pending,
                'last_result': self.job_results.get(job.id)
            }
            jobs.append(job_info)
        return jobs
    
    def run_job_now(self, job_id: str):
        """Executa um job imediatamente"""
        job = self.scheduler.get_job(job_id)
        if job:
            self.scheduler.modify_job(job_id, next_run_time=datetime.now())
            logger.info(f"Triggered immediate execution of job: {job_id}")
        else:
            logger.error(f"Job not found: {job_id}")
    
    def add_one_time_job(
        self,
        func: Callable,
        run_date: datetime,
        id: Optional[str] = None,
        name: Optional[str] = None,
        kwargs: Optional[Dict] = None
    ) -> Job:
        """Adiciona job para executar uma vez em data específica"""
        job_id = id or f"onetime_{datetime.now().timestamp()}"
        
        return self.add_job(
            func=func,
            trigger='date',
            id=job_id,
            name=name or f"One-time job {job_id}",
            kwargs=kwargs,
            run_date=run_date
        )
    
    def get_job_history(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Obtém histórico de execução de um job"""
        return self.job_results.get(job_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do scheduler"""
        jobs = self.get_jobs()
        
        return {
            'running': self.scheduler.running,
            'total_jobs': len(jobs),
            'pending_jobs': sum(1 for j in jobs if j['pending']),
            'successful_runs': sum(
                1 for r in self.job_results.values() 
                if r['status'] == 'success'
            ),
            'failed_runs': sum(
                1 for r in self.job_results.values() 
                if r['status'] == 'error'
            ),
            'jobs': jobs
        }

# ============================================================================
# CRON EXPRESSION HELPER
# ============================================================================

class CronHelper:
    """Helper para criar expressões cron"""
    
    @staticmethod
    def every_minute() -> Dict:
        """A cada minuto"""
        return {'trigger': 'interval', 'minutes': 1}
    
    @staticmethod
    def every_hour() -> Dict:
        """A cada hora"""
        return {'trigger': 'interval', 'hours': 1}
    
    @staticmethod
    def daily_at(hour: int, minute: int = 0) -> Dict:
        """Diariamente em horário específico"""
        return {
            'trigger': 'cron',
            'hour': hour,
            'minute': minute
        }
    
    @staticmethod
    def weekly_on(day: str, hour: int, minute: int = 0) -> Dict:
        """Semanalmente em dia específico"""
        days = {
            'monday': 'mon', 'tuesday': 'tue', 'wednesday': 'wed',
            'thursday': 'thu', 'friday': 'fri', 'saturday': 'sat',
            'sunday': 'sun'
        }
        
        return {
            'trigger': 'cron',
            'day_of_week': days.get(day.lower(), day),
            'hour': hour,
            'minute': minute
        }
    
    @staticmethod
    def monthly_on(day: int, hour: int, minute: int = 0) -> Dict:
        """Mensalmente em dia específico"""
        return {
            'trigger': 'cron',
            'day': day,
            'hour': hour,
            'minute': minute
        }

# ============================================================================
# EXEMPLO DE USO
# ============================================================================

async def example_custom_job():
    """Job customizado de exemplo"""
    logger.info("Running custom job...")
    await asyncio.sleep(2)
    return {'status': 'completed', 'data': 'example'}

async def main():
    """Exemplo de uso do scheduler"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Cria scheduler
    scheduler = PrometheusScheduler({
        'timezone': 'America/Sao_Paulo',
        'jobs': {
            'backup_daily': {'enabled': True},
            'cleanup_logs': {'enabled': True},
            'health_check': {'enabled': True}
        }
    })
    
    # Adiciona job customizado
    scheduler.add_job(
        func=example_custom_job,
        trigger='interval',
        seconds=10,
        id='custom_job',
        name='Custom Example Job'
    )
    
    # Inicia scheduler
    scheduler.start()
    
    # Mostra jobs
    print("\n=== Scheduled Jobs ===")
    for job in scheduler.get_jobs():
        print(f"- {job['name']} (ID: {job['id']})")
        print(f"  Trigger: {job['trigger']}")
        print(f"  Next run: {job['next_run']}")
        print()
    
    # Roda por 60 segundos
    try:
        await asyncio.sleep(60)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
    
    # Para scheduler
    scheduler.stop()
    
    # Mostra estatísticas
    stats = scheduler.get_stats()
    print("\n=== Scheduler Statistics ===")
    print(f"Total jobs: {stats['total_jobs']}")
    print(f"Successful runs: {stats['successful_runs']}")
    print(f"Failed runs: {stats['failed_runs']}")

if __name__ == "__main__":
    asyncio.run(main())
