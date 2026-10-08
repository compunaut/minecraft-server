from pathlib import Path
import tempfile,subprocess,shutil,os,json,zipfile
r=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
 tmp=Path(tmp).resolve();origin=tmp/'origin.git';repo=tmp/'checkout';runner=tmp/'runner';runner.mkdir()
 def run(*args,cwd=None,ok=True):
  p=subprocess.run(args,cwd=cwd,text=True,capture_output=True)
  if ok and p.returncode:raise RuntimeError(p.stdout+p.stderr)
  return p
 run('git','init','--bare','--initial-branch=main',str(origin));run('git','clone',str(origin),str(repo))
 run('git','config','user.name','Publish Test',cwd=repo);run('git','config','user.email','test@example.invalid',cwd=repo)
 shutil.copy(r/'.gitignore',repo/'.gitignore');(repo/'untouched.txt').write_text('keep this\n')
 run('git','add','.',cwd=repo);run('git','commit','-m','initial',cwd=repo);run('git','push','origin','main',cwd=repo)
 env=dict(os.environ,RUNNER_TEMP=str(runner))
 zip=next((r/'dist').glob('epic-fight-pack-v*.zip'))
 tag=zip.stem.removeprefix('epic-fight-pack-')
 cmd=['bash',str(r/'scripts/publish-client-pack.sh'),str(zip),tag,'main']
 p=subprocess.run(cmd,cwd=repo,env=env,text=True,capture_output=True);assert p.returncode==0,p.stdout+p.stderr
 files=run('git','--git-dir',str(origin),'diff-tree','--no-commit-id','--name-only','-r','main').stdout.splitlines()
 assert files==[f'client-packs/{zip.name}',f'client-packs/{zip.name}.sha256'],files
 p=subprocess.run(cmd,cwd=repo,env=env,text=True,capture_output=True);assert p.returncode!=0 and 'Refusing to overwrite' in p.stderr,p.stdout+p.stderr
 assert not list(runner.iterdir()),'Temporary worktree leaked'
 print('Publishing test passed: only ZIP/checksum committed, default branch updated, duplicate version refused, worktree cleaned')
