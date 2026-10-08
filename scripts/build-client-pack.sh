#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PYTHON="${PYTHON:-python3}"
"$PYTHON" scripts/pack.py validate
version=$("$PYTHON" scripts/pack.py version)
mkdir -p dist
# Pure CurseForge references: no non-CurseForge binaries may be silently bundled.
packwiz curseforge export --side client --output "dist/epic-fight-pack-v${version}.zip"
"$PYTHON" scripts/pack.py check-zip "dist/epic-fight-pack-v${version}.zip"
