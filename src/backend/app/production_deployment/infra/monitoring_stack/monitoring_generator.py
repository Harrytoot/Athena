from dataclasses import dataclass, field
from typing import Optional
import json
import os


@dataclass
class PrometheusConfig:
    scrape_interval: str = "15s"
    evaluation_interval: str = "15s"
    targets: list[str] = field(default_factory=lambda: ["localhost:8000"])
    metrics_path: str = "/metrics"

    def to_dict(self) -> dict:
        return {
            "global": {
                "scrape_interval": self.scrape_interval,
                "evaluation_interval": self.evaluation_interval,
            },
            "scrape_configs": [
                {
                    "job_name": "athena",
                    "metrics_path": self.metrics_path,
                    "static_configs": [{"targets": self.targets}],
                }
            ],
        }


@dataclass
class GrafanaDatasource:
    name: str = "Prometheus"
    type: str = "prometheus"
    url: str = "http://prometheus:9090"
    access: str = "proxy"

    def to_dict(self) -> dict:
        return {
            "apiVersion": 1,
            "datasources": [
                {
                    "name": self.name,
                    "type": self.type,
                    "url": self.url,
                    "access": self.access,
                    "isDefault": True,
                }
            ],
        }


@dataclass
class DashboardPanel:
    title: str
    type: str = "graph"
    datasource: str = "Prometheus"
    targets: list[dict] = field(default_factory=list)


@dataclass
class GrafanaDashboard:
    title: str
    panels: list[DashboardPanel] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "dashboard": {
                "title": self.title,
                "panels": [
                    {
                        "title": p.title,
                        "type": p.type,
                        "datasource": p.datasource,
                        "targets": p.targets,
                    }
                    for p in self.panels
                ],
            }
        }


class MonitoringStackGenerator:
    def __init__(self, output_dir: str) -> None:
        self._output_dir = output_dir

    def generate_prometheus(self, config: Optional[PrometheusConfig] = None) -> str:
        config = config or PrometheusConfig()
        path = os.path.join(self._output_dir, "prometheus.yml")
        os.makedirs(self._output_dir, exist_ok=True)

        content = json.dumps(config.to_dict(), indent=2)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return path

    def generate_grafana_datasource(self, config: Optional[GrafanaDatasource] = None) -> str:
        config = config or GrafanaDatasource()
        path = os.path.join(self._output_dir, "datasource.yml")
        os.makedirs(self._output_dir, exist_ok=True)

        content = json.dumps(config.to_dict(), indent=2)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return path

    def generate_default_dashboard(self) -> str:
        dashboard = GrafanaDashboard(
            title="Athena System Overview",
            panels=[
                DashboardPanel(
                    title="API Request Rate",
                    targets=[{"expr": 'rate(http_requests_total[5m])', "legendFormat": "{{method}} {{endpoint}}"}],
                ),
                DashboardPanel(
                    title="Response Latency",
                    targets=[{"expr": 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))', "legendFormat": "p95"}],
                ),
                DashboardPanel(
                    title="Error Rate",
                    targets=[{"expr": 'rate(http_requests_total{status=~"5.."}[5m])', "legendFormat": "5xx errors"}],
                ),
                DashboardPanel(
                    title="Component Health",
                    targets=[{"expr": 'athena_component_health', "legendFormat": "{{component}}"}],
                ),
            ],
        )

        path = os.path.join(self._output_dir, "dashboard.json")
        os.makedirs(self._output_dir, exist_ok=True)

        content = json.dumps(dashboard.to_dict(), indent=2)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return path

    def generate_docker_compose_monitoring(
        self, prometheus_port: int = 9090, grafana_port: int = 3000
    ) -> str:
        compose = {
            "version": "3.8",
            "services": {
                "prometheus": {
                    "image": "prom/prometheus:latest",
                    "ports": [f"{prometheus_port}:9090"],
                    "volumes": ["./prometheus.yml:/etc/prometheus/prometheus.yml"],
                    "command": "--config.file=/etc/prometheus/prometheus.yml",
                    "restart": "unless-stopped",
                    "networks": ["monitoring"],
                },
                "grafana": {
                    "image": "grafana/grafana:latest",
                    "ports": [f"{grafana_port}:3000"],
                    "volumes": ["./datasource.yml:/etc/grafana/provisioning/datasources/datasource.yml"],
                    "restart": "unless-stopped",
                    "networks": ["monitoring"],
                },
            },
            "networks": {
                "monitoring": {"driver": "bridge"},
            },
        }

        path = os.path.join(self._output_dir, "docker-compose.monitoring.yml")
        os.makedirs(self._output_dir, exist_ok=True)

        import yaml
        content = yaml.dump(compose, default_flow_style=False, sort_keys=False)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return path
