from dataclasses import dataclass
from enum import Enum
from typing import Optional
import logging
import os

logger = logging.getLogger(__name__)


class EnvironmentType(str, Enum):
    PAPER = "paper"
    LIVE = "live"
    SANDBOX = "sandbox"
    REPLAY = "replay"


@dataclass(frozen=True)
class EnvironmentConfig:
    env_type: EnvironmentType
    env_file: str
    db_suffix: str = ""
    redis_db: int = 0
    read_only: bool = False
    require_confirmation: bool = False
    max_position_size: Optional[float] = None
    allowed_markets: Optional[list[str]] = None

    @property
    def is_live(self) -> bool:
        return self.env_type == EnvironmentType.LIVE

    @property
    def is_paper(self) -> bool:
        return self.env_type == EnvironmentType.PAPER

    @property
    def is_sandbox(self) -> bool:
        return self.env_type == EnvironmentType.SANDBOX

    @property
    def is_replay(self) -> bool:
        return self.env_type == EnvironmentType.REPLAY


ENVIRONMENT_CONFIGS: dict[EnvironmentType, EnvironmentConfig] = {
    EnvironmentType.PAPER: EnvironmentConfig(
        env_type=EnvironmentType.PAPER,
        env_file=".env.paper",
        db_suffix="_paper",
        redis_db=0,
        read_only=False,
        max_position_size=100000.0,
    ),
    EnvironmentType.LIVE: EnvironmentConfig(
        env_type=EnvironmentType.LIVE,
        env_file=".env.production",
        db_suffix="_live",
        redis_db=1,
        read_only=False,
        require_confirmation=True,
    ),
    EnvironmentType.SANDBOX: EnvironmentConfig(
        env_type=EnvironmentType.SANDBOX,
        env_file=".env.sandbox",
        db_suffix="_sandbox",
        redis_db=2,
        read_only=True,
        max_position_size=10000.0,
    ),
    EnvironmentType.REPLAY: EnvironmentConfig(
        env_type=EnvironmentType.REPLAY,
        env_file=".env.replay",
        db_suffix="_replay",
        redis_db=3,
        read_only=True,
    ),
}


class EnvironmentSwitchError(Exception):
    pass


class EnvironmentSwitcher:
    def __init__(self) -> None:
        self._current: EnvironmentConfig = ENVIRONMENT_CONFIGS[EnvironmentType.PAPER]
        self._previous: Optional[EnvironmentConfig] = None
        self._switch_lock: bool = False

    @property
    def current(self) -> EnvironmentConfig:
        return self._current

    @property
    def current_type(self) -> EnvironmentType:
        return self._current.env_type

    def detect_from_env(self) -> EnvironmentConfig:
        env_name = os.getenv("ATHENA_ENV", "paper").lower()
        try:
            env_type = EnvironmentType(env_name)
        except ValueError:
            logger.warning("Unknown ATHENA_ENV=%s, defaulting to PAPER", env_name)
            env_type = EnvironmentType.PAPER

        self._current = ENVIRONMENT_CONFIGS[env_type]
        self._load_env_file(self._current.env_file)
        return self._current

    async def switch_to(self, target: EnvironmentType, force: bool = False) -> EnvironmentConfig:
        if self._switch_lock:
            raise EnvironmentSwitchError("Environment switch in progress")

        if target == self._current.env_type and not force:
            return self._current

        target_config = ENVIRONMENT_CONFIGS[target]

        if target_config.require_confirmation and not force:
            raise EnvironmentSwitchError(
                f"Switching to {target.value} requires explicit confirmation (force=True)"
            )

        if self._current.is_live and not force:
            raise EnvironmentSwitchError(
                "Switching away from LIVE requires explicit confirmation (force=True)"
            )

        self._switch_lock = True
        try:
            self._previous = self._current
            self._current = target_config
            self._load_env_file(target_config.env_file)
            logger.info(
                "Environment switched: %s -> %s",
                self._previous.env_type.value if self._previous else "none",
                self._current.env_type.value,
            )
            return self._current
        finally:
            self._switch_lock = False

    async def rollback(self) -> EnvironmentConfig:
        if self._previous is None:
            raise EnvironmentSwitchError("No previous environment to rollback to")

        logger.warning("Rolling back environment to %s", self._previous.env_type.value)
        previous = self._previous
        self._previous = self._current
        self._current = previous
        self._load_env_file(self._current.env_file)
        return self._current

    def can_switch_to(self, target: EnvironmentType) -> bool:
        if self._switch_lock:
            return False
        return True

    def _load_env_file(self, env_file: str) -> None:
        if os.path.isfile(env_file):
            with open(env_file, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, _, value = line.partition("=")
                        os.environ[key] = value.strip('"').strip("'")
