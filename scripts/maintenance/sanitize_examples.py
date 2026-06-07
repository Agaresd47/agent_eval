"""One-off scrub for examples/ run records. Removes leaked local paths."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples"

REPLACEMENTS = [
    ("C:\\\\Users\\\\agares\\\\OneDrive\\\\0 求职\\\\面试\\\\Agent_info_flow", "<REPO_ROOT>"),
    ("C:\\\\Users\\\\agares\\\\OneDrive\\\\0 求职\\\\面试\\\\agent_eval", "<REPO_ROOT>"),
    ("C:\\\\Users\\\\agares\\\\AppData\\\\Local\\\\Temp", "<SANDBOX_TEMP>"),
    ("C:\\Users\\agares\\OneDrive\\0 求职\\面试\\Agent_info_flow", "<REPO_ROOT>"),
    ("C:\\Users\\agares\\OneDrive\\0 求职\\面试\\agent_eval", "<REPO_ROOT>"),
    ("C:\\Users\\agares\\AppData\\Local\\Temp", "<SANDBOX_TEMP>"),
    ("/c/Users/agares/OneDrive/0 求职/面试/Agent_info_flow", "<REPO_ROOT>"),
    ("/c/Users/agares/OneDrive/0 求职/面试/agent_eval", "<REPO_ROOT>"),
    ("/c/Users/agares/AppData/Local/Temp", "<SANDBOX_TEMP>"),
    (" agares ", " user "),
]


def scrub(path: Path) -> bool:
    try:
        original = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return False
    updated = original
    for needle, replacement in REPLACEMENTS:
        updated = updated.replace(needle, replacement)
    if updated == original:
        return False
    path.write_text(updated, encoding="utf-8")
    return True


def main() -> None:
    touched = 0
    scanned = 0
    for path in EXAMPLES.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".json", ".md", ".txt", ".yaml", ".yml"}:
            continue
        scanned += 1
        if scrub(path):
            touched += 1
    print(f"scanned={scanned} touched={touched}")


if __name__ == "__main__":
    main()
