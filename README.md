# MatchLens: evidence-backed football intelligence

A local, reproducible prototype for the Microsoft x Premier League **Inside the Game** hackathon.

> **Pitch:** MatchLens turns a stream of synthetic football events into evidence-backed turning-point explanations. Casual fans get a clear story; analysts get the linked events and match context behind it.

## What works now

- **Ingest:** ordered synthetic football events in JSON.
- **Data innovation:** seeded generation recreates the same football event sequence.
- **Interpret:** deterministic rules identify a super-sub impact and decisive goal without guessing.
- **Explainability:** every insight records its rule and event IDs; the dashboard links those IDs to inspectable rows.
- **Personalization:** a Fan/Analyst toggle changes the wording for the same grounded insight.
- **Render:** a zero-dependency local replay dashboard showing timeline, score, xG and evidence-linked cards.
- **Safe demo data:** no accounts, APIs, Azure resources, third-party packages, real match data or footage are used by this local build.

## Run locally

Requires Python 3.10+ only.

```bash
python generate_match.py --seed 77 --output match_events.json
python detect_insights.py --events match_events.json --output match_insights.json
python replay_dashboard.py --events match_events.json --insights match_insights.json
```

Open `http://127.0.0.1:8000` in a browser. To stop the server, press `Ctrl+C` in the window running it.

## Verify the reproducible demo

```bash
python verify_demo.py
```

The offline check generates seed `77`, validates the synthetic data, validates the two expected evidence-linked insights, and renders the dashboard HTML. A successful check prints one `PASS` line.

## Evidence contract

`detect_insights.py` creates `match_insights.json`. Every insight carries only the event IDs needed to support its claim:

```json
{
  "kind": "SUPER_SUB",
  "headline": "S. Jacobs scored 11 minutes after entering for Blue Lions.",
  "evidence_event_ids": [8, 9, 10],
  "audience_copy": {
    "fan": "Super-sub S. Jacobs changed it for Blue Lions.",
    "analyst": "S. Jacobs entered at 71', put a 0.35 xG shot on target at 79', then scored at 82'."
  },
  "rule": "substitute_goal_with_on_target_shot_within_15_minutes"
}
```

Current deterministic rules:

- **SUPER_SUB:** a substitute makes an on-target shot and scores for the same team within 15 minutes of entering.
- **DECISIVE_GOAL:** a goal changes a draw into a one-goal lead and the opposition does not score later in the event stream.

The project deliberately does not call a goal a comeback unless the data proves the team had been behind.

## Two-minute demo

A timed, record-ready walkthrough is in [`DEMO_SCRIPT.md`](DEMO_SCRIPT.md). It demonstrates the functioning product, evidence links and the Fan/Analyst difference in about 1:55.

## Honest submission status

This local prototype demonstrates the five-stage football pipeline, synthetic data, explainability and audience-specific rendering. It **does not yet integrate Microsoft Foundry or Azure**. Do not describe Microsoft/Azure services as used until they are genuinely connected and shown in the demo.

Before submitting, the official rules require:

- a newly built project that meets the challenge;
- an elevator pitch describing the project and the Microsoft/Azure technologies actually used;
- a public demo video under two minutes, showing the project working, with a public YouTube, Vimeo, Facebook Video or Youku URL;
- a **public** GitHub repository URL;
- free judge access to a working website, demo or test build through the judging period; and
- English submission materials, original work and properly licensed assets only.

Source: [Microsoft’s Inside the Game Official Rules](https://github.com/microsoft/insidethegamehackathon/blob/main/OFFICIAL%20RULES.md).

## Suggested next build step

Once the Innovation Studio sign-in problem is resolved, add one genuinely Foundry-backed explanation path with the current deterministic output as its cited context and a safe local fallback. Then document the exact model/service, deployment instructions and privacy boundary. That is the smallest credible move toward the Microsoft-platform and agentic-design judging criteria without compromising this reproducible local demo.
