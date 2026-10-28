"""Loads settings from a .env file into the environment."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_env():
    """Reads .env in the project folder or in the folder above it (the repository root)."""
    for env_file in (ROOT / ".env", ROOT.parent / ".env"):
        if env_file.exists():
            for line in env_file.read_text(encoding="utf-8").splitlines():
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())
