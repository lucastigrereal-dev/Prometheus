"""
Prometheus Telemetry Extensions
Métricas e health checks para o sistema de integridade
"""

from .integrity_metrics import IntegrityMetricsCollector, MetricPoint
from .integrity_health import IntegrityHealthChecker, HealthCheckResult, HealthStatus

__version__ = "3.5.0"

__all__ = [
    "IntegrityMetricsCollector",
    "MetricPoint",
    "IntegrityHealthChecker",
    "HealthCheckResult",
    "HealthStatus",
]
