"""Unified source and contributor indexes. No mathematical review."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs"
BASE = ROOT / "problems"

def records(path):
    if not path.exists():
        return []
    obj = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(obj, list):
        raise ValueError(f"Expected list in {path}")
    return obj

def field(value):
    text = str(value if value is not None else "")
    text = re.sub(r"<[^>]*>", "", text)
    text = text.replace("|", "&#124;")
    text = text.replace("\r", " ").replace("\n", " ")
    return text[:500]

def url(value):
    value = str(value or "").strip()
    if not value.startswith("https://"):
        return None
    if any(x in value for x in ["\n", "\r", " ", "<", ">"]):
        return None
    return value

def link(label, value):
    u = url(value)
    return f"[{field(label)}](<{u}>)" if u else field(label)

def load_local_problems():
    found = {}
    for meta in sorted(BASE.glob("**/metadata.json")):
        if "contributions" in meta.parts:
            continue
        obj = json.loads(meta.read_text(encoding="utf-8"))
        pid = obj.get("problem_id") or obj.get("id")
        if pid:
            found[pid] = (obj, meta.parent)
    return found

def main():
    DOCS.mkdir(exist_ok=True)

    external = records(DATA / "problems.json")
    claims = records(DATA / "claims.json")
    local = load_local_problems()

    titles = {
        p["id"]: str(p.get("title", p["id"]))
        for p in external
        if p.get("id")
    }

    for pid, (obj, folder) in local.items():
        titles[pid] = str(obj.get("title", titles.get(pid, pid)))

    problems = [
        "# Mathematical Problems",
        "",
        "These are indexed problem records, not necessarily distinct",
        "mathematical questions. OMP does not verify their status.",
        "",
        "| Problem ID | Name | Record |",
        "|---|---|---|",
    ]

    for pid, title in sorted(titles.items(), key=lambda x: x[1].lower()):
        if pid in local:
            rel = local[pid][1].relative_to(ROOT).as_posix()
            dest = "../" + rel + "/README.md"
            ref = f"[Problem page](<{dest}>)"
        else:
            ref = "External indexed record"
        problems.append(f"| `{field(pid)}` | {field(title)} | {ref} |")

    if len(problems) == 6:
        problems.append("| — | No indexed problems yet | — |")

    contributions = [
        "# Research Contributions",
        "",
        "**Source-reported and contributor-submitted research.**",
        "OMP does not verify mathematical correctness, novelty,",
        "authorship, or academic priority.",
        "",
        "Different records may concern the same mathematical problem.",
        "",
        "| Problem | Contribution | Reported status | Source |",
        "|---|---|---|---|",
    ]

    count_external = 0
    for c in sorted(claims, key=lambda x: x.get("id", "")):
        pid = c.get("problem_id")
        src = c.get("source") or {}
        name = titles.get(pid, pid or "Unknown problem")
        outcome = c.get("reported_outcome")
        status = src.get("reported_status", "unknown")
        label = field(outcome or "Source-reported result")
        contributions.append(
            f"| {field(name)} | {label} | "
            f"{field(status)} | {link('Original source', src.get('url'))} |"
        )
        count_external += 1

    count_local = 0
    for meta in sorted(BASE.glob("**/contributions/*/metadata.json")):
        c = json.loads(meta.read_text(encoding="utf-8"))
        pid = c.get("problem_id")
        title = c.get("title", c.get("id", "Untitled"))
        rel = meta.parent.relative_to(ROOT).as_posix()
        dest = "../" + rel + "/README.md"
        contributions.append(
            f"| {field(titles.get(pid, pid or 'Unknown'))} | "
            f"[{field(title)}](<{dest}>) | "
            f"{field(c.get('reported_status', 'not specified'))} | "
            f"{link('Original submission', c.get('issue_url'))} |"
        )
        count_local += 1

    if not count_local and not count_external:
        contributions.append("| — | No contributions yet | — | — |")

    (DOCS / "PROBLEMS.md").write_text(
        "\n".join(problems) + "\n", encoding="utf-8"
    )
    (DOCS / "CONTRIBUTIONS.md").write_text(
        "\n".join(contributions) + "\n", encoding="utf-8"
    )

    print(
        f"UNIFIED INDEX: problems={len(titles)} "
        f"external_claims={count_external} "
        f"submitted_contributions={count_local}"
    )

if __name__ == "__main__":
    main()
