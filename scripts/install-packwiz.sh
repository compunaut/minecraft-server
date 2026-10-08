#!/usr/bin/env bash
set -euo pipefail
# Same revision as the local working Packwiz binary. No @latest in CI.
GOBIN="${GOBIN:-$PWD/.cache/bin}" go install github.com/packwiz/packwiz@v0.0.0-20260218225342-dfd8b68a4796
