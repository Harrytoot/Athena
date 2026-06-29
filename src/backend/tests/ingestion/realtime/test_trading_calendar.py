from datetime import datetime

import pytest

from app.ingestion.realtime.trading_calendar import (
    BEIJING_TZ,
    TradingCalendar,
)


class TestTradingCalendar:

    @pytest.fixture
    def calendar(self):
        return TradingCalendar()

    def test_morning_session_is_trading(self, calendar):
        dt = datetime(2026, 6, 29, 10, 0, 0, tzinfo=BEIJING_TZ)
        assert calendar.is_trading_session(dt) is True

    def test_afternoon_session_is_trading(self, calendar):
        dt = datetime(2026, 6, 29, 14, 0, 0, tzinfo=BEIJING_TZ)
        assert calendar.is_trading_session(dt) is True

    def test_before_open_not_trading(self, calendar):
        dt = datetime(2026, 6, 29, 9, 0, 0, tzinfo=BEIJING_TZ)
        assert calendar.is_trading_session(dt) is False

    def test_lunch_break_not_trading(self, calendar):
        dt = datetime(2026, 6, 29, 12, 0, 0, tzinfo=BEIJING_TZ)
        assert calendar.is_trading_session(dt) is False

    def test_after_close_not_trading(self, calendar):
        dt = datetime(2026, 6, 29, 15, 30, 0, tzinfo=BEIJING_TZ)
        assert calendar.is_trading_session(dt) is False

    def test_weekend_not_trading(self, calendar):
        dt = datetime(2026, 6, 27, 10, 0, 0, tzinfo=BEIJING_TZ)
        assert calendar.is_trading_session(dt) is False

    def test_session_phase_pre_market(self, calendar):
        dt = datetime(2026, 6, 29, 9, 20, 0, tzinfo=BEIJING_TZ)
        assert calendar.session_phase(dt) == "pre_market"

    def test_session_phase_open_morning(self, calendar):
        dt = datetime(2026, 6, 29, 10, 0, 0, tzinfo=BEIJING_TZ)
        assert calendar.session_phase(dt) == "open_morning"

    def test_session_phase_lunch_break(self, calendar):
        dt = datetime(2026, 6, 29, 12, 0, 0, tzinfo=BEIJING_TZ)
        assert calendar.session_phase(dt) == "lunch_break"

    def test_session_phase_open_afternoon(self, calendar):
        dt = datetime(2026, 6, 29, 14, 0, 0, tzinfo=BEIJING_TZ)
        assert calendar.session_phase(dt) == "open_afternoon"

    def test_session_phase_closed(self, calendar):
        dt = datetime(2026, 6, 29, 15, 30, 0, tzinfo=BEIJING_TZ)
        assert calendar.session_phase(dt) == "closed"

    def test_is_weekday_monday(self):
        monday = datetime(2026, 6, 29, tzinfo=BEIJING_TZ)
        assert TradingCalendar.is_weekday(monday) is True

    def test_is_weekday_saturday(self):
        saturday = datetime(2026, 6, 27, tzinfo=BEIJING_TZ)
        assert TradingCalendar.is_weekday(saturday) is False

    def test_next_open_time_from_morning(self, calendar):
        dt = datetime(2026, 6, 29, 10, 0, 0, tzinfo=BEIJING_TZ)
        next_open = calendar.next_open_time(dt)
        assert next_open.hour == 10
        assert next_open.minute == 0

    def test_next_open_time_from_lunch_break(self, calendar):
        dt = datetime(2026, 6, 29, 12, 0, 0, tzinfo=BEIJING_TZ)
        next_open = calendar.next_open_time(dt)
        assert next_open.hour == 13
        assert next_open.minute == 0

    def test_next_open_time_after_close(self, calendar):
        dt = datetime(2026, 6, 29, 16, 0, 0, tzinfo=BEIJING_TZ)
        next_open = calendar.next_open_time(dt)
        assert next_open.hour == 9
        assert next_open.minute == 30
        assert next_open.day > dt.day
        assert TradingCalendar.is_weekday(next_open)

    def test_session_duration(self, calendar):
        assert calendar.session_duration_minutes() == 240

    def test_market_open_exactly_at_start(self, calendar):
        dt = datetime(2026, 6, 29, 9, 30, 0, tzinfo=BEIJING_TZ)
        assert calendar.is_trading_session(dt) is True

    def test_market_closed_exactly_at_end(self, calendar):
        dt = datetime(2026, 6, 29, 11, 30, 0, tzinfo=BEIJING_TZ)
        assert calendar.is_trading_session(dt) is False
