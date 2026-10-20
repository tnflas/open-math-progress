"""Generate the basic research index."""
import json
from pathlib import Path

def main():
    root = Path(__file__).resolve().parents[1]
    problems = json.loads(
        (root / "data/problems.json").read_text(encoding="utf-8")
    )

    lines = [
        "# Research Index",
        "",
        "Entries are source-reported and not independently verified.",
        "",
    ]

    for item in problems:
        title = str(item.get("title", "Untitled")).replace("\n", " ")
        url = str(item.get("source_url", ""))
        if url.startswith(("https://", "http://")):
            lines.append(f"- {title} — {url}")

    if not problems:
        lines.append("No indexed records yet.")

    (root / "docs/INDEX.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print("Generated docs/INDEX.md")

if __name__ == "__main__":
    main()
