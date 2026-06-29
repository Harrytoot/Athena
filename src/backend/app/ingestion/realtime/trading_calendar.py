from datetime import datetime, time, timedelta, timezone

BEIJING_TZ = timezone(timedelta(hours=8))

_MORNING_OPEN = time(9, 30, 0)
_MORNING_CLOSE = time(11, 30, 0)
_AFTERNOON_OPEN = time(13, 0, 0)
_AFTERNOON_CLOSE = time(15, 0, 0)
_PRE_MARKET_START = time(9, 15, 0)


class TradingCalendar:

    def __init__(self, tz: timezone = BEIJING_TZ):
        self._tz = tz

    @staticmethod
    def is_weekday(dt: datetime) -> bool:
        return dt.weekday() < 5

    def is_trading_session(self, now: datetime | None = None) -> bool:
        dt = self._as_beijing(now)
        if not self.is_weekday(dt):
            return False
        t = dt.time()
        return (_MORNING_OPEN <= t < _MORNING_CLOSE) or (_AFTERNOON_OPEN <= t < _AFTERNOON_CLOSE)

    def session_phase(self, now: datetime | None = None) -> str:
        dt = self._as_beijing(now)
        if not self.is_weekday(dt):
            return "closed"

        t = dt.time()
        if t < _PRE_MARKET_START:
            return "pre_market"
        if _PRE_MARKET_START <= t < _MORNING_OPEN:
            return "pre_market"
        if _MORNING_OPEN <= t < _MORNING_CLOSE:
            return "open_morning"
        if _MORNING_CLOSE <= t < _AFTERNOON_OPEN:
            return "lunch_break"
        if _AFTERNOON_OPEN <= t < _AFTERNOON_CLOSE:
            return "open_afternoon"

        return "closed"

    def next_open_time(self, now: datetime | None = None) -> datetime:
        dt = self._as_beijing(now)
        phase = self.session_phase(dt)

        if phase == "pre_market":
            return dt.replace(hour=9, minute=30, second=0, microsecond=0)
        if phase == "open_morning":
            return dt
        if phase == "lunch_break":
            return dt.replace(hour=13, minute=0, second=0, microsecond=0)
        if phase == "open_afternoon":
            return dt

        next_day = dt + timedelta(days=1)
        while not self.is_weekday(next_day):
            next_day += timedelta(days=1)
        return next_day.replace(hour=9, minute=30, second=0, microsecond=0)

    def session_duration_minutes(self) -> int:
        return 240

    def _as_beijing(self, dt: datetime | None) -> datetime:
        if dt is None:
            return datetime.now(self._tz)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=self._tz)
        return dt.astimezone(self._tz)
