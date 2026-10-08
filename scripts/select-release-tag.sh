#!/usr/bin/env bash
set -euo pipefail
# PR builds never release. Main publishes each canonical pack version once.
event=${1:?event required}
ref=${2:?ref required}
[[ "$event" != pull_request ]] || exit 0
version=$(python3 scripts/pack.py version)
tag="v$version"
[[ "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]
if [[ "$ref" == refs/tags/* ]]; then
    [[ "$ref" == "refs/tags/$tag" ]] || { echo 'Tag does not match pack version' >&2; exit 1; }
    echo "$tag"
elif [[ "$ref" == refs/heads/main ]]; then
    if ! git show-ref --verify --quiet "refs/tags/$tag"; then
        echo "$tag"
    fi
fi
