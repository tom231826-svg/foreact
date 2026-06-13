from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def path(name: str) -> Path:
    return ROOT / name
