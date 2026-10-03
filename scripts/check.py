"""
One command: ruff + mypy on backend/app + pytest.

Invoked from the repo root so it can grow into a frontend check later.
Runs everything sequentially, returns non-zero if any stage fails.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND = REPO_ROOT / "backend"
FRONTEND = REPO_ROOT / "frontend"
VENV_PY = BACKEND / ".venv" / "Scripts" / "python.exe"
if not VENV_PY.exists():
    VENV_PY = BACKEND / ".venv" / "bin" / "python"


def run(name: str, cmd: list[str], cwd: Path, *, shell: bool = False) -> bool:
    print(f"\n=== {name} ===")
    print("$", " ".join(str(c) for c in cmd))
    result = subprocess.run(cmd, cwd=cwd, shell=shell)
    ok = result.returncode == 0
    print(f"[{name}] {'ok' if ok else 'FAILED'}")
    return ok


def main() -> int:
    if not VENV_PY.exists():
        print(f"venv python not found at {VENV_PY} — create backend/.venv first")
        return 2

    stages = [
        ("backend:ruff", [str(VENV_PY), "-m", "ruff", "check", "app", "tests"], BACKEND, False),
        ("backend:mypy", [str(VENV_PY), "-m", "mypy", "app"], BACKEND, False),
        ("backend:pytest", [str(VENV_PY), "-m", "pytest", "tests", "-q"], BACKEND, False),
    ]
    # Frontend stages run only if frontend/ exists AND node_modules is installed
    # — the check script shouldn't force a dependency install mid-check.
    if FRONTEND.exists() and (FRONTEND / "node_modules").exists():
        stages.extend([
            ("frontend:typecheck", ["npx", "tsc", "--noEmit"], FRONTEND, True),
            ("frontend:lint", ["npx", "eslint", "src", "--max-warnings=0"], FRONTEND, True),
            ("frontend:test", ["npx", "vitest", "run"], FRONTEND, True),
        ])

    failed: list[str] = []
    for name, cmd, cwd, shell in stages:
        if not run(name, cmd, cwd, shell=shell):
            failed.append(name)

    if failed:
        print(f"\nFAIL: {', '.join(failed)}")
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
