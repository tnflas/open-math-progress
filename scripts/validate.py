"""Validate local JSON data formats."""
import json
from pathlib import Path

def main():
    root = Path(__file__).resolve().parents[1]
    for name in ("problems", "claims", "notices"):
        path = root / "data" / f"{name}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"{path} must contain a JSON array")
        print(f"Valid: {path.name}")

if __name__ == "__main__":
    main()
