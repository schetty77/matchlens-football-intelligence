#!/usr/bin/env python3
"""Zero-dependency local replay dashboard for MatchLens.

Run after generating events and insights:
python replay_dashboard.py --events match_events.json --insights match_insights.json
Then open http://127.0.0.1:8000 in your browser.
"""
import argparse
import html
import json
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


def insight_cards(insights):
    if not insights:
        return "<p class='empty'>No insight file loaded yet. Run <code>detect_insights.py</code> first.</p>"
    cards = []
    for item in insights:
        evidence = " ".join(
            f"<a href='#event-{event_id}'>Event {event_id}</a>"
            for event_id in item["evidence_event_ids"]
        )
        fan = html.escape(item["audience_copy"]["fan"])
        analyst = html.escape(item["audience_copy"]["analyst"])
        headline = html.escape(item["headline"])
        kind = html.escape(item["kind"].replace("_", " ").title())
        cards.append(f"""<article class='insight'>
          <p class='label'>{kind} · deterministic rule</p><h3>{headline}</h3>
          <p class='audience-copy' data-fan='{fan}' data-analyst='{analyst}'><strong>Fan:</strong> {fan}</p>
          <p class='evidence-links'><strong>Linked evidence:</strong> {evidence}</p>
        </article>""")
    return "".join(cards)


def dashboard(doc, insight_doc=None):
    match, events = doc["match"], doc["events"]
    home, away = match["home"], match["away"]
    score = {home["id"]: 0, away["id"]: 0}
    xg = defaultdict(float)
    rows = []
    for event in events:
        if event["type"] in {"shot", "goal"}:
            xg[event["team"]] += float(event.get("xg", 0))
        if event["type"] == "goal":
            score[event["team"]] += 1
        important = "important" if event["type"] in {"goal", "shot", "yellow_card", "substitution"} else ""
        detail = []
        for key in ("xg", "assist", "recipient", "distance_m", "successful", "on_target", "on_for", "reason"):
            if key in event:
                detail.append(f"{key.replace('_', ' ')}: {event[key]}")
        rows.append(
            f"<tr id='event-{event['id']}' class='{important}'><td>{event['id']}</td><td>{event['minute']}'</td>"
            f"<td>{html.escape(event['team_name'])}</td><td>{html.escape(event['type'].replace('_', ' '))}</td>"
            f"<td>{html.escape(event['player'])}</td><td>{html.escape('; '.join(detail))}</td></tr>"
        )
    final = f"{home['name']} {score[home['id']]}–{score[away['id']]} {away['name']}"
    xg_line = f"xG: {xg[home['id']]:.2f} – {xg[away['id']]:.2f}"
    data = html.escape(json.dumps(doc, indent=2))
    insights = insight_doc.get("insights", []) if insight_doc else []
    return f"""<!doctype html><html><head><meta charset='utf-8'><title>MatchLens replay</title><style>
body{{font-family:system-ui,sans-serif;max-width:1100px;margin:28px auto;padding:0 16px;background:#f6f8fb;color:#16202a}}h1{{margin-bottom:0}}.notice{{background:#e8f2ff;border-left:4px solid #2979ff;padding:12px}}.score{{font-size:30px;font-weight:700;margin:12px 0 0}}.mode-switch{{display:flex;gap:8px;align-items:center;margin-top:18px}}button{{border:1px solid #3564a7;border-radius:18px;background:#fff;color:#234b84;padding:7px 12px;font-weight:700;cursor:pointer}}button[aria-pressed='true']{{background:#234b84;color:#fff}}.insight-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(290px,1fr));gap:14px;margin-top:12px}}.insight{{background:#fff;border:1px solid #dbe4f0;border-radius:10px;padding:14px}}.insight h3{{margin:4px 0 10px}}.label{{font-size:12px;font-weight:700;color:#3564a7;margin:0;text-transform:uppercase}}.evidence-links a{{margin-right:8px}}.empty{{background:#fff8dd;padding:12px}}table{{width:100%;border-collapse:collapse;background:white;margin-top:18px}}td,th{{padding:9px;border-bottom:1px solid #e5e7eb;text-align:left;font-size:14px}}.important{{background:#fff8dd}}tr:target{{outline:3px solid #2979ff}}details{{margin-top:18px}}code{{white-space:pre-wrap}}</style></head><body>
<h1>MatchLens replay dashboard</h1><p class='notice'>{html.escape(doc['disclaimer'])}</p><p class='score'>{final}</p><p>{xg_line} · Seed {doc['seed']} · {len(events)} events</p>
<p>Replay is ordered, inspectable and reproducible: the same seed recreates the same football event sequence.</p>
<h2>Evidence-linked insights</h2><div class='mode-switch' aria-label='Audience mode'><span>View for:</span><button id='fan-mode' aria-pressed='true'>Fan</button><button id='analyst-mode' aria-pressed='false'>Analyst</button></div><div class='insight-grid'>{insight_cards(insights)}</div>
<table><thead><tr><th>ID</th><th>Min</th><th>Team</th><th>Event</th><th>Player</th><th>Evidence</th></tr></thead><tbody>{''.join(rows)}</tbody></table>
<details><summary>Show raw event data</summary><code>{data}</code></details>
<script>const buttons={{fan:document.getElementById('fan-mode'),analyst:document.getElementById('analyst-mode')}};function setAudience(mode){{document.querySelectorAll('.audience-copy').forEach(p=>{{p.innerHTML='<strong>'+ (mode==='fan'?'Fan':'Analyst') +':</strong> '+p.dataset[mode];}});Object.entries(buttons).forEach(([name,button])=>button.setAttribute('aria-pressed',name===mode));}}buttons.fan.onclick=()=>setAudience('fan');buttons.analyst.onclick=()=>setAudience('analyst');</script>
</body></html>"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--events", default="match_events.json")
    parser.add_argument("--insights", default="match_insights.json")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    doc = json.loads(Path(args.events).read_text(encoding="utf-8"))
    insight_path = Path(args.insights)
    insight_doc = json.loads(insight_path.read_text(encoding="utf-8")) if insight_path.exists() else None
    page = dashboard(doc, insight_doc).encode()

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(page)

        def log_message(self, *args):
            pass

    print(f"Open http://127.0.0.1:{args.port} — serving {len(doc['events'])} deterministic synthetic events and {len(insight_doc.get('insights', [])) if insight_doc else 0} insights.")
    HTTPServer(("127.0.0.1", args.port), Handler).serve_forever()


if __name__ == "__main__":
    main()
