from enum import Enum

from pydantic import Field
from pydantic_settings import BaseSettings


class DeploymentMode(str, Enum):
    DOCKER = "docker"
    KUBERNETES = "kubernetes"
    STANDALONE = "standalone"


class DeploymentSettings(BaseSettings):
    DEPLOYMENT_MODE: DeploymentMode = DeploymentMode.STANDALONE
    DEPLOYMENT_REGION: str = "default"
    DEPLOYMENT_INSTANCE_ID: str = "athena-01"

    RUNTIME_RESTART_MAX_RETRIES: int = Field(default=3, ge=0)
    RUNTIME_RESTART_BACKOFF_SECONDS: float = Field(default=1.0, ge=0)
    RUNTIME_HEALTH_CHECK_INTERVAL_SECONDS: float = Field(default=30.0, ge=1.0)
    RUNTIME_COMPONENT_STARTUP_TIMEOUT_SECONDS: float = Field(default=60.0, ge=1.0)

    FAILOVER_ENABLED: bool = True
    FAILOVER_HEARTBEAT_INTERVAL_SECONDS: float = Field(default=10.0, ge=1.0)
    FAILOVER_LEASE_DURATION_SECONDS: float = Field(default=30.0, ge=1.0)

    SECRET_BACKEND: str = "env"
    SECRET_VAULT_ADDR: str = ""
    SECRET_VAULT_TOKEN: str = ""
    SECRET_ENCRYPTION_KEY: str = Field(default="", description="AES-256 key for at-rest secret encryption")

    DOCKER_REGISTRY: str = ""
    DOCKER_IMAGE_TAG: str = "latest"

    K8S_NAMESPACE: str = "athena"
    K8S_CONTEXT: str = ""

    MONITORING_PROMETHEUS_PORT: int = 9090
    MONITORING_GRAFANA_PORT: int = 3000

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "env_prefix": "ATHENA_",
    }

    @property
    def is_production(self) -> bool:
        from app.config import settings
        return settings.ENV == "production"

    @property
    def is_kubernetes(self) -> bool:
        return self.DEPLOYMENT_MODE == DeploymentMode.KUBERNETES

    @property
    def is_docker(self) -> bool:
        return self.DEPLOYMENT_MODE == DeploymentMode.DOCKER


deployment_config = DeploymentSettings()
