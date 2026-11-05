"""Pre-push check that likely credentials are not tracked by Git."""
from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUSPICIOUS_PATTERNS = [
    re.compile(
        r"GIGACHAT_CREDENTIALS[ \t]*=[ \t]*[A-Za-z0-9+/=_-]{32,}",
        re.IGNORECASE,
    ),
    re.compile(
        r"Authorization[ \t]*:[ \t]*Basic[ \t]+[A-Za-z0-9+/=_-]{32,}",
        re.IGNORECASE,
    ),
]


def tracked_files() -> list[Path]:
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return [
            path
            for path in ROOT.rglob("*")
            if path.is_file()
            and ".git" not in path.parts
            and "venv" not in path.parts
            and ".venv" not in path.parts
            and path.name != ".env"
        ]

    return [ROOT / line for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    problems: list[str] = []

    for path in tracked_files():
        if not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue

        if any(pattern.search(text) for pattern in SUSPICIOUS_PATTERNS):
            problems.append(str(path.relative_to(ROOT)))

    if problems:
        print("Возможные секреты найдены в файлах:")
        for problem in problems:
            print(f"- {problem}")
        return 1

    print("OK: явных секретов в отслеживаемых файлах не найдено.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
