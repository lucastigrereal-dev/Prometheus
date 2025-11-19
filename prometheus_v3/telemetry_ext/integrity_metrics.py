"""
Integrity Metrics Collector
Coleta métricas do sistema de integridade para observabilidade
"""

import time
from typing import Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict
import json
from pathlib import Path
import logging

logger = logging.getLogger("prometheus.integrity_metrics")


@dataclass
class MetricPoint:
    """
    Ponto de métrica individual
    """
    timestamp: str
    metric_name: str
    value: float
    labels: dict[str, str]
    unit: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class IntegrityMetricsCollector:
    """
    Coletor de métricas do sistema de integridade

    Métricas coletadas:
    - integrity.files.total
    - integrity.files.valid
    - integrity.files.modified
    - integrity.files.corrupted
    - integrity.files.protected
    - integrity.verification.duration_ms
    - integrity.verification.success_rate
    - safe_write.operations.total
    - safe_write.operations.success
    - safe_write.operations.failed
    - safe_write.bytes_written
    - mutations.detected
    - mutations.authorized
    - violations.detected
    - violations.critical
    """

    def __init__(
        self,
        metrics_file: str | Path = "runtime/integrity_metrics.jsonl",
        retention_days: int = 30
    ):
        self.metrics_file = Path(metrics_file)
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days

        # Contadores em memória
        self.counters: dict[str, float] = defaultdict(float)
        self.gauges: dict[str, float] = {}
        self.histograms: dict[str, list[float]] = defaultdict(list)

        logger.info(f"IntegrityMetricsCollector inicializado: {metrics_file}")

    def record_metric(
        self,
        metric_name: str,
        value: float,
        labels: Optional[dict[str, str]] = None,
        unit: str = ""
    ):
        """
        Registra métrica

        Args:
            metric_name: Nome da métrica (ex: integrity.files.total)
            value: Valor da métrica
            labels: Labels para dimensionar métrica
            unit: Unidade da métrica (ms, bytes, count)
        """
        point = MetricPoint(
            timestamp=datetime.now().isoformat(),
            metric_name=metric_name,
            value=value,
            labels=labels or {},
            unit=unit
        )

        # Append ao arquivo
        try:
            with open(self.metrics_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(point.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Erro ao registrar métrica: {e}")

    def increment_counter(self, metric_name: str, value: float = 1.0, labels: Optional[dict] = None):
        """
        Incrementa contador

        Args:
            metric_name: Nome do contador
            value: Valor a incrementar
            labels: Labels opcionais
        """
        self.counters[metric_name] += value
        self.record_metric(metric_name, self.counters[metric_name], labels, unit="count")

    def set_gauge(self, metric_name: str, value: float, labels: Optional[dict] = None):
        """
        Define valor de gauge (valor atual)

        Args:
            metric_name: Nome do gauge
            value: Valor atual
            labels: Labels opcionais
        """
        self.gauges[metric_name] = value
        self.record_metric(metric_name, value, labels)

    def record_histogram(self, metric_name: str, value: float, labels: Optional[dict] = None):
        """
        Registra valor em histograma

        Args:
            metric_name: Nome do histograma
            value: Valor observado
            labels: Labels opcionais
        """
        self.histograms[metric_name].append(value)
        self.record_metric(metric_name, value, labels)

    # ========================================================================
    # MÉTODOS DE CONVENIÊNCIA PARA INTEGRIDADE
    # ========================================================================

    def record_file_stats(self, stats: dict[str, Any]):
        """
        Registra estatísticas de arquivos

        Args:
            stats: Dict com estatísticas do FileIntegrityService
        """
        # Total files
        self.set_gauge("integrity.files.total", stats["total_files"])

        # Por status
        for status, count in stats["by_status"].items():
            self.set_gauge(
                "integrity.files.by_status",
                count,
                labels={"status": status}
            )

        # Por categoria
        for category, count in stats["by_category"].items():
            self.set_gauge(
                "integrity.files.by_category",
                count,
                labels={"category": category}
            )

        # Protected files
        self.set_gauge("integrity.files.protected", stats["protected_files"])

        # Total size
        self.set_gauge(
            "integrity.files.total_size_bytes",
            stats["total_size_bytes"],
            unit="bytes"
        )

    def record_verification_duration(self, duration_ms: float, success: bool):
        """
        Registra duração de verificação

        Args:
            duration_ms: Duração em milliseconds
            success: Se verificação foi bem-sucedida
        """
        self.record_histogram(
            "integrity.verification.duration_ms",
            duration_ms,
            labels={"success": str(success)},
        )

    def record_safe_write_operation(
        self,
        success: bool,
        bytes_written: int,
        duration_ms: float
    ):
        """
        Registra operação de safe write

        Args:
            success: Se operação foi bem-sucedida
            bytes_written: Bytes escritos
            duration_ms: Duração da operação
        """
        # Incrementar contador
        if success:
            self.increment_counter("safe_write.operations.success")
        else:
            self.increment_counter("safe_write.operations.failed")

        self.increment_counter("safe_write.operations.total")

        # Bytes escritos
        if success:
            self.increment_counter("safe_write.bytes_written", bytes_written)

        # Duração
        self.record_histogram(
            "safe_write.operation.duration_ms",
            duration_ms,
            labels={"success": str(success)}
        )

    def record_mutation_detected(self, mutation_type: str, authorized: bool):
        """
        Registra mutação detectada

        Args:
            mutation_type: Tipo de mutação (created, modified, deleted)
            authorized: Se mutação foi autorizada
        """
        self.increment_counter(
            "mutations.detected",
            labels={"type": mutation_type, "authorized": str(authorized)}
        )

        if authorized:
            self.increment_counter("mutations.authorized")

    def record_violation(self, violation_type: str, severity: str):
        """
        Registra violação detectada

        Args:
            violation_type: Tipo de violação
            severity: Severidade (warning, error, critical)
        """
        self.increment_counter(
            "violations.detected",
            labels={"type": violation_type, "severity": severity}
        )

        if severity == "critical":
            self.increment_counter("violations.critical")

    # ========================================================================
    # QUERY E ANÁLISE
    # ========================================================================

    def query_metrics(
        self,
        metric_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        labels: Optional[dict[str, str]] = None
    ) -> list[MetricPoint]:
        """
        Consulta métricas por nome e período

        Args:
            metric_name: Nome da métrica
            start_time: Timestamp inicial (default: últimas 24h)
            end_time: Timestamp final (default: agora)
            labels: Filtrar por labels

        Returns:
            Lista de MetricPoint
        """
        if not self.metrics_file.exists():
            return []

        if start_time is None:
            start_time = datetime.now() - timedelta(hours=24)

        if end_time is None:
            end_time = datetime.now()

        results = []

        try:
            with open(self.metrics_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        point = MetricPoint(**data)

                        # Filtrar por nome
                        if point.metric_name != metric_name:
                            continue

                        # Filtrar por timestamp
                        point_time = datetime.fromisoformat(point.timestamp)
                        if not (start_time <= point_time <= end_time):
                            continue

                        # Filtrar por labels
                        if labels:
                            if not all(point.labels.get(k) == v for k, v in labels.items()):
                                continue

                        results.append(point)

                    except Exception as e:
                        logger.error(f"Erro ao parsear métrica: {e}")
                        continue

        except Exception as e:
            logger.error(f"Erro ao consultar métricas: {e}")

        return results

    def get_metric_stats(
        self,
        metric_name: str,
        hours: int = 24
    ) -> dict[str, float]:
        """
        Obtém estatísticas de métrica

        Args:
            metric_name: Nome da métrica
            hours: Número de horas para análise

        Returns:
            Dict com min, max, avg, sum, count
        """
        start_time = datetime.now() - timedelta(hours=hours)
        points = self.query_metrics(metric_name, start_time=start_time)

        if not points:
            return {
                "min": 0.0,
                "max": 0.0,
                "avg": 0.0,
                "sum": 0.0,
                "count": 0
            }

        values = [p.value for p in points]

        return {
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "sum": sum(values),
            "count": len(values)
        }

    def cleanup_old_metrics(self):
        """
        Remove métricas antigas (baseado em retention_days)
        """
        if not self.metrics_file.exists():
            return

        cutoff_time = datetime.now() - timedelta(days=self.retention_days)
        temp_file = self.metrics_file.with_suffix('.tmp')

        try:
            kept_count = 0
            removed_count = 0

            with open(self.metrics_file, 'r', encoding='utf-8') as infile:
                with open(temp_file, 'w', encoding='utf-8') as outfile:
                    for line in infile:
                        try:
                            data = json.loads(line.strip())
                            timestamp = datetime.fromisoformat(data['timestamp'])

                            if timestamp >= cutoff_time:
                                outfile.write(line)
                                kept_count += 1
                            else:
                                removed_count += 1

                        except Exception as e:
                            logger.error(f"Erro ao processar linha: {e}")
                            outfile.write(line)  # Manter linha com erro

            # Substituir arquivo original
            temp_file.replace(self.metrics_file)

            logger.info(f"Cleanup de métricas: {kept_count} mantidas, {removed_count} removidas")

        except Exception as e:
            logger.error(f"Erro no cleanup: {e}")
            if temp_file.exists():
                temp_file.unlink()

    def get_current_counters(self) -> dict[str, float]:
        """
        Retorna valores atuais dos contadores

        Returns:
            Dict com contadores
        """
        return dict(self.counters)

    def get_current_gauges(self) -> dict[str, float]:
        """
        Retorna valores atuais dos gauges

        Returns:
            Dict com gauges
        """
        return dict(self.gauges)

    def reset_counters(self):
        """
        Reseta contadores em memória
        """
        self.counters.clear()
        logger.info("Contadores resetados")
