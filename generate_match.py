#!/usr/bin/env python3
"""Create deterministic, synthetic football match events for MatchLens.

No network, accounts, paid services, or third-party packages are needed.
Run: python generate_match.py --seed 77 --output match_events.json
"""
import argparse
import json
import random
from datetime import datetime, timezone
from pathlib import Path

HOME = {"id": "blue-lions", "name": "Blue Lions", "short": "BLU"}
AWAY = {"id": "red-hawks", "name": "Red Hawks", "short": "RED"}
HOME_PLAYERS = ["M. Dlamini", "K. Mokoena", "L. Naidoo", "T. Williams", "S. Jacobs"]
AWAY_PLAYERS = ["A. Ndlovu", "P. Botha", "J. Mthembu", "R. Petersen", "C. Adams"]


def event(event_id, minute, team, kind, player, **extra):
    item = {
        "id": event_id,
        "minute": minute,
        "team": team["id"],
        "team_name": team["name"],
        "type": kind,
        "player": player,
        "synthetic": True,
    }
    item.update(extra)
    return item


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=77)
    parser.add_argument("--output", default="match_events.json")
    args = parser.parse_args()
    rng = random.Random(args.seed)
    events, event_id = [], 1

    # A deterministic narrative: early home control, away counter, late comeback.
    scripted = [
        (6, HOME, "pass", "M. Dlamini", {"recipient": "K. Mokoena", "distance_m": 23, "successful": True}),
        (12, HOME, "shot", "K. Mokoena", {"xg": 0.18, "on_target": True}),
        (19, AWAY, "tackle", "P. Botha", {"successful": True}),
        (28, HOME, "goal", "L. Naidoo", {"xg": 0.41, "assist": "K. Mokoena"}),
        (37, AWAY, "shot", "A. Ndlovu", {"xg": 0.09, "on_target": False}),
        (52, AWAY, "goal", "A. Ndlovu", {"xg": 0.24, "assist": "J. Mthembu"}),
        (63, HOME, "yellow_card", "T. Williams", {"reason": "late challenge"}),
        (71, HOME, "substitution", "S. Jacobs", {"on_for": "T. Williams"}),
        (79, HOME, "shot", "S. Jacobs", {"xg": 0.35, "on_target": True}),
        (82, HOME, "goal", "S. Jacobs", {"xg": 0.35, "assist": "M. Dlamini"}),
        (90, AWAY, "shot", "C. Adams", {"xg": 0.12, "on_target": False}),
    ]
    for minute, team, kind, player, data in scripted:
        events.append(event(event_id, minute, team, kind, player, **data)); event_id += 1

    # Extra synthetic actions make the stream feel match-like without pretending it is real data.
    for minute in sorted(rng.sample([m for m in range(1, 90) if m not in {6,12,19,28,37,52,63,71,79,82}], 28)):
        team = HOME if rng.random() < 0.53 else AWAY
        players = HOME_PLAYERS if team is HOME else AWAY_PLAYERS
        kind = rng.choices(["pass", "pressure", "tackle", "possession_change", "shot"], [48, 18, 15, 14, 5])[0]
        data = {}
        if kind == "pass": data = {"recipient": rng.choice(players), "distance_m": rng.randint(5, 42), "successful": rng.random() < .82}
        if kind == "tackle": data = {"successful": rng.random() < .64}
        if kind == "shot": data = {"xg": round(rng.uniform(.02, .16), 2), "on_target": rng.random() < .37}
        events.append(event(event_id, minute, team, kind, rng.choice(players), **data)); event_id += 1
    events.sort(key=lambda item: (item["minute"], item["id"]))

    document = {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "disclaimer": "Entirely synthetic, football-realistic demo data. Not match footage or licensed match-event data.",
        "match": {"home": HOME, "away": AWAY, "competition": "MatchLens synthetic showcase", "duration_minutes": 90},
        "events": events,
    }
    Path(args.output).write_text(json.dumps(document, indent=2), encoding="utf-8")
    print(f"Wrote {len(events)} synthetic events to {args.output} (seed={args.seed}).")


if __name__ == "__main__":
    main()
