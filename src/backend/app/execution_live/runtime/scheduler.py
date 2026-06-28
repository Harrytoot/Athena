from dataclasses import dataclass, field
from datetime import datetime, time, timezone
from enum import Enum


class ScheduleCycle(str, Enum):
    DAILY = "daily"
    INTRADAY = "intraday"
    CONTINUOUS = "continuous"
    MANUAL = "manual"


@dataclass
class ScheduleConfig:
    cycle: ScheduleCycle = ScheduleCycle.INTRADAY
    interval_seconds: int = 300
    trading_start: time = time(9, 30)
    trading_end: time = time(15, 0)
    lunch_start: time | None = time(11, 30)
    lunch_end: time | None = time(13, 0)
    max_cycles_per_day: int = 1000
    skip_weekends: bool = True
    timezone_name: str = "Asia/Shanghai"


@dataclass
class ScheduleState:
    cycle_count: int = 0
    last_run: datetime | None = None
    next_run: datetime | None = None
    is_trading: bool = False
    is_lunch_break: bool = False
    paused: bool = False


class ExecutionScheduler:

    def __init__(self, config: ScheduleConfig | None = None):
        self.config = config or ScheduleConfig()
        self.state = ScheduleState()
        self._run_history: list[dict] = []

    def should_run(self, now: datetime | None = None) -> bool:
        if now is None:
            now = datetime.now(timezone.utc)

        if self.state.paused:
            return False

        if self.config.skip_weekends and now.weekday() >= 5:
            self.state.is_trading = False
            return False

        current_time = now.time()

        if current_time < self.config.trading_start or current_time > self.config.trading_end:
            self.state.is_trading = False
            return False

        if self.config.lunch_start and self.config.lunch_end:
            if self.config.lunch_start <= current_time <= self.config.lunch_end:
                self.state.is_lunch_break = True
                return False

        self.state.is_trading = True
        self.state.is_lunch_break = False

        if self.config.cycle == ScheduleCycle.MANUAL:
            return False

        if self.config.cycle == ScheduleCycle.CONTINUOUS:
            return True

        if self.state.last_run is None:
            return True

        elapsed = (now - self.state.last_run).total_seconds()
        if elapsed >= self.config.interval_seconds:
            return True

        return False

    def mark_run(self, now: datetime | None = None):
        if now is None:
            now = datetime.now(timezone.utc)

        self.state.last_run = now
        self.state.cycle_count += 1

        if self.config.cycle == ScheduleCycle.INTRADAY:
            import datetime as dt
            self.state.next_run = now + dt.timedelta(seconds=self.config.interval_seconds)

        entry = {
            "cycle": self.state.cycle_count,
            "timestamp": now.isoformat(),
            "is_trading": self.state.is_trading,
        }
        self._run_history.append(entry)

        if len(self._run_history) > 1000:
            self._run_history = self._run_history[-500:]

    def pause(self):
        self.state.paused = True

    def resume(self):
        self.state.paused = False

    def is_trading_hours(self, now: datetime | None = None) -> bool:
        if now is None:
            now = datetime.now(timezone.utc)

        if self.config.skip_weekends and now.weekday() >= 5:
            return False

        current_time = now.time()
        if current_time < self.config.trading_start or current_time > self.config.trading_end:
            return False

        if self.config.lunch_start and self.config.lunch_end:
            if self.config.lunch_start <= current_time <= self.config.lunch_end:
                return False

        return True

    def reset_daily(self):
        self.state.cycle_count = 0
        self.state.last_run = None
        self.state.next_run = None
        self._run_history.clear()

    @property
    def total_cycles(self) -> int:
        return self.state.cycle_count
