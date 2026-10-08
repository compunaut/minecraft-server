"""Exercise release decisions against real pack metadata and disposable Git tags."""
from pathlib import Path
import os, shutil, subprocess, tempfile
root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as directory:
    repo = Path(directory)
    for name in ('scripts', 'mods', 'config'):
        shutil.copytree(root / name, repo / name)
    for name in ('pack.toml', 'index.toml'):
        shutil.copy(root / name, repo / name)
    def run(*args):
        return subprocess.run(args, cwd=repo, text=True, capture_output=True, check=True).stdout.strip()
    run('git', 'init', '--initial-branch=main')
    run('git', 'config', 'user.name', 'Release Test')
    run('git', 'config', 'user.email', 'test@example.invalid')
    run('git', 'add', '.')
    run('git', 'commit', '-m', 'test pack')
    tag = 'v' + run('python3', 'scripts/pack.py', 'version')
    def select(event, ref):
        return run('bash', 'scripts/select-release-tag.sh', event, ref)
    assert select('pull_request', 'refs/heads/main') == ''
    assert select('push', 'refs/heads/feature') == ''
    assert select('push', 'refs/heads/main') == tag
    run('git', 'tag', tag)
    assert select('push', 'refs/heads/main') == ''
    assert select('push', 'refs/tags/' + tag) == tag
    failed = subprocess.run(['bash', 'scripts/select-release-tag.sh', 'push', 'refs/tags/v999.0.0'], cwd=repo, capture_output=True)
    assert failed.returncode != 0
    pack = repo / 'pack.toml'
    import re
    pack.write_text(re.sub(r'^version = ".*"$', 'version = "999.0.0"', pack.read_text(), count=1, flags=re.MULTILINE))
    assert select('push', 'refs/heads/main') == 'v999.0.0'
print('Release selection passed: PR/feature skipped, new main version selected, existing version skipped, manual tag checked, version bump selected')
