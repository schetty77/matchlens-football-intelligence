#!/usr/bin/env python3
"""Detect evidence-linked football insights from MatchLens synthetic events.

No external services are used. Each insight is produced by a deterministic rule
and only cites the event IDs that support its claim.
"""
import argparse
import json
from pathlib import Path


def insight(kind, headline, evidence, fan, analyst, rule):
    return {
        "kind": kind,
        "headline": headline,
        "evidence_event_ids": [event["id"] for event in evidence],
        "evidence": [
            {
                "event_id": event["id"],
                "minute": event["minute"],
                "type": event["type"],
                "team": event["team_name"],
                "player": event["player"],
            }
            for event in evidence
        ],
        "audience_copy": {"fan": fan, "analyst": analyst},
        "rule": rule,
    }


def detect(doc):
    """Return ordered, reproducible insights for an ordered event document."""
    events = sorted(doc["events"], key=lambda event: (event["minute"], event["id"]))
    insights = []

    # A substitute's on-target shot and goal soon after entering is a clear,
    # evidence-bounded turning-point pattern.
    for substitute in (event for event in events if event["type"] == "substitution"):
        window = [
            event for event in events
            if substitute["minute"] < event["minute"] <= substitute["minute"] + 15
            and event["team"] == substitute["team"] and event["player"] == substitute["player"]
        ]
        shot = next((event for event in window if event["type"] == "shot" and event.get("on_target")), None)
        goal = next((event for event in window if event["type"] == "goal"), None)
        if shot and goal:
            name, team = substitute["player"], substitute["team_name"]
            minutes = goal["minute"] - substitute["minute"]
            insights.append(insight(
                "SUPER_SUB",
                f"{name} scored {minutes} minutes after entering for {team}.",
                [substitute, shot, goal],
                f"Super-sub {name} changed it for {team}.",
                f"{name} entered at {substitute['minute']}', put a {float(shot.get('xg', 0)):.2f} xG shot on target at {shot['minute']}', then scored at {goal['minute']}'.",
                "substitute_goal_with_on_target_shot_within_15_minutes",
            ))

    # Identify a final decisive goal: it changes a draw to a one-goal lead,
    # and the opposition does not score later. It is deliberately not labelled
    # a 'comeback' unless the data proves a team was trailing.
    teams = [doc["match"]["home"]["id"], doc["match"]["away"]["id"]]
    score = {team: 0 for team in teams}
    for index, event in enumerate(events):
        if event["type"] != "goal":
            continue
        before = dict(score)
        score[event["team"]] += 1
        other = next(team for team in teams if team != event["team"])
        later_opposition_goal = any(
            future["type"] == "goal" and future["team"] == other
            for future in events[index + 1:]
        )
        if before[event["team"]] == before[other] and score[event["team"]] == score[other] + 1 and not later_opposition_goal:
            prior_equaliser = next((
                previous for previous in reversed(events[:index])
                if previous["type"] == "goal" and previous["team"] == other
            ), None)
            evidence = [prior_equaliser, event] if prior_equaliser else [event]
            team, player = event["team_name"], event["player"]
            insights.append(insight(
                "DECISIVE_GOAL",
                f"{player}'s {event['minute']}' goal became {team}'s winner.",
                evidence,
                f"{player} found the winner for {team}.",
                f"After the score was levelled at {prior_equaliser['minute'] if prior_equaliser else '?'}', {player} scored at {event['minute']}' ({float(event.get('xg', 0)):.2f} xG); no later opposition goal appears in the event stream.",
                "draw_to_one_goal_lead_with_no_later_opposition_goal",
            ))
    return insights


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", default="match_events.json")
    parser.add_argument("--output", default="match_insights.json")
    args = parser.parse_args()
    doc = json.loads(Path(args.events).read_text(encoding="utf-8"))
    payload = {
        "schema_version": "1.0",
        "synthetic": bool(all(event.get("synthetic") for event in doc["events"])),
        "source_seed": doc["seed"],
        "disclaimer": "Insights are deterministic demonstrations over synthetic events, not claims about a real match.",
        "insights": detect(doc),
    }
    Path(args.output).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {len(payload['insights'])} evidence-linked insights to {args.output} (seed={doc['seed']}).")


if __name__ == "__main__":
    main()
