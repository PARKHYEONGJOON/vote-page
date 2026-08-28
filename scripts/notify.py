#!/usr/bin/env python3
"""votes/ 변경 push 시 텔레그램으로 '새 투표 + 현황' 알림. (GitHub Actions에서 실행)"""
import json, os, subprocess, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
roster = json.loads((ROOT / "roster.json").read_text(encoding="utf-8"))
votes = {}
for p in sorted((ROOT / "votes").glob("*.json")):
    try:
        v = json.loads(p.read_text(encoding="utf-8"))
        votes[v["name"]] = v
    except Exception as e:  # noqa
        print("skip", p, e)

changed = subprocess.run(["git", "diff", "--name-only", "HEAD~1", "HEAD", "--", "votes/"],
                         capture_output=True, text=True, cwd=ROOT).stdout.split()
new = [json.loads((ROOT / f).read_text(encoding="utf-8")) for f in changed if (ROOT / f).exists()]

members = roster["members"]
answered = [m for m in members if m in votes]
pending = [m for m in members if m not in votes]
extra = [n for n in votes if n not in members]

lines = []
for v in new:
    lines.append(f"🗳 {v['name']} — {', '.join(v.get('picks', []))}")
    if v.get("memo"):
        lines.append(f"메모: {v['memo']}")
lines.append("")
lines.append(f"응답 {len(answered)}/{len(members)}" + (f" · 미응답: {', '.join(pending)}" if pending else " · 전원 응답 ✅"))
if extra:
    lines.append(f"명단 외 응답: {', '.join(extra)}")
counts = {s: sum(s in v.get("picks", []) for v in votes.values()) for s in roster["slots"]}
lines.append("가능 인원: " + " · ".join(f"{s} {c}명" for s, c in counts.items()))
lines.append("현황판: https://parkhyeongjoon.github.io/vote-page/status.html")
text = "\n".join(lines)
print(text)

tok, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
if not (tok and chat):
    raise SystemExit("no telegram secrets")
data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
with urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/sendMessage", data, timeout=20) as r:
    print(r.status)
