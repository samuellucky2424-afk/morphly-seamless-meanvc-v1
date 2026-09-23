from __future__ import annotations
import json
import subprocess
from pathlib import Path

roots = {
    "seamless_communication": Path("/opt/seamless_communication"),
    "MeanVC2": Path("/opt/MeanVC2"),
}

def git(path: Path, *args):
    return subprocess.check_output(["git", "-C", str(path), *args], text=True).strip()

manifest = {}
for name, path in roots.items():
    manifest[name] = {
        "sha": git(path, "rev-parse", "HEAD"),
        "remote": git(path, "remote", "get-url", "origin"),
    }
print(json.dumps(manifest, indent=2))
