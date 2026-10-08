#!/bin/bash
set -euo pipefail
if [[ "${EULA:-FALSE}" != TRUE ]]; then
  echo 'Read the Minecraft EULA and explicitly set EULA=TRUE.' >&2
  exit 1
fi
# Versions come from the immutable pack baked into this image, never overrides.
read -r VERSION FORGE_VERSION < <(python3 /opt/pack-tool.py --root /opt/pack versions)
export VERSION FORGE_VERSION TYPE=FORGE
unset PACKWIZ_URL MODS MODPACK MODRINTH_PROJECTS CF_SLUG CF_PAGE_URL CF_FILE_ID
python3 /opt/pack-tool.py --root /opt/pack install --data /data
# /start ultimately execs upstream mc-server-runner, which gracefully saves on SIGTERM.
exec /start "$@"
