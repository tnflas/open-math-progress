"""VibeMath JSON Feed adapter. Records source claims only."""
import json
from collections import Counter
from urllib.request import Request, urlopen
from urllib.parse import urlsplit

BASE = "https://cyanseek.github.io/VibeMath/api/v1/"

STATUS_MAP = {
    "resolved": "claimed_solved",
    "partial": "partial_progress",
    "contested": "disputed",
    "retracted": "retracted",
}

def fetch(name):
    req = Request(
        BASE + name,
        headers={"User-Agent": "OpenMathProgress/1.0"}
    )
    with urlopen(req, timeout=40) as response:
        payload = json.load(response)
    records = payload.get("data")
    if not isinstance(records, list):
        raise ValueError(f"Invalid VibeMath {name} feed")
    return records

def clean_url(value):
    if not isinstance(value, str):
        return None
    value = value.strip()

    # Handle ordinary URLs and Markdown-formatted URLs.
    if value.startswith("[") and "](" in value:
        value = value.split("](", 1)[1].rstrip(")")

    parts = urlsplit(value)
    if parts.scheme != "https" or not parts.netloc:
        return None
    return value

def source_url(problem):
    sources = problem.get("canonical_sources") or []

    # Prefer the direct problem entry as the stable claim identity.
    for kind in ("source-assertion", "primary-mathematical-source"):
        for entry in sources:
            if entry.get("kind") == kind:
                url = clean_url(entry.get("url"))
                if url:
                    return url
    return None

def collect_vibemath(config, token=None):
    problems = fetch("problems.json")
    events = fetch("events.json")

    by_problem = {}
    for event in events:
        pid = event.get("problem_id")
        if pid:
            by_problem.setdefault(pid, []).append(event)

    results = []
    counts = Counter()
    seen_urls = set()

    for problem in problems:
        raw_status = problem.get("current_status")
        counts[f"status:{raw_status}"] += 1

        if raw_status not in STATUS_MAP:
            counts["skipped_status"] += 1
            continue

        pid = problem.get("id")
        associated = by_problem.get(pid, [])

        if not associated:
            counts["skipped_without_event"] += 1
            continue

        url = source_url(problem)
        if not url:
            counts["skipped_without_url"] += 1
            continue

        if url in seen_urls:
            counts["skipped_duplicate_url"] += 1
            continue
        seen_urls.add(url)

        title_obj = problem.get("title") or {}
        if isinstance(title_obj, dict):
            title = (
                title_obj.get("en")
                or title_obj.get("original")
                or problem.get("slug")
            )
        else:
            title = str(title_obj)

        if not title:
            counts["skipped_without_title"] += 1
            continue

        # Current status belongs to the mathematical problem.
        # Event type describes research activity, not complete solution.
        latest = sorted(
            associated,
            key=lambda e: e.get("occurred_at") or "",
        )[-1]

        ai_value = latest.get("ai_contribution")
        ai_reported = bool(
            ai_value and ai_value not in
            ("unknown", "none", "not_reported")
        )

        results.append({
            "title": title,
            "source_url": url,
            "repository": config["repo"],
            "status": STATUS_MAP[raw_status],
            "reported_outcome": latest.get("type") or raw_status,
            "reported_evidence": (
                "VibeMath source-reported problem status: "
                + raw_status
                + ". Event: "
                + str(latest.get("type") or "unknown")
                + ". OMP has not independently verified this result."
            ),
            "ai_involvement": (
                "reported" if ai_reported else "unknown"
            ),
            "source_updated_at": problem.get("updated_at"),
        })
        counts["imported"] += 1

    print(
        "VIBEMATH",
        f"problems={len(problems)}",
        f"events={len(events)}",
        f"imported={len(results)}",
    )
    print("VIBEMATH STATUS COUNTS:", dict(counts))

    return results
