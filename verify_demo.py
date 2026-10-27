#!/usr/bin/env python3
"""Offline checks for the reproducible MatchLens demo."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(*args):
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=True)


def main():
    with tempfile.TemporaryDirectory() as directory:
        work = Path(directory)
        events_path = work / "events.json"
        insights_path = work / "insights.json"
        run(sys.executable, "generate_match.py", "--seed", "77", "--output", str(events_path))
        run(sys.executable, "detect_insights.py", "--events", str(events_path), "--output", str(insights_path))
        events = json.loads(events_path.read_text(encoding="utf-8"))
        insights = json.loads(insights_path.read_text(encoding="utf-8"))

    assert len(events["events"]) == 39, "Expected 39 events for seed 77"
    assert all(event["synthetic"] for event in events["events"]), "Every event must be synthetic"
    assert insights["synthetic"] is True, "Insight document must be synthetic"
    assert [item["kind"] for item in insights["insights"]] == ["SUPER_SUB", "DECISIVE_GOAL"]
    assert insights["insights"][0]["evidence_event_ids"] == [8, 9, 10]
    assert insights["insights"][1]["evidence_event_ids"] == [6, 10]

    from replay_dashboard import dashboard
    page = dashboard(events, insights)
    assert "Fan" in page and "Analyst" in page and "Linked evidence" in page
    assert "id='event-10'" in page
    print("PASS: seed 77 yields 39 synthetic events, 2 evidence-linked insights, and a renderable Fan/Analyst dashboard.")


if __name__ == "__main__":
    main()
