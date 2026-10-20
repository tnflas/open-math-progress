"""Conservative GitHub README index adapter."""
import base64
import json
import re
from urllib.request import Request, urlopen
from urllib.parse import urljoin

def collect_readme_index(source, token=None):
    repo = source["repo"]
    url = f"https://api.github.com/repos/{repo}/readme"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "open-math-progress",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = Request(url, headers=headers)
    with urlopen(req, timeout=30) as response:
        obj = json.load(response)

    content = base64.b64decode(
        obj["content"].replace("\n", "")
    ).decode("utf-8")

    # Prefer the actual README path and branch returned by GitHub.
    html_url = obj.get("html_url") or f"https://github.com/{repo}"
    base_url = html_url.rsplit("/", 1)[0] + "/"

    results = []
    in_index = False

    pattern = re.compile(
        r"^\s*-\s+\*\*\[(.+?)\]\(([^)]+)\)\*\*\s*(.*)$"
    )

    for line in content.splitlines():
        if re.match(r"^##\s+Index\s*$", line, re.I):
            in_index = True
            continue

        if in_index and re.match(r"^##\s+", line):
            break

        if not in_index:
            continue

        match = pattern.match(line)
        if not match:
            continue

        title, target, remainder = match.groups()

        # Read only a status explicitly attached to the entry.
        status_match = re.match(
            r"^\s*(?:—|-)\s*"
            r"(?:\*+)?"
            r"(proved|refuted|nonexistence|"
            r"claimed refutation|claimed proof)",
            remainder,
            re.I,
        )

        if not status_match:
            continue

        outcome = status_match.group(1).lower()

        if outcome not in {
            "proved", "refuted", "nonexistence",
            "claimed refutation", "claimed proof"
        }:
            continue

        source_url = urljoin(base_url, target)

        # Use a direct entry link, never the whole README
        # as the identifier for every row.
        results.append({
            "title": title,
            "source_url": source_url,
            "repository": repo,
            "status": "claimed_solved",
            "reported_outcome": outcome,
            "source_collection_category": "ai-math-curated-index",
            "reported_evidence": remainder[:2000],
            "ai_involvement": "unknown",
            "source_updated_at": None,
        })

    print(f"README {repo}: extracted={len(results)}")
    return results
