"""
Integrity Health Checker
Verifica saúde do sistema de integridade
"""

from typing import Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger("prometheus.integrity_health")


class HealthStatus(Enum):
    """Status de saúde"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"


@dataclass
class HealthCheckResult:
    """
    Resultado de verificação de saúde
    """
    component: str
    status: HealthStatus
    message: str
    timestamp: str
    metrics: dict[str, Any]
    recommendations: list[str]

    def __post_init__(self):
        if isinstance(self.status, str):
            self.status = HealthStatus(self.status)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data['status'] = self.status.value
        return data


class IntegrityHealthChecker:
    """
    Verificador de saúde do sistema de integridade

    Verifica:
    - Taxa de integridade dos arquivos
    - Performance de verificações
    - Taxa de sucesso de escritas
    - Volume de mutações não autorizadas
    - Presença de violações críticas
    """

    def __init__(
        self,
        integrity_service: Any,
        metrics_collector: Any
    ):
        self.integrity_service = integrity_service
        self.metrics_collector = metrics_collector
        logger.info("IntegrityHealthChecker inicializado")

    def check_overall_health(self) -> HealthCheckResult:
        """
        Verifica saúde geral do sistema

        Returns:
            HealthCheckResult com status geral
        """
        # Executar checks individuais
        file_integrity_check = self.check_file_integrity()
        verification_check = self.check_verification_performance()
        write_operations_check = self.check_write_operations()
        mutations_check = self.check_mutations()

        # Determinar status geral (pior status encontrado)
        statuses = [
            file_integrity_check.status,
            verification_check.status,
            write_operations_check.status,
            mutations_check.status
        ]

        # Ordenar por severidade
        severity_order = [
            HealthStatus.CRITICAL,
            HealthStatus.UNHEALTHY,
            HealthStatus.DEGRADED,
            HealthStatus.HEALTHY
        ]

        overall_status = HealthStatus.HEALTHY
        for severity in severity_order:
            if severity in statuses:
                overall_status = severity
                break

        # Agregar recomendações
        all_recommendations = []
        for check in [file_integrity_check, verification_check, write_operations_check, mutations_check]:
            all_recommendations.extend(check.recommendations)

        # Agregar métricas
        all_metrics = {
            "file_integrity": file_integrity_check.metrics,
            "verification": verification_check.metrics,
            "write_operations": write_operations_check.metrics,
            "mutations": mutations_check.metrics
        }

        return HealthCheckResult(
            component="integrity_system",
            status=overall_status,
            message=self._generate_overall_message(overall_status),
            timestamp=datetime.now().isoformat(),
            metrics=all_metrics,
            recommendations=all_recommendations
        )

    def check_file_integrity(self) -> HealthCheckResult:
        """
        Verifica saúde da integridade dos arquivos

        Returns:
            HealthCheckResult
        """
        try:
            stats = self.integrity_service.get_stats()

            total = stats["total_files"]
            valid = stats["by_status"].get("valid", 0)
            modified = stats["by_status"].get("modified", 0)
            corrupted = stats["by_status"].get("corrupted", 0)

            if total == 0:
                return HealthCheckResult(
                    component="file_integrity",
                    status=HealthStatus.DEGRADED,
                    message="No files are being monitored",
                    timestamp=datetime.now().isoformat(),
                    metrics={"total_files": 0},
                    recommendations=["Register files for monitoring"]
                )

            integrity_rate = valid / total if total > 0 else 0

            # Determinar status
            status = HealthStatus.HEALTHY
            recommendations = []

            if corrupted > 0:
                status = HealthStatus.CRITICAL
                recommendations.append(f"Fix {corrupted} corrupted files immediately")
            elif integrity_rate < 0.9:
                status = HealthStatus.UNHEALTHY
                recommendations.append(f"Integrity rate low ({integrity_rate:.1%}), review {modified} modified files")
            elif integrity_rate < 0.95:
                status = HealthStatus.DEGRADED
                recommendations.append(f"Approve or reject {modified} pending modifications")

            return HealthCheckResult(
                component="file_integrity",
                status=status,
                message=f"Integrity rate: {integrity_rate:.1%}",
                timestamp=datetime.now().isoformat(),
                metrics={
                    "total_files": total,
                    "valid_files": valid,
                    "modified_files": modified,
                    "corrupted_files": corrupted,
                    "integrity_rate": integrity_rate
                },
                recommendations=recommendations
            )

        except Exception as e:
            logger.error(f"Erro ao verificar integridade: {e}")
            return HealthCheckResult(
                component="file_integrity",
                status=HealthStatus.UNHEALTHY,
                message=f"Health check failed: {e}",
                timestamp=datetime.now().isoformat(),
                metrics={},
                recommendations=["Investigate health check failure"]
            )

    def check_verification_performance(self) -> HealthCheckResult:
        """
        Verifica performance das verificações

        Returns:
            HealthCheckResult
        """
        try:
            # Obter métricas de duração
            stats = self.metrics_collector.get_metric_stats(
                "integrity.verification.duration_ms",
                hours=1
            )

            if stats["count"] == 0:
                return HealthCheckResult(
                    component="verification_performance",
                    status=HealthStatus.DEGRADED,
                    message="No verifications in last hour",
                    timestamp=datetime.now().isoformat(),
                    metrics={"verifications_count": 0},
                    recommendations=["Schedule regular verifications"]
                )

            avg_duration = stats["avg"]
            max_duration = stats["max"]

            # Determinar status baseado em duração
            status = HealthStatus.HEALTHY
            recommendations = []

            if avg_duration > 10000:  # >10s
                status = HealthStatus.UNHEALTHY
                recommendations.append("Average verification time too high (>10s)")
            elif avg_duration > 5000:  # >5s
                status = HealthStatus.DEGRADED
                recommendations.append("Consider optimizing verification process")

            if max_duration > 30000:  # >30s
                recommendations.append(f"Some verifications taking very long ({max_duration/1000:.1f}s)")

            return HealthCheckResult(
                component="verification_performance",
                status=status,
                message=f"Avg verification: {avg_duration:.0f}ms",
                timestamp=datetime.now().isoformat(),
                metrics={
                    "avg_duration_ms": avg_duration,
                    "max_duration_ms": max_duration,
                    "min_duration_ms": stats["min"],
                    "verifications_count": stats["count"]
                },
                recommendations=recommendations
            )

        except Exception as e:
            logger.error(f"Erro ao verificar performance: {e}")
            return HealthCheckResult(
                component="verification_performance",
                status=HealthStatus.DEGRADED,
                message=f"Unable to assess performance: {e}",
                timestamp=datetime.now().isoformat(),
                metrics={},
                recommendations=[]
            )

    def check_write_operations(self) -> HealthCheckResult:
        """
        Verifica saúde das operações de escrita

        Returns:
            HealthCheckResult
        """
        try:
            counters = self.metrics_collector.get_current_counters()

            total_ops = counters.get("safe_write.operations.total", 0)
            success_ops = counters.get("safe_write.operations.success", 0)
            failed_ops = counters.get("safe_write.operations.failed", 0)

            if total_ops == 0:
                return HealthCheckResult(
                    component="write_operations",
                    status=HealthStatus.HEALTHY,
                    message="No write operations",
                    timestamp=datetime.now().isoformat(),
                    metrics={"total_operations": 0},
                    recommendations=[]
                )

            success_rate = success_ops / total_ops if total_ops > 0 else 0

            # Determinar status
            status = HealthStatus.HEALTHY
            recommendations = []

            if success_rate < 0.9:
                status = HealthStatus.CRITICAL
                recommendations.append(f"Write success rate critical ({success_rate:.1%})")
            elif success_rate < 0.95:
                status = HealthStatus.UNHEALTHY
                recommendations.append(f"Write success rate low ({success_rate:.1%})")
            elif success_rate < 0.99:
                status = HealthStatus.DEGRADED
                recommendations.append(f"Some write operations failing ({failed_ops} failures)")

            return HealthCheckResult(
                component="write_operations",
                status=status,
                message=f"Success rate: {success_rate:.1%}",
                timestamp=datetime.now().isoformat(),
                metrics={
                    "total_operations": total_ops,
                    "success_operations": success_ops,
                    "failed_operations": failed_ops,
                    "success_rate": success_rate
                },
                recommendations=recommendations
            )

        except Exception as e:
            logger.error(f"Erro ao verificar operações: {e}")
            return HealthCheckResult(
                component="write_operations",
                status=HealthStatus.DEGRADED,
                message=f"Unable to assess: {e}",
                timestamp=datetime.now().isoformat(),
                metrics={},
                recommendations=[]
            )

    def check_mutations(self) -> HealthCheckResult:
        """
        Verifica volume de mutações

        Returns:
            HealthCheckResult
        """
        try:
            counters = self.metrics_collector.get_current_counters()

            detected = counters.get("mutations.detected", 0)
            authorized = counters.get("mutations.authorized", 0)

            unauthorized = detected - authorized

            # Determinar status
            status = HealthStatus.HEALTHY
            recommendations = []

            if unauthorized > 10:
                status = HealthStatus.CRITICAL
                recommendations.append(f"{unauthorized} unauthorized mutations detected!")
            elif unauthorized > 5:
                status = HealthStatus.UNHEALTHY
                recommendations.append(f"Review {unauthorized} unauthorized mutations")
            elif unauthorized > 0:
                status = HealthStatus.DEGRADED
                recommendations.append(f"Approve or investigate {unauthorized} pending mutations")

            return HealthCheckResult(
                component="mutations",
                status=status,
                message=f"{unauthorized} unauthorized mutations",
                timestamp=datetime.now().isoformat(),
                metrics={
                    "mutations_detected": detected,
                    "mutations_authorized": authorized,
                    "mutations_unauthorized": unauthorized
                },
                recommendations=recommendations
            )

        except Exception as e:
            logger.error(f"Erro ao verificar mutações: {e}")
            return HealthCheckResult(
                component="mutations",
                status=HealthStatus.DEGRADED,
                message=f"Unable to assess: {e}",
                timestamp=datetime.now().isoformat(),
                metrics={},
                recommendations=[]
            )

    def _generate_overall_message(self, status: HealthStatus) -> str:
        """
        Gera mensagem de status geral

        Args:
            status: Status geral

        Returns:
            Mensagem legível
        """
        messages = {
            HealthStatus.HEALTHY: "All integrity systems operating normally",
            HealthStatus.DEGRADED: "Integrity system degraded, attention needed",
            HealthStatus.UNHEALTHY: "Integrity system unhealthy, immediate action required",
            HealthStatus.CRITICAL: "CRITICAL: Integrity compromised, urgent intervention needed"
        }

        return messages.get(status, "Unknown status")
