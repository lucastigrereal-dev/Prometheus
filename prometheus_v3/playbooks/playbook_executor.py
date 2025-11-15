"""
PROMETHEUS V3 - PLAYBOOK EXECUTOR
Sistema para executar playbooks automatizados
"""

import yaml
import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
import re
import hashlib

logger = logging.getLogger(__name__)

# ============================================================================
# DATA STRUCTURES
# ============================================================================

@dataclass
class PlaybookStep:
    """Representa um passo do playbook"""
    id: str
    name: str
    type: str
    description: str
    parameters: Dict[str, Any]
    outputs: List[str]
    optional: bool = False
    when: Optional[str] = None
    dependencies: List[str] = None

@dataclass
class Playbook:
    """Representa um playbook completo"""
    name: str
    version: str
    description: str
    variables: Dict[str, Any]
    steps: List[PlaybookStep]
    validation: Dict[str, Any]
    rollback: Optional[Dict[str, Any]]
    metrics: Dict[str, Any]

@dataclass
class ExecutionContext:
    """Contexto de execução do playbook"""
    playbook_id: str
    variables: Dict[str, Any]
    outputs: Dict[str, Any]
    current_step: int
    start_time: datetime
    errors: List[str]
    warnings: List[str]

# ============================================================================
# PLAYBOOK EXECUTOR
# ============================================================================

class PlaybookExecutor:
    """
    Executor de playbooks automatizados
    Processa YAML e executa steps sequencialmente
    """
    
    def __init__(self, playbooks_dir: str = "playbooks"):
        self.playbooks_dir = Path(playbooks_dir)
        self.playbooks_cache = {}
        self.execution_history = []
        self.step_executors = self._register_step_executors()
        
    def _register_step_executors(self) -> Dict[str, callable]:
        """Registra executores para cada tipo de step"""
        return {
            'web_search': self._execute_web_search,
            'ai_generation': self._execute_ai_generation,
            'code_generation': self._execute_code_generation,
            'optimization': self._execute_optimization,
            'deployment': self._execute_deployment,
            'validation': self._execute_validation,
            'notification': self._execute_notification,
            'seo_research': self._execute_seo_research,
            'enhancement': self._execute_enhancement,
            'dns_configuration': self._execute_dns_configuration
        }
    
    async def load_playbook(self, playbook_name: str) -> Playbook:
        """Carrega playbook do arquivo YAML"""
        
        # Verifica cache
        if playbook_name in self.playbooks_cache:
            return self.playbooks_cache[playbook_name]
        
        # Busca arquivo
        playbook_path = self._find_playbook_file(playbook_name)
        if not playbook_path:
            raise FileNotFoundError(f"Playbook '{playbook_name}' not found")
        
        # Carrega YAML
        with open(playbook_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Parseia playbook
        playbook = self._parse_playbook(data)
        
        # Adiciona ao cache
        self.playbooks_cache[playbook_name] = playbook
        
        return playbook
    
    def _find_playbook_file(self, name: str) -> Optional[Path]:
        """Encontra arquivo do playbook"""
        possible_files = [
            self.playbooks_dir / f"{name}.yaml",
            self.playbooks_dir / f"{name}.yml",
            self.playbooks_dir / name if name.endswith(('.yaml', '.yml')) else None
        ]
        
        for path in possible_files:
            if path and path.exists():
                return path
        
        return None
    
    def _parse_playbook(self, data: Dict[str, Any]) -> Playbook:
        """Parseia dados YAML em objeto Playbook"""
        
        # Parse steps
        steps = []
        for step_data in data.get('steps', []):
            step = PlaybookStep(
                id=step_data.get('id', f"step_{len(steps)}"),
                name=step_data['name'],
                type=step_data['type'],
                description=step_data.get('description', ''),
                parameters=step_data.get('parameters', {}),
                outputs=step_data.get('outputs', []),
                optional=step_data.get('optional', False),
                when=step_data.get('when'),
                dependencies=step_data.get('dependencies', [])
            )
            steps.append(step)
        
        return Playbook(
            name=data['name'],
            version=data.get('version', '1.0'),
            description=data.get('description', ''),
            variables=data.get('variables', {}),
            steps=steps,
            validation=data.get('validation', {}),
            rollback=data.get('rollback'),
            metrics=data.get('metrics', {})
        )
    
    async def execute(
        self,
        playbook_name: str,
        variables: Dict[str, Any],
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """Executa um playbook"""
        
        logger.info(f"Executing playbook: {playbook_name}")
        
        # Carrega playbook
        playbook = await self.load_playbook(playbook_name)
        
        # Valida variáveis
        self._validate_variables(playbook, variables)
        
        # Cria contexto de execução
        context = ExecutionContext(
            playbook_id=self._generate_execution_id(playbook_name),
            variables=variables,
            outputs={},
            current_step=0,
            start_time=datetime.now(),
            errors=[],
            warnings=[]
        )
        
        # Executa pre-validation
        if playbook.validation.get('pre_execution'):
            await self._run_validations(
                playbook.validation['pre_execution'],
                context,
                'pre'
            )
        
        # Executa steps
        try:
            for i, step in enumerate(playbook.steps):
                context.current_step = i
                
                # Verifica condição 'when'
                if step.when and not self._evaluate_condition(step.when, context):
                    logger.info(f"Skipping step {step.name}: condition not met")
                    continue
                
                # Verifica dependências
                if not self._check_dependencies(step, context):
                    if step.optional:
                        logger.warning(f"Skipping optional step {step.name}: dependencies not met")
                        continue
                    else:
                        raise RuntimeError(f"Dependencies not met for step {step.name}")
                
                # Executa step
                if dry_run:
                    logger.info(f"[DRY RUN] Would execute: {step.name}")
                    result = {'dry_run': True, 'step': step.name}
                else:
                    result = await self._execute_step(step, context)
                
                # Armazena outputs
                for output_key in step.outputs:
                    context.outputs[f"{step.id}.{output_key}"] = result.get(output_key)
            
            # Executa post-validation
            if playbook.validation.get('post_execution'):
                await self._run_validations(
                    playbook.validation['post_execution'],
                    context,
                    'post'
                )
            
            # Prepara resultado final
            execution_result = {
                'success': len(context.errors) == 0,
                'playbook': playbook.name,
                'execution_id': context.playbook_id,
                'duration': (datetime.now() - context.start_time).total_seconds(),
                'outputs': context.outputs,
                'errors': context.errors,
                'warnings': context.warnings,
                'metrics': self._collect_metrics(context, playbook)
            }
            
            # Salva no histórico
            self.execution_history.append(execution_result)
            
            return execution_result
            
        except Exception as e:
            logger.error(f"Playbook execution failed: {e}")
            
            # Tenta rollback se disponível
            if playbook.rollback and playbook.rollback.get('enabled'):
                await self._execute_rollback(playbook, context)
            
            raise
    
    def _validate_variables(self, playbook: Playbook, provided: Dict[str, Any]):
        """Valida variáveis fornecidas"""
        
        for var_name, var_config in playbook.variables.items():
            if isinstance(var_config, dict):
                # Variável com configuração
                if var_config.get('required', False) and var_name not in provided:
                    raise ValueError(f"Required variable '{var_name}' not provided")
                
                # Aplica default se não fornecido
                if var_name not in provided and 'default' in var_config:
                    provided[var_name] = var_config['default']
    
    async def _execute_step(
        self,
        step: PlaybookStep,
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Executa um step individual"""
        
        logger.info(f"Executing step: {step.name}")
        
        # Substitui variáveis nos parâmetros
        processed_params = self._process_parameters(step.parameters, context)
        
        # Encontra executor
        executor = self.step_executors.get(step.type)
        if not executor:
            raise NotImplementedError(f"No executor for step type: {step.type}")
        
        # Executa
        try:
            result = await executor(processed_params, context)
            logger.info(f"Step {step.name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Step {step.name} failed: {e}")
            context.errors.append(f"{step.name}: {str(e)}")
            raise
    
    def _process_parameters(
        self,
        parameters: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Processa parâmetros substituindo variáveis"""
        
        def replace_vars(value):
            if isinstance(value, str):
                # Substitui {variable_name}
                pattern = r'\{([^}]+)\}'
                
                def replacer(match):
                    var_path = match.group(1)
                    
                    # Busca em variables
                    if var_path in context.variables:
                        return str(context.variables[var_path])
                    
                    # Busca em outputs
                    if var_path in context.outputs:
                        return str(context.outputs[var_path])
                    
                    # Path navigation (e.g., step1.output1)
                    parts = var_path.split('.')
                    current = context.outputs
                    
                    for part in parts:
                        if isinstance(current, dict) and part in current:
                            current = current[part]
                        else:
                            return match.group(0)  # Não encontrado, mantém original
                    
                    return str(current)
                
                return re.sub(pattern, replacer, value)
            
            elif isinstance(value, dict):
                return {k: replace_vars(v) for k, v in value.items()}
            
            elif isinstance(value, list):
                return [replace_vars(item) for item in value]
            
            else:
                return value
        
        return replace_vars(parameters)
    
    def _evaluate_condition(self, condition: str, context: ExecutionContext) -> bool:
        """Avalia condição booleana"""
        
        # Substitui variáveis
        processed = self._process_parameters({'cond': condition}, context)['cond']
        
        try:
            # Avaliação segura
            # Em produção, usar um parser mais robusto
            return eval(processed, {"__builtins__": {}}, context.variables)
        except:
            logger.warning(f"Failed to evaluate condition: {condition}")
            return False
    
    def _check_dependencies(self, step: PlaybookStep, context: ExecutionContext) -> bool:
        """Verifica se dependências foram satisfeitas"""
        
        if not step.dependencies:
            return True
        
        for dep in step.dependencies:
            # Verifica se output existe
            if not any(key.startswith(f"{dep}.") for key in context.outputs):
                return False
        
        return True
    
    async def _run_validations(
        self,
        validations: List[Dict[str, Any]],
        context: ExecutionContext,
        phase: str
    ):
        """Executa validações"""
        
        for validation in validations:
            check = validation.get('check', '')
            processed = self._process_parameters({'check': check}, context)['check']
            
            try:
                result = eval(processed, {"__builtins__": {}}, {
                    **context.variables,
                    **context.outputs
                })
                
                if not result:
                    message = validation.get('error') or validation.get('warning', 'Validation failed')
                    
                    if 'error' in validation:
                        context.errors.append(f"[{phase}] {message}")
                        raise ValueError(message)
                    else:
                        context.warnings.append(f"[{phase}] {message}")
                        
            except Exception as e:
                logger.error(f"Validation failed: {e}")
                context.errors.append(f"Validation error: {str(e)}")
    
    async def _execute_rollback(self, playbook: Playbook, context: ExecutionContext):
        """Executa procedimento de rollback"""
        
        logger.warning("Executing rollback procedure")
        
        for rollback_step in playbook.rollback.get('steps', []):
            try:
                # Verifica condição
                if 'when' in rollback_step:
                    if not self._evaluate_condition(rollback_step['when'], context):
                        continue
                
                # Executa ação de rollback
                logger.info(f"Rollback: {rollback_step['name']}")
                
                # Aqui você implementaria as ações de rollback específicas
                
            except Exception as e:
                logger.error(f"Rollback step failed: {e}")
    
    def _collect_metrics(
        self,
        context: ExecutionContext,
        playbook: Playbook
    ) -> Dict[str, Any]:
        """Coleta métricas da execução"""
        
        metrics = {
            'execution_time': (datetime.now() - context.start_time).total_seconds(),
            'steps_executed': context.current_step + 1,
            'total_steps': len(playbook.steps),
            'errors_count': len(context.errors),
            'warnings_count': len(context.warnings)
        }
        
        # Métricas customizadas do playbook
        for metric_name in playbook.metrics.get('track', []):
            if metric_name in context.outputs:
                metrics[metric_name] = context.outputs[metric_name]
        
        return metrics
    
    def _generate_execution_id(self, playbook_name: str) -> str:
        """Gera ID único para execução"""
        timestamp = datetime.now().isoformat()
        content = f"{playbook_name}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    # ============================================================================
    # STEP EXECUTORS (Simulados)
    # ============================================================================
    
    async def _execute_web_search(
        self,
        parameters: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Executa busca web"""
        
        queries = parameters.get('queries', [])
        results = []
        
        for query in queries:
            # Simulação - em produção, usar API real
            results.append({
                'query': query,
                'results': f"10 results for '{query}'"
            })
        
        return {
            'competitor_insights': results,
            'best_practices': ['Practice 1', 'Practice 2'],
            'design_trends': ['Trend 1', 'Trend 2']
        }
    
    async def _execute_ai_generation(
        self,
        parameters: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Executa geração com IA"""
        
        prompt = parameters.get('prompt', '')
        provider = parameters.get('provider', 'claude')
        
        # Simulação - em produção, chamar provider real
        return {
            'headline': 'Amazing Headline Generated',
            'subheadline': 'Perfect subheadline for conversion',
            'value_proposition': 'Clear value prop',
            'benefits': ['Benefit 1', 'Benefit 2', 'Benefit 3'],
            'how_it_works': ['Step 1', 'Step 2', 'Step 3'],
            'faq': [
                {'q': 'Question 1?', 'a': 'Answer 1'},
                {'q': 'Question 2?', 'a': 'Answer 2'}
            ],
            'cta_texts': ['Get Started', 'Learn More']
        }
    
    async def _execute_code_generation(
        self,
        parameters: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Executa geração de código"""
        
        return {
            'html_file': '<html>...</html>',
            'css_file': 'body { margin: 0; }',
            'structure_map': {'sections': ['hero', 'benefits']}
        }
    
    async def _execute_optimization(
        self,
        parameters: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Executa otimização"""
        
        return {
            'optimized_html': '<html>optimized...</html>',
            'optimized_css': 'body{margin:0}',
            'performance_report': {'score': 95}
        }
    
    async def _execute_deployment(
        self,
        parameters: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Executa deployment"""
        
        platform = parameters.get('platform', 'netlify')
        
        return {
            'live_url': f'https://example.{platform}.app',
            'preview_url': f'https://preview.example.{platform}.app',
            'deployment_id': 'deploy_123',
            'ssl_certificate': {'valid': True}
        }
    
    async def _execute_validation(
        self,
        parameters: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Executa validação"""
        
        return {
            'test_results': {
                'lighthouse_score': 92,
                'seo_score': 95,
                'accessibility_score': 88
            },
            'issues_found': [],
            'recommendations': ['Consider lazy loading']
        }
    
    async def _execute_notification(
        self,
        parameters: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Executa notificação"""
        
        channels = parameters.get('channels', {})
        
        # Simulação
        for channel_type, config in channels.items():
            logger.info(f"Sending notification via {channel_type}")
        
        return {
            'notification_sent': True,
            'report_url': 'https://reports.example.com/123'
        }
    
    async def _execute_seo_research(
        self,
        parameters: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Executa pesquisa SEO"""
        
        return {
            'primary_keywords': ['keyword1', 'keyword2'],
            'long_tail_keywords': ['long tail 1', 'long tail 2'],
            'search_volume': {'keyword1': 1000, 'keyword2': 500}
        }
    
    async def _execute_enhancement(
        self,
        parameters: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Executa melhorias"""
        
        return {
            'enhanced_html': '<html>enhanced...</html>',
            'javascript_file': 'console.log("ready");',
            'manifest_json': {'name': 'App', 'version': '1.0'}
        }
    
    async def _execute_dns_configuration(
        self,
        parameters: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Executa configuração DNS"""
        
        return {
            'domain_configured': True,
            'dns_propagation_status': 'pending'
        }

# ============================================================================
# CLI INTERFACE
# ============================================================================

async def main():
    """Interface CLI para executar playbooks"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Prometheus Playbook Executor')
    parser.add_argument('playbook', help='Nome do playbook')
    parser.add_argument('--var', '-v', action='append', help='Variável (formato: key=value)')
    parser.add_argument('--dry-run', action='store_true', help='Simular execução')
    parser.add_argument('--list', '-l', action='store_true', help='Listar playbooks disponíveis')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    executor = PlaybookExecutor()
    
    if args.list:
        # Lista playbooks
        playbooks_dir = Path('playbooks')
        if playbooks_dir.exists():
            print("\nAvailable playbooks:")
            for f in playbooks_dir.glob('*.yaml'):
                print(f"  - {f.stem}")
        return
    
    # Parse variáveis
    variables = {}
    if args.var:
        for var in args.var:
            if '=' in var:
                key, value = var.split('=', 1)
                variables[key] = value
    
    # Executa playbook
    try:
        result = await executor.execute(
            playbook_name=args.playbook,
            variables=variables,
            dry_run=args.dry_run
        )
        
        print("\n" + "="*60)
        print(f"PLAYBOOK EXECUTION {'SIMULATION' if args.dry_run else 'COMPLETED'}")
        print("="*60)
        print(f"Success: {result['success']}")
        print(f"Duration: {result['duration']:.2f}s")
        
        if result['errors']:
            print(f"\nErrors ({len(result['errors'])}):")
            for error in result['errors']:
                print(f"  ❌ {error}")
        
        if result['warnings']:
            print(f"\nWarnings ({len(result['warnings'])}):")
            for warning in result['warnings']:
                print(f"  ⚠️ {warning}")
        
        if result['success']:
            print("\n✅ Playbook executed successfully!")
        
    except Exception as e:
        print(f"\n❌ Execution failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    asyncio.run(main())
