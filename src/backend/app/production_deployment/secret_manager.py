from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
import logging
import os

from app.production_deployment.environment_switcher import EnvironmentType

logger = logging.getLogger(__name__)


@dataclass
class BrokerCredentials:
    broker_id: str
    api_key: str = ""
    api_secret: str = ""
    account_id: str = ""
    paper_api_key: str = ""
    paper_api_secret: str = ""

    def mask(self) -> dict[str, str]:
        return {
            "broker_id": self.broker_id,
            "api_key": self._mask(self.api_key),
            "api_secret": "********",
            "account_id": self.account_id,
            "paper_api_key": self._mask(self.paper_api_key),
            "paper_api_secret": "********",
        }

    @staticmethod
    def _mask(value: str) -> str:
        if len(value) <= 4:
            return "****"
        return value[:2] + "****" + value[-2:]


@dataclass
class ApiCredentials:
    service_name: str
    api_key: str = ""
    api_secret: str = ""
    endpoint: str = ""

    def mask(self) -> dict[str, str]:
        return {
            "service_name": self.service_name,
            "api_key": BrokerCredentials._mask(self.api_key),
            "api_secret": "********",
            "endpoint": self.endpoint,
        }


@dataclass
class SecretBundle:
    environment: EnvironmentType
    broker_credentials: list[BrokerCredentials] = field(default_factory=list)
    api_credentials: list[ApiCredentials] = field(default_factory=list)
    custom_secrets: dict[str, str] = field(default_factory=dict)


class SecretBackend(ABC):
    @abstractmethod
    async def get_secret(self, key: str) -> Optional[str]:
        ...

    @abstractmethod
    async def set_secret(self, key: str, value: str) -> None:
        ...

    @abstractmethod
    async def delete_secret(self, key: str) -> None:
        ...


class EnvSecretBackend(SecretBackend):
    def __init__(self, prefix: str = "ATHENA_SECRET_") -> None:
        self._prefix = prefix

    async def get_secret(self, key: str) -> Optional[str]:
        return os.getenv(f"{self._prefix}{key}")

    async def set_secret(self, key: str, value: str) -> None:
        os.environ[f"{self._prefix}{key}"] = value

    async def delete_secret(self, key: str) -> None:
        os.environ.pop(f"{self._prefix}{key}", None)


class SecretManager:
    _INSTANCE: Optional["SecretManager"] = None
    _bundle_lock: bool = False

    def __init__(self, backend: Optional[SecretBackend] = None) -> None:
        self._backend = backend or EnvSecretBackend()
        self._bundles: dict[EnvironmentType, SecretBundle] = {}
        self._current_env: Optional[EnvironmentType] = None

    @classmethod
    def get_instance(cls) -> "SecretManager":
        if cls._INSTANCE is None:
            cls._INSTANCE = cls()
        return cls._INSTANCE

    @property
    def backend(self) -> SecretBackend:
        return self._backend

    async def load_for_environment(self, env_type: EnvironmentType) -> SecretBundle:
        self._current_env = env_type

        if env_type in self._bundles:
            return self._bundles[env_type]

        bundle = await self._read_bundle(env_type)
        self._bundles[env_type] = bundle
        logger.info("Secrets loaded for environment: %s", env_type.value)
        return bundle

    async def unload_environment(self, env_type: EnvironmentType) -> None:
        self._bundles.pop(env_type, None)
        if self._current_env == env_type:
            self._current_env = None
        logger.info("Secrets unloaded for environment: %s", env_type.value)

    async def get_broker_credentials(self, broker_id: str) -> Optional[BrokerCredentials]:
        bundle = self._get_current_bundle()
        for cred in bundle.broker_credentials:
            if cred.broker_id == broker_id:
                return cred
        return None

    async def get_api_credentials(self, service_name: str) -> Optional[ApiCredentials]:
        bundle = self._get_current_bundle()
        for cred in bundle.api_credentials:
            if cred.service_name == service_name:
                return cred
        return None

    async def get_custom_secret(self, key: str) -> Optional[str]:
        bundle = self._get_current_bundle()
        return bundle.custom_secrets.get(key)

    async def set_custom_secret(self, key: str, value: str) -> None:
        bundle = self._get_current_bundle()
        bundle.custom_secrets[key] = value
        await self._backend.set_secret(f"{self._current_env.value}_{key}", value)

    def mask_current_bundle(self) -> dict:
        bundle = self._get_current_bundle()
        return {
            "environment": bundle.environment.value,
            "broker_count": len(bundle.broker_credentials),
            "api_count": len(bundle.api_credentials),
            "custom_keys": list(bundle.custom_secrets.keys()),
            "brokers": [c.mask() for c in bundle.broker_credentials],
            "api_services": [c.mask() for c in bundle.api_credentials],
        }

    def is_bundle_loaded(self, env_type: EnvironmentType) -> bool:
        return env_type in self._bundles

    def _get_current_bundle(self) -> SecretBundle:
        if self._current_env is None or self._current_env not in self._bundles:
            raise RuntimeError(f"No secrets loaded for current environment ({self._current_env})")
        return self._bundles[self._current_env]

    async def _read_bundle(self, env_type: EnvironmentType) -> SecretBundle:
        bundle = SecretBundle(environment=env_type)

        broker_ids_raw = await self._backend.get_secret(f"{env_type.value}_BROKER_IDS")
        if broker_ids_raw:
            for broker_id in broker_ids_raw.split(","):
                broker_id = broker_id.strip()
                cred = BrokerCredentials(
                    broker_id=broker_id,
                    api_key=await self._backend.get_secret(f"{env_type.value}_{broker_id}_API_KEY") or "",
                    api_secret=await self._backend.get_secret(f"{env_type.value}_{broker_id}_API_SECRET") or "",
                    account_id=await self._backend.get_secret(f"{env_type.value}_{broker_id}_ACCOUNT_ID") or "",
                    paper_api_key=await self._backend.get_secret(f"{env_type.value}_{broker_id}_PAPER_API_KEY") or "",
                    paper_api_secret=await self._backend.get_secret(f"{env_type.value}_{broker_id}_PAPER_API_SECRET") or "",
                )
                bundle.broker_credentials.append(cred)

        service_ids_raw = await self._backend.get_secret(f"{env_type.value}_API_SERVICES")
        if service_ids_raw:
            for service_name in service_ids_raw.split(","):
                service_name = service_name.strip()
                cred = ApiCredentials(
                    service_name=service_name,
                    api_key=await self._backend.get_secret(f"{env_type.value}_{service_name}_API_KEY") or "",
                    api_secret=await self._backend.get_secret(f"{env_type.value}_{service_name}_API_SECRET") or "",
                    endpoint=await self._backend.get_secret(f"{env_type.value}_{service_name}_ENDPOINT") or "",
                )
                bundle.api_credentials.append(cred)

        return bundle
