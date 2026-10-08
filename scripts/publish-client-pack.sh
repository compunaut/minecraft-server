#!/usr/bin/env bash
set -euo pipefail
zip=$(realpath "${1:?client ZIP required}")
tag=${2:?version tag required}
branch=${3:?target branch required}
[[ "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo 'Expected version tag vX.Y.Z' >&2; exit 1; }
git check-ref-format --branch "$branch" >/dev/null
expected="epic-fight-pack-${tag}.zip"
[[ "$(basename "$zip")" == "$expected" ]] || { echo 'ZIP filename does not match tag' >&2; exit 1; }
python3 - "$zip" "${tag#v}" <<'CHECK'
import json,sys,zipfile
with zipfile.ZipFile(sys.argv[1]) as z:
    assert json.loads(z.read('manifest.json'))['version'] == sys.argv[2], 'ZIP version does not match tag'
    assert not any(n.lower().endswith('.jar') for n in z.namelist()), 'Do not publish bundled mod JARs'
CHECK
# Work on a separate checkout of the latest default branch; retain the tag checkout.
publish_root=$(mktemp -d "${RUNNER_TEMP:-${TMPDIR:-/tmp}}/client-pack-publish.XXXXXX")
cleanup() { git worktree remove --force "$publish_root/tree" >/dev/null 2>&1 || true; rmdir "$publish_root" 2>/dev/null || true; }
trap cleanup EXIT
git fetch origin "$branch"
git worktree add --detach "$publish_root/tree" FETCH_HEAD
out="$publish_root/tree/client-packs"
mkdir -p "$out"
if [[ -e "$out/$expected" || -e "$out/$expected.sha256" ]]; then
    echo "Refusing to overwrite published $expected; create a new pack version." >&2
    exit 1
fi
cp "$zip" "$out/$expected"
(cd "$out" && sha256sum "$expected" > "$expected.sha256")
git -C "$publish_root/tree" config user.name 'github-actions[bot]'
git -C "$publish_root/tree" config user.email '41898282+github-actions[bot]@users.noreply.github.com'
git -C "$publish_root/tree" add -- "client-packs/$expected" "client-packs/$expected.sha256"
git -C "$publish_root/tree" commit -m "Publish client pack $tag"
if ! git -C "$publish_root/tree" push origin "HEAD:refs/heads/$branch"; then
    echo 'Could not publish client ZIP: check default-branch protections or concurrent updates. No force push was attempted. The Actions artifact remains downloadable.' >&2
    exit 1
fi
