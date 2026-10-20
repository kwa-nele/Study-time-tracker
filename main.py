"""Study timer / habit tracker. Logs study sessions to a JSON file."""
import argparse
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

DEFAULT_FILE = Path(os.environ.get("STUDY_TRACKER_FILE", Path.home() / ".study_tracker.json"))


# ---------- storage ----------
def load_data(path: Path) -> dict:
    if not path.exists():
        return {"active": None, "sessions": []}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_data(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# ---------- core logic ----------
def start_session(data: dict, subject: str, now: datetime) -> None:
    if data["active"]:
        raise ValueError(f"A session for '{data['active']['subject']}' is already running.")
    data["active"] = {"subject": subject, "start": now.isoformat()}


def stop_session(data: dict, now: datetime) -> dict:
    if not data["active"]:
        raise ValueError("No session is running. Use 'start' first.")
    start = datetime.fromisoformat(data["active"]["start"])
    minutes = max(1, round((now - start).total_seconds() / 60))
    session = {
        "subject": data["active"]["subject"],
        "date": start.date().isoformat(),
        "minutes": minutes,
    }
    data["sessions"].append(session)
    data["active"] = None
    return session


def add_manual(data: dict, subject: str, minutes: int, day) -> dict:
    if minutes <= 0:
        raise ValueError("Minutes must be greater than 0.")
    session = {"subject": subject, "date": day.isoformat(), "minutes": minutes}
    data["sessions"].append(session)
    return session


def format_minutes(minutes: int) -> str:
    hours, mins = divmod(minutes, 60)
    if hours and mins:
        return f"{hours}h {mins}m"
    return f"{hours}h" if hours else f"{mins}m"


def weekly_summary(data: dict, today) -> dict:
    """Totals for the Monday-Sunday week containing `today`."""
    monday = today - timedelta(days=today.weekday())
    days = {(monday + timedelta(days=i)).isoformat(): 0 for i in range(7)}
    subjects: dict = {}
    for s in data["sessions"]:
        if s["date"] in days:
            days[s["date"]] += s["minutes"]
            subjects[s["subject"]] = subjects.get(s["subject"], 0) + s["minutes"]
    return {"days": days, "subjects": subjects, "total": sum(days.values())}


# ---------- command-line interface ----------
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Track your study sessions.")
    p.add_argument("--file", type=Path, default=DEFAULT_FILE, help="data file location")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("start", help="start a study session")
    s.add_argument("subject")
    sub.add_parser("stop", help="stop the running session")
    sub.add_parser("status", help="show the running session")
    a = sub.add_parser("add", help="log a past session manually")
    a.add_argument("subject")
    a.add_argument("minutes", type=int)
    sub.add_parser("summary", help="show this week's totals")
    return p


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)
    data = load_data(args.file)
    now = datetime.now()

    try:
        if args.command == "start":
            start_session(data, args.subject, now)
            print(f"Started studying {args.subject}. Run 'stop' when you're done.")
        elif args.command == "stop":
            s = stop_session(data, now)
            print(f"Logged {format_minutes(s['minutes'])} of {s['subject']}.")
        elif args.command == "add":
            s = add_manual(data, args.subject, args.minutes, now.date())
            print(f"Added {format_minutes(s['minutes'])} of {s['subject']}.")
        elif args.command == "status":
            a = data["active"]
            print(f"Studying {a['subject']} since {a['start'][11:16]}." if a else "No session running.")
        elif args.command == "summary":
            r = weekly_summary(data, now.date())
            print("This week:")
            for day, mins in r["days"].items():
                bar = "#" * (mins // 15)
                print(f"  {day}  {format_minutes(mins):>7}  {bar}")
            print(f"Total: {format_minutes(r['total'])}")
            for subj, mins in sorted(r["subjects"].items(), key=lambda x: -x[1]):
                print(f"  {subj}: {format_minutes(mins)}")
    except ValueError as e:
        print(f"Error: {e}")
        raise SystemExit(1)

    save_data(args.file, data)


if __name__ == "__main__":
    main()