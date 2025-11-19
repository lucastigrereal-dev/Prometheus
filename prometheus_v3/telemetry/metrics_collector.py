"""
Metrics Collector - Sistema de métricas de performance e uso
PRINCÍPIOS:
- Contadores (incrementais): requests, tasks, errors
- Gauges (valores instantâneos): active_tasks, memory_usage
- Histogramas (distribuições): latency, duration
- Agregação e estatísticas
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
import threading

class MetricsCollector:
    """Coletor de métricas do sistema"""

    def __init__(self, window_minutes: int = 60):
        """
        Inicializa o coletor de métricas

        Args:
            window_minutes: Janela de tempo para métricas rolantes (minutos)
        """
        self.window_minutes = window_minutes
        self.window_seconds = window_minutes * 60

        # Contadores (incrementais)
        self.counters: Dict[str, int] = defaultdict(int)

        # Gauges (valores instantâneos)
        self.gauges: Dict[str, float] = {}

        # Histogramas (séries temporais com valores)
        self.histograms: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))

        # Durações (para calcular latências)
        self.durations: Dict[str, List[float]] = defaultdict(list)

        # Lock para thread-safety
        self.lock = threading.Lock()

        # Timestamp de inicialização
        self.start_time = datetime.now()

    def increment(self, counter: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """
        Incrementa um contador

        Args:
            counter: Nome do contador
            value: Valor a incrementar (default 1)
            labels: Labels para dimensões adicionais
        """
        with self.lock:
            key = self._build_key(counter, labels)
            self.counters[key] += value

    def decrement(self, counter: str, value: int = 1, labels: Optional[Dict[str, str]] = None):
        """Decrementa um contador"""
        with self.lock:
            key = self._build_key(counter, labels)
            self.counters[key] -= value

    def set_gauge(self, gauge: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Define valor de um gauge

        Args:
            gauge: Nome do gauge
            value: Valor atual
            labels: Labels para dimensões adicionais
        """
        with self.lock:
            key = self._build_key(gauge, labels)
            self.gauges[key] = value

    def record_value(self, metric: str, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Registra um valor em histograma

        Args:
            metric: Nome da métrica
            value: Valor a registrar
            labels: Labels para dimensões adicionais
        """
        with self.lock:
            key = self._build_key(metric, labels)
            timestamp = datetime.now()
            self.histograms[key].append({
                'timestamp': timestamp,
                'value': value
            })

            # Limpar valores antigos
            self._cleanup_histogram(key)

    def record_duration(self, metric: str, duration_seconds: float, labels: Optional[Dict[str, str]] = None):
        """
        Registra uma duração (para cálculo de latências)

        Args:
            metric: Nome da métrica
            duration_seconds: Duração em segundos
            labels: Labels para dimensões adicionais
        """
        self.record_value(metric, duration_seconds, labels)

    def time_operation(self, metric: str, labels: Optional[Dict[str, str]] = None):
        """
        Context manager para medir duração de operação

        Usage:
            with metrics.time_operation('api_request'):
                # código a medir
                pass
        """
        return _TimerContext(self, metric, labels)

    def _build_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Constrói chave única com labels"""
        if not labels:
            return name

        label_str = ','.join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def _cleanup_histogram(self, key: str):
        """Remove valores antigos do histograma baseado na janela de tempo"""
        cutoff_time = datetime.now() - timedelta(seconds=self.window_seconds)

        histogram = self.histograms[key]
        while histogram and histogram[0]['timestamp'] < cutoff_time:
            histogram.popleft()

    def get_counter(self, counter: str, labels: Optional[Dict[str, str]] = None) -> int:
        """Retorna valor de um contador"""
        key = self._build_key(counter, labels)
        return self.counters.get(key, 0)

    def get_gauge(self, gauge: str, labels: Optional[Dict[str, str]] = None) -> Optional[float]:
        """Retorna valor de um gauge"""
        key = self._build_key(gauge, labels)
        return self.gauges.get(key)

    def get_histogram_stats(self, metric: str, labels: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Retorna estatísticas de um histograma

        Returns:
            Dict com count, sum, avg, min, max, p50, p95, p99
        """
        key = self._build_key(metric, labels)
        histogram = self.histograms.get(key, deque())

        if not histogram:
            return {
                'count': 0,
                'sum': 0,
                'avg': 0,
                'min': 0,
                'max': 0,
                'p50': 0,
                'p95': 0,
                'p99': 0
            }

        values = [entry['value'] for entry in histogram]
        sorted_values = sorted(values)
        count = len(sorted_values)

        return {
            'count': count,
            'sum': sum(sorted_values),
            'avg': sum(sorted_values) / count,
            'min': sorted_values[0],
            'max': sorted_values[-1],
            'p50': self._percentile(sorted_values, 0.50),
            'p95': self._percentile(sorted_values, 0.95),
            'p99': self._percentile(sorted_values, 0.99)
        }

    def _percentile(self, sorted_values: List[float], percentile: float) -> float:
        """Calcula percentil"""
        if not sorted_values:
            return 0

        index = int(len(sorted_values) * percentile)
        index = min(index, len(sorted_values) - 1)
        return sorted_values[index]

    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Retorna todas as métricas

        Returns:
            Dict com counters, gauges e histograms
        """
        with self.lock:
            # Calcular uptime
            uptime_seconds = (datetime.now() - self.start_time).total_seconds()

            return {
                'timestamp': datetime.now().isoformat(),
                'uptime_seconds': uptime_seconds,
                'counters': dict(self.counters),
                'gauges': dict(self.gauges),
                'histograms': {
                    key: self.get_histogram_stats(key.split('{')[0], self._parse_labels(key))
                    for key in self.histograms.keys()
                }
            }

    def _parse_labels(self, key: str) -> Optional[Dict[str, str]]:
        """Parse labels de uma chave"""
        if '{' not in key:
            return None

        label_str = key.split('{')[1].rstrip('}')
        if not label_str:
            return None

        labels = {}
        for pair in label_str.split(','):
            k, v = pair.split('=')
            labels[k] = v

        return labels

    def reset_all(self):
        """Reseta todas as métricas"""
        with self.lock:
            self.counters.clear()
            self.gauges.clear()
            self.histograms.clear()
            self.start_time = datetime.now()

    def get_summary(self) -> Dict[str, Any]:
        """
        Retorna resumo executivo das métricas

        Returns:
            Dict com principais KPIs
        """
        uptime = (datetime.now() - self.start_time).total_seconds()

        return {
            'uptime_seconds': uptime,
            'uptime_hours': round(uptime / 3600, 2),
            'total_requests': self.get_counter('api_requests'),
            'total_tasks': self.get_counter('tasks_total'),
            'tasks_completed': self.get_counter('tasks_completed'),
            'tasks_failed': self.get_counter('tasks_failed'),
            'active_tasks': self.get_gauge('active_tasks') or 0,
            'avg_task_duration_seconds': self.get_histogram_stats('task_duration').get('avg', 0),
            'avg_api_latency_ms': self.get_histogram_stats('api_latency_ms').get('avg', 0)
        }


class _TimerContext:
    """Context manager para medir duração"""

    def __init__(self, collector: MetricsCollector, metric: str, labels: Optional[Dict[str, str]]):
        self.collector = collector
        self.metric = metric
        self.labels = labels
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.collector.record_duration(self.metric, duration, self.labels)


# Singleton global
metrics = MetricsCollector()
