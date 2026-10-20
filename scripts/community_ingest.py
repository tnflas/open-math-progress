"""Import community GitHub Issue Forms without mathematical review."""
import json
import os
import re
import sys
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "problems"
DOCS = ROOT / "docs"
API = "https://api.github.com/"

def get(path):
    token = os.getenv("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "OpenMathProgress",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    with urlopen(Request(API + path, headers=headers), timeout=30) as r:
        return json.load(r)

def parse_form(body):
    """Parse sections emitted by GitHub Issue Forms."""
    result = {}
    key = None
    for line in (body or "").splitlines():
        if line.startswith("### "):
            key = line[4:].strip()
            result[key] = ""
        elif key:
            result[key] += line + "\n"
    return {k: v.strip() for k, v in result.items()}

def clean(s, limit=4000):
    return str(s or "").replace("\x00", "")[:limit]

def md(s):
    """Keep untrusted user text from creating Markdown/HTML markup."""
    s = clean(s).replace("&", "&amp;").replace("<", "&lt;")
    return s.replace(">", "&gt;")

def write_new(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(
            json.dumps(obj, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        return True
    return False

def write_generated(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old != content:
        path.write_text(content, encoding="utf-8")

def problem_records():
    records = {}
    external = ROOT / "data/problems.json"
    if external.exists():
        for p in json.loads(external.read_text(encoding="utf-8")):
            if p.get("id"):
                records[p["id"]] = p.get("title", p["id"])
    for f in sorted(BASE.glob("community/*/metadata.json")):
        p = json.loads(f.read_text(encoding="utf-8"))
        records[p["id"]] = p["title"]
    return records

def process_problem(issue):
    n = issue["number"]
    pid = f"OMP-U-{n}"
    fields = parse_form(issue.get("body"))
    title = fields.get("Problem Title")
    statement = fields.get("Problem Statement")
    reference = fields.get("Original Reference")
    if not title or not statement or not reference:
        print("SKIP incomplete problem", n)
        return

    folder = BASE / "community" / pid.lower()
    meta = {
        "id": pid,
        "title": clean(title, 500),
        "statement": clean(statement, 12000),
        "original_reference": clean(reference, 2000),
        "field": clean(fields.get("Mathematical Field", "Other")),
        "submitted_by": (issue.get("user") or {}).get("login"),
        "issue_url": issue["html_url"],
        "created_at": issue["created_at"],
        "verification": "not_assessed",
        "registration_type": "contributor_submitted",
    }
    created = write_new(folder / "metadata.json", meta)
    if created:
        print("REGISTERED", pid)

def find_folder(pid):
    community = BASE / "community" / pid.lower()
    if (community / "metadata.json").exists():
        return community
    # Match an already materialized problem directory by metadata.
    for p in BASE.iterdir():
        f = p / "metadata.json"
        if f.exists():
            try:
                meta = json.loads(f.read_text(encoding="utf-8"))
                if meta.get("problem_id", meta.get("id")) == pid:
                    return p
            except (ValueError, OSError):
                pass
    # External indexed problems may have no local directory yet.
    existing = problem_records()
    if pid not in existing:
        return None
    return BASE / "indexed" / pid.lower()

def process_contribution(issue):
    n = issue["number"]
    fields = parse_form(issue.get("body"))
    pid = fields.get("Problem ID", "").strip()
    title = fields.get("Contribution Title", "").strip()
    abstract = fields.get("Abstract", "").strip()
    links = fields.get("Manuscript and Attachment Links", "").strip()

    if not all((pid, title, abstract, links)):
        print("SKIP incomplete contribution", n)
        return

    folder = find_folder(pid)
    if folder is None:
        print("PENDING unknown problem", pid, "issue", n)
        return

    cid = f"OMP-C-I-{n}"
    cdir = folder / "contributions" / cid.lower()
    authors = [
        clean(x, 300) for x in
        fields.get("Authors", "").splitlines() if x.strip()
    ]
    meta = {
        "id": cid,
        "problem_id": pid,
        "title": clean(title, 500),
        "authors": authors,
        "abstract": clean(abstract, 12000),
        "reported_status": clean(fields.get("Reported Status")),
        "ai_involvement": clean(fields.get("AI Involvement")),
        "manuscript_links": clean(links, 8000),
        "issue_url": issue["html_url"],
        "submitted_by": (issue.get("user") or {}).get("login"),
        "created_at": issue["created_at"],
        "verification": "not_assessed",
    }
    if write_new(cdir / "metadata.json", meta):
        print("REGISTERED", cid)

def rebuild_indexes():
    problems = problem_records()
    p_lines = [
        "# Community Mathematical Problems", "",
        "Contributor-submitted; not independently verified by OMP.",
        "",
    ]
    c_lines = [
        "# Community Research Contributions", "",
        "Contributor-submitted; no mathematical or priority adjudication.",
        "",
    ]
    for f in sorted(BASE.glob("community/*/metadata.json")):
        p = json.loads(f.read_text(encoding="utf-8"))
        rel = f.parent.relative_to(ROOT)
        p_lines.append(
            f"- {md(p['title'])} — `{p['id']}` "
            f"([record](../{rel}/README.md))"
        )

    for f in sorted(BASE.glob("**/contributions/*/metadata.json")):
        c = json.loads(f.read_text(encoding="utf-8"))
        rel = f.parent.relative_to(ROOT)
        c_lines.append(
            f"- {md(c['title'])} — `{c['problem_id']}` "
            f"([report](../{rel}/README.md))"
        )

    for f in sorted(BASE.glob("community/*/metadata.json")):
        p = json.loads(f.read_text(encoding="utf-8"))
        folder = f.parent
        lines = [
            "# " + md(p["title"]), "",
            "**Problem ID:** `" + p["id"] + "`", "",
            "**Mathematical verification:** Not assessed.", "",
            "## Statement", "", md(p["statement"]), "",
            "## Original reference", "",
            md(p["original_reference"]), "",
            "## Contributions", "",
        ]
        for cf in sorted(folder.glob("contributions/*/metadata.json")):
            c = json.loads(cf.read_text(encoding="utf-8"))
            lines.append(
                "- [" + md(c["title"]) + "]"
                "(contributions/" + cf.parent.name + "/README.md)"
            )
        write_generated(folder / "README.md", "\n".join(lines) + "\n")

    for f in sorted(BASE.glob("**/contributions/*/metadata.json")):
        c = json.loads(f.read_text(encoding="utf-8"))
        lines = [
            "# " + md(c["title"]), "",
            "**Problem ID:** `" + md(c["problem_id"]) + "`", "",
            "**Authors:** " + ", ".join(md(x) for x in c["authors"]), "",
            "**Reported status:** " + md(c["reported_status"]), "",
            "**AI involvement:** " + md(c["ai_involvement"]), "",
            "**OMP verification:** Not assessed", "",
            "## Abstract", "", md(c["abstract"]), "",
            "## Manuscript and attachments", "",
            md(c["manuscript_links"]), "",
            "## Original submission", "",
            c["issue_url"], "",
        ]
        write_generated(f.parent / "README.md", "\n".join(lines) + "\n")

    if len(p_lines) == 4:
        p_lines.append("No community problems registered yet.")
    if len(c_lines) == 4:
        c_lines.append("No community contributions registered yet.")

    write_generated(
        DOCS / "COMMUNITY_PROBLEMS.md",
        "\n".join(p_lines) + "\n",
    )


def main():
    repo = os.getenv("GITHUB_REPOSITORY")
    if not repo or not re.fullmatch(r"[\w.-]+/[\w.-]+", repo):
        raise SystemExit("GITHUB_REPOSITORY is required")

    issues = []
    for page in range(1, 11):
        batch = get(
            f"repos/{repo}/issues?state=all&per_page=100&page={page}"
        )
        issues.extend(x for x in batch if "pull_request" not in x)
        if len(batch) < 100:
            break

    # Process problem registrations before their contributions.
    for issue in issues:
        if issue.get("title", "").startswith("[New Problem]"):
            process_problem(issue)

    for issue in issues:
        if issue.get("title", "").startswith("[Contribution]"):
            process_contribution(issue)

    rebuild_indexes()
    print("Community synchronization complete")

if __name__ == "__main__":
    main()
