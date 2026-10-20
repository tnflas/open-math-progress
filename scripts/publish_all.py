"""Publish one coherent view of external and Issue-submitted research."""
import html
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
BASE = ROOT / "problems"
DATA = ROOT / "data"

from unify_index import main as build_unified

def read_json(path):
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))

def txt(s):
    s = str(s if s is not None else "")
    s = "".join(ch for ch in s if ch.isprintable())
    s = html.escape(s, quote=False)
    return s.replace("|", "&#124;")[:500]

def url(s):
    s = str(s or "").strip()
    parts = urlsplit(s)
    if parts.scheme not in ("https", "http") or not parts.netloc:
        return ""
    if any(ch.isspace() for ch in s) or "<" in s or ">" in s:
        return ""
    return s

def link(name, dest):
    u = url(dest)
    return f"[{txt(name)}](<{u}>)" if u else txt(name)

def markdown_file(path, content):
    path.write_text("\n".join(content) + "\n", encoding="utf-8")

def local_problems():
    results = {}
    for p in sorted(BASE.glob("**/metadata.json")):
        if "contributions" in p.parts:
            continue
        o = read_json(p)
        pid = o.get("id") or o.get("problem_id")
        if pid:
            results[pid] = (o, p.parent)
    return results

def local_contributions():
    results = []
    for p in sorted(BASE.glob("**/contributions/*/metadata.json")):
        o = read_json(p)
        if o.get("id") and o.get("problem_id"):
            results.append((o, p.parent))
    return results

def main():
    DOCS.mkdir(exist_ok=True)

    build_unified()

    external_p = read_json(DATA / "problems.json")
    external_c = read_json(DATA / "claims.json")
    local_p = local_problems()
    local_c = local_contributions()

    titles = {
        p["id"]: p.get("title", p["id"])
        for p in external_p if p.get("id")
    }
    titles.update({
        pid: obj.get("title", pid)
        for pid, (obj, _) in local_p.items()
    })

    # Preserve the existing source-derived content, then add Issue
    # submissions, without copying anything into external JSON data.
    index = [
        "# Mathematical Research Index", "",
        "**Source-reported and contributor-submitted research. "
        "OMP does not independently verify results.**", "",
        "## Community-Submitted Contributions", "",
        "| Problem | Contribution | Reported status | Manuscript |",
        "|---|---|---|---|",
    ]

    for c, folder in sorted(
        local_c,
        key=lambda item: (item[0].get("created_at") or "", item[0]["id"]),
        reverse=True,
    ):
        pid = c["problem_id"]
        relative = folder.relative_to(ROOT).as_posix()
        paper = c.get("manuscript_links") or ""
        paper_url = next(
            (part for part in re.findall(r"https?://[^\s<>)]+", paper)
             if url(part)),
            "",
        )
        index.append(
            f"| {txt(titles.get(pid, pid))} (`{txt(pid)}`) "
            f"| [{txt(c.get('title'))}](../{relative}/README.md) "
            f"| {txt(c.get('reported_status', 'research_report'))} "
            f"| {link('Manuscript', paper_url) if paper_url else link('Submission', c.get('issue_url'))} |"
        )

    if not local_c:
        index.append("| No submitted contributions yet | — | — | — |")

    index.extend([
        "",
        "## External Source-Reported Claims", "",
        "| Problem | Reported outcome | Source status | Original source |",
        "|---|---|---|---|",
    ])

    for c in sorted(external_c, key=lambda x: (
        str(titles.get(x.get("problem_id"), "")).lower(),
        str(x.get("id", "")),
    )):
        src = c.get("source") or {}
        index.append(
            f"| {txt(titles.get(c.get('problem_id'), c.get('problem_id')))} "
            f"| {txt(c.get('reported_outcome') or 'Not specified')} "
            f"| {txt(src.get('reported_status', 'unknown'))} "
            f"| {link('Original', src.get('url'))} |"
        )

    if not external_c:
        index.append("| No external claims | — | — | — |")

    markdown_file(DOCS / "INDEX.md", index)

    # A single chronological feed combining both submission types.
    events = []

    for c in external_c:
        src = c.get("source") or {}
        for e in c.get("status_history", []):
            stamp = e.get("observed_at") or ""
            events.append((
                stamp,
                "External source",
                titles.get(c.get("problem_id"), "Unknown"),
                e.get("status", ""),
                src.get("url", ""),
            ))

    for pid, (p, _) in local_p.items():
        events.append((
            p.get("created_at") or "",
            "New problem registration",
            p.get("title", pid),
            "Not assessed",
            p.get("issue_url", ""),
        ))

    for c, _ in local_c:
        events.append((
            c.get("created_at") or "",
            "Research contribution",
            c.get("title", c["id"]),
            c.get("reported_status", "Not specified"),
            c.get("issue_url", ""),
        ))

    recent = [
        "# Recent Research Progress", "",
        "Publicly observed or submitted records, not verified results.", "",
    ]
    for stamp, kind, title, status, source in sorted(
        events, key=lambda x: x[0], reverse=True
    )[:100]:
        recent.append(
            f"- **{txt(stamp)}** — {txt(kind)}: "
            f"**{txt(title)}** — {txt(status)} "
            f"({link('source', source)})"
        )

    if not events:
        recent.append("No recorded updates yet.")

    markdown_file(DOCS / "RECENT_PROGRESS.md", recent)

    # Preconditions: all current research submissions must be visible.
    problems_text = (DOCS / "PROBLEMS.md").read_text(encoding="utf-8")
    contribution_text = (DOCS / "CONTRIBUTIONS.md").read_text(
        encoding="utf-8"
    )
    index_text = (DOCS / "INDEX.md").read_text(encoding="utf-8")
    recent_text = (DOCS / "RECENT_PROGRESS.md").read_text(encoding="utf-8")

    for pid, (p, _) in local_p.items():
        if pid not in problems_text:
            raise AssertionError(f"Problem missing from index: {pid}")
        if p.get("title") not in index_text and not any(
            c.get("problem_id") == pid for c, _ in local_c
        ):
            # Registration appears in Problems and Recent even
            # without a research contribution.
            if p.get("title") not in recent_text:
                raise AssertionError(f"Problem not published: {pid}")

    for c, _ in local_c:
        title = txt(c.get("title"))
        if title not in contribution_text or title not in index_text:
            raise AssertionError(f"Contribution not published: {c['id']}")
        if title not in recent_text and len(events) <= 100:
            raise AssertionError(f"Contribution absent from recent feed: {c['id']}")

    from chronological_indexes import main as publish_utc_indexes
    publish_utc_indexes()

    print(
        f"PUBLISHED problems={len(titles)} "
        f"external_claims={len(external_c)} "
        f"local_contributions={len(local_c)}"
    )

if __name__ == "__main__":
    main()
