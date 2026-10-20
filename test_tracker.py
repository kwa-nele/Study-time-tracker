from datetime import date, datetime, timedelta
import pytest
from tracker import (add_manual, format_minutes, start_session, stop_session,
                     weekly_summary, load_data, save_data)


def fresh():
    return {"active": None, "sessions": []}


def test_start_then_stop_logs_minutes():
    data = fresh()
    t0 = datetime(2026, 10, 14, 9, 0)
    start_session(data, "Maths", t0)
    session = stop_session(data, t0 + timedelta(minutes=45))
    assert session["minutes"] == 45
    assert data["active"] is None
    assert len(data["sessions"]) == 1


def test_cannot_start_twice():
    data = fresh()
    start_session(data, "Maths", datetime.now())
    with pytest.raises(ValueError):
        start_session(data, "Coding", datetime.now())


def test_cannot_stop_without_start():
    with pytest.raises(ValueError):
        stop_session(fresh(), datetime.now())


def test_add_manual_rejects_zero_minutes():
    with pytest.raises(ValueError):
        add_manual(fresh(), "Maths", 0, date.today())


def test_weekly_summary_only_counts_current_week():
    data = fresh()
    wed = date(2026, 10, 14)          # a Wednesday
    add_manual(data, "Maths", 60, wed)
    add_manual(data, "Coding", 30, wed - timedelta(days=1))
    add_manual(data, "Maths", 999, wed - timedelta(days=10))   # last week, ignored
    r = weekly_summary(data, wed)
    assert r["total"] == 90
    assert r["subjects"] == {"Maths": 60, "Coding": 30}


@pytest.mark.parametrize("mins, text", [(5, "5m"), (60, "1h"), (95, "1h 35m")])
def test_format_minutes(mins, text):
    assert format_minutes(mins) == text


def test_save_and_load_roundtrip(tmp_path):
    f = tmp_path / "data.json"
    data = fresh()
    add_manual(data, "Maths", 20, date(2026, 10, 14))
    save_data(f, data)
    assert load_data(f) == data