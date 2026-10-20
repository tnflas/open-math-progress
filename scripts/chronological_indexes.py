"""Generate UTC-dated, newest-first public research indexes."""
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs"
BASE = ROOT / "problems"

def read(path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))

def parse_time(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        raw = value.strip()
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        t = datetime.fromisoformat(raw)
        if t.tzinfo is None:
            return None
        return t.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        return None

def fmt(t):
    return t.strftime("%Y-%m-%d %H:%M:%S") if t else "Unknown"

def sort_key(item):
    t = item.get("time")
    return (
        t is not None,
        t or datetime.min.replace(tzinfo=timezone.utc),
        item.get("id", ""),
    )

def esc(value):
    s = str(value if value is not None else "")
    s = html.escape(s, quote=False)
    return s.replace("|", "&#124;").replace("\n", " ").replace("\r", " ")[:700]

def safe_url(value):
    s = str(value or "").strip()
    u = urlsplit(s)
    if u.scheme not in ("http", "https") or not u.netloc:
        return ""
    if any(c.isspace() for c in s) or "<" in s or ">" in s:
        return ""
    return s

def link(label, address):
    address = safe_url(address)
    if not address:
        return esc(label)
    return f"[{esc(label)}](<{address}>)"

def output(name, lines):
    DOCS.mkdir(exist_ok=True)
    path = DOCS / name
    content = "\n".join(lines).rstrip() + "\n"
    if not path.exists() or path.read_text(encoding="utf-8") != content:
        path.write_text(content, encoding="utf-8")

def main():
    raw_problems = read(DATA / "problems.json", [])
    raw_claims = read(DATA / "claims.json", [])
    raw_notices = read(DATA / "notices.json", [])

    local_problems = {}
    local_contributions = []

    for path in sorted(BASE.glob("**/metadata.json")):
        obj = read(path, {})
        if not isinstance(obj, dict):
            continue
        if "contributions" in path.parts:
            if obj.get("id") and obj.get("problem_id"):
                local_contributions.append((obj, path.parent))
        else:
            pid = obj.get("id") or obj.get("problem_id")
            if pid:
                local_problems[pid] = (obj, path.parent)

    titles = {
        p["id"]: p.get("title", p["id"])
        for p in raw_problems if p.get("id")
    }
    titles.update({
        pid: obj.get("title", pid)
        for pid, (obj, _) in local_problems.items()
    })

    # External records only have first-observed timestamps.
    # Do not treat these as source publication dates.
    first_seen = {}
    contributions = []
    events = []

    for claim in raw_claims:
        pid = claim.get("problem_id")
        source = claim.get("source") or {}
        t = parse_time(source.get("first_observed"))
        if t and (pid not in first_seen or t < first_seen[pid]):
            first_seen[pid] = t

        item = {
            "id": claim.get("id", ""),
            "problem": titles.get(pid, pid or "Unknown"),
            "title": claim.get("reported_outcome") or "Source-reported result",
            "status": source.get("reported_status", "unknown"),
            "source": source.get("url"),
            "time": t,
            "kind": "First observed",
            "type": "external",
        }
        contributions.append(item)

        history = claim.get("status_history") or []
        for event in history:
            et = parse_time(event.get("observed_at"))
            if et:
                events.append({
                    "id": claim.get("id", ""),
                    "time": et,
                    "type": "External status observation",
                    "title": item["problem"],
                    "status": event.get("status", ""),
                    "source": item["source"],
                })

    problems = []
    for p in raw_problems:
        pid = p.get("id")
        if pid:
            problems.append({
                "id": pid,
                "title": titles.get(pid, pid),
                "time": first_seen.get(pid),
                "kind": "First indexed",
                "source": None,
                "local_path": None,
            })

    local_ids = set(local_problems)

    for pid, (p, folder) in local_problems.items():
        t = parse_time(p.get("created_at"))
        if pid in {x["id"] for x in problems}:
            problems = [x for x in problems if x["id"] != pid]
        problems.append({
            "id": pid,
            "title": titles.get(pid, pid),
            "time": t,
            "kind": "Submitted",
            "source": p.get("issue_url"),
            "local_path": folder,
        })
        if t:
            events.append({
                "id": pid,
                "time": t,
                "type": "Problem registration",
                "title": titles.get(pid, pid),
                "status": "Not assessed",
                "source": p.get("issue_url"),
            })

    for obj, folder in local_contributions:
        pid = obj["problem_id"]
        t = parse_time(obj.get("created_at"))
        item = {
            "id": obj["id"],
            "problem": titles.get(pid, pid),
            "title": obj.get("title", obj["id"]),
            "status": obj.get("reported_status", "Not specified"),
            "source": obj.get("issue_url"),
            "time": t,
            "kind": "Submitted",
            "type": "local",
            "local_path": folder,
        }
        contributions.append(item)
        if t:
            events.append({
                "id": obj["id"],
                "time": t,
                "type": "Research contribution",
                "title": obj.get("title", obj["id"]),
                "status": item["status"],
                "source": obj.get("issue_url"),
            })

    problems.sort(key=sort_key, reverse=True)
    contributions.sort(key=sort_key, reverse=True)
    events.sort(key=sort_key, reverse=True)

    problem_lines = [
        "# Mathematical Problems", "",
        "Newest submissions and first observations appear first.",
        "All timestamps are UTC.", "",
        "**Submitted** means a GitHub contribution was filed.",
        "**First indexed** means OMP first observed an external record;",
        "it is not the mathematical problem's original publication date.",
        "", "| Time (UTC) | Type | Problem ID | Mathematical problem | Record |",
        "|---|---|---|---|---|",
    ]

    for p in problems:
        pid = p["id"]
        if p["local_path"]:
            rel = p["local_path"].relative_to(ROOT).as_posix()
            record = f"[Problem page](../{rel}/README.md)"
        else:
            record = "Indexed record"
        problem_lines.append(
            f"| {fmt(p['time'])} | {p['kind']} | `{esc(pid)}` "
            f"| {esc(p['title'])} | {record} |"
        )

    if not problems:
        problem_lines.append("| — | — | — | No problems yet | — |")
    output("PROBLEMS.md", problem_lines)

    contribution_lines = [
        "# Research Contributions", "",
        "Newest submissions and first observations appear first.",
        "All timestamps are UTC.", "",
        "External timestamps are **first observed by OMP**, not",
        "necessarily paper submission or publication dates.", "",
        "| Time (UTC) | Time type | Problem | Contribution | Status | Source |",
        "|---|---|---|---|---|---|",
    ]

    for c in contributions:
        name = esc(c["title"])
        if c["type"] == "local":
            rel = c["local_path"].relative_to(ROOT).as_posix()
            name = f"[{name}](../{rel}/README.md)"
        contribution_lines.append(
            f"| {fmt(c['time'])} | {c['kind']} "
            f"| {esc(c['problem'])} | {name} "
            f"| {esc(c['status'])} "
            f"| {link('Original record', c['source'])} |"
        )
    if not contributions:
        contribution_lines.append("| — | — | — | None yet | — | — |")
    output("CONTRIBUTIONS.md", contribution_lines)

    index = [
        "# Mathematical Research Index", "",
        "All records are source-reported or contributor-submitted,",
        "not independently verified by OMP.", "",
        "Ordered newest first by submitted or first-observed UTC time.",
        "First observed is not the same as published.", "",
        "| Time (UTC) | Time type | Problem | Research result | Reported status | Source |",
        "|---|---|---|---|---|---|",
    ]
    for c in contributions:
        name = esc(c["title"])
        if c["type"] == "local":
            rel = c["local_path"].relative_to(ROOT).as_posix()
            name = f"[{name}](../{rel}/README.md)"
        index.append(
            f"| {fmt(c['time'])} | {c['kind']} "
            f"| {esc(c['problem'])} | {name} "
            f"| {esc(c['status'])} | {link('Source', c['source'])} |"
        )
    if not contributions:
        index.append("| — | — | — | No records yet | — | — |")
    output("INDEX.md", index)

    recent = [
        "# Recent Research Progress", "",
        "Most recent 100 recorded events, newest first.",
        "All timestamps are UTC. An observation is not a",
        "mathematical verification or a publication event.", "",
        "| Event time (UTC) | Event | Problem or contribution | Status | Source |",
        "|---|---|---|---|---|",
    ]
    for e in events[:100]:
        recent.append(
            f"| {fmt(e['time'])} | {esc(e['type'])} "
            f"| {esc(e['title'])} | {esc(e['status'])} "
            f"| {link('Original', e['source'])} |"
        )
    if not events:
        recent.append("| — | — | No events yet | — | — |")
    output("RECENT_PROGRESS.md", recent)

    notices = [
        "# Public Research Notices", "",
        "Unreviewed public notices; newest first, UTC.", "",
        "| Submitted (UTC) | Notice | Category | Source |",
        "|---|---|---|---|",
    ]
    for n in sorted(
        raw_notices,
        key=lambda x: sort_key({
            "time": parse_time(x.get("created_at")),
            "id": x.get("id", ""),
        }),
        reverse=True,
    ):
        notices.append(
            f"| {fmt(parse_time(n.get('created_at')))} "
            f"| {esc(n.get('title', n.get('id', 'Notice')))} "
            f"| {esc(n.get('category', 'Other'))} "
            f"| {link('Discussion', n.get('url'))} |"
        )
    if len(notices) == 6:
        notices.append("| — | No notices yet | — | — |")
    output("PUBLIC_NOTICES.md", notices)

    # Assert the two known Ryser Issue records are not silently lost.
    for pid in ("OMP-U-1",):
        if pid in local_ids:
            assert pid in (DOCS / "PROBLEMS.md").read_text()
    if any(c[0].get("id") == "OMP-C-I-2" for c in local_contributions):
        assert any(
            c["id"] == "OMP-C-I-2" for c in contributions
        )

    print(
        f"UTC INDEX PASS: {len(problems)} problems, "
        f"{len(contributions)} contributions, "
        f"{len(events)} events, {len(raw_notices)} notices"
    )

if __name__ == "__main__":
    main()
