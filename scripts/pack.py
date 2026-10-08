#!/usr/bin/env python3
"""Validate canonical Packwiz metadata, fetch pinned files, and install server mods."""
import argparse, hashlib, json, os, re, shutil, sys, tempfile, urllib.parse, urllib.request, zipfile
from pathlib import Path
try:
    import tomllib
except ImportError:
    import tomli as tomllib

def load(p):
    return tomllib.loads(Path(p).read_text())

def require(ok, message):
    if not ok:
        raise ValueError(message)

def digest(p, algorithm='sha256'):
    h = hashlib.new(algorithm)
    with Path(p).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()

# Required project identities prevent substitutions; versions live only in Packwiz.
REQUIRED = {405076,1434276,1408812,1377795,1151542,900642,1225584,1036425,1184379,1090102,918614}
EMBEDDIUM = 908741

def read_pack(root):
    pack = load(root/'pack.toml')
    require(pack['versions']['minecraft'] == '1.20.1', 'Minecraft must remain 1.20.1')
    require(set(pack['versions']) == {'minecraft','forge'}, 'Forge must be the sole loader')
    require(re.fullmatch(r'47\.\d+\.\d+', pack['versions']['forge']), 'Expected Forge 47.x for 1.20.1')
    require(re.fullmatch(r'\d+\.\d+\.\d+', pack['version']), 'Pack version must be semantic x.y.z')
    idx = pack['index']
    require(idx['file'] == 'index.toml' and idx['hash-format'] == 'sha256', 'Unexpected index format')
    require(digest(root/'index.toml') == idx['hash'], 'Stale pack/index hash; run packwiz refresh')
    index = load(root/'index.toml')
    require(index['hash-format'] == 'sha256', 'Index must use sha256')
    mods, seen, projects, filenames = [], set(), set(), set()
    for entry in index.get('files', []):
        rel = entry['file']; p = root/rel
        require(rel not in seen and not p.is_symlink() and '..' not in Path(rel).parts, 'Duplicate or unsafe path: '+rel)
        seen.add(rel)
        require(p.is_file() and digest(p) == entry['hash'], 'Missing/stale indexed file: '+rel)
        if rel.startswith('mods/') and rel.endswith('.pw.toml'):
            require(entry.get('metafile') is True, 'Mod metadata must be marked metafile')
            mod = load(p); cf = mod.get('update',{}).get('curseforge',{})
            require(cf.get('project-id') and cf.get('file-id'), 'CurseForge metadata required: '+rel)
            require(mod['download'].get('mode') == 'metadata:curseforge', 'Unsupported distribution mode: '+rel)
            require(mod['download']['hash-format'] in ('sha1','sha256','sha512'), 'Unsupported checksum')
            require(re.fullmatch(r'[0-9a-f]+',mod['download']['hash']), 'Invalid checksum')
            project = cf['project-id']
            require(project not in projects, 'Duplicate project: '+str(project))
            require(mod['filename'] not in filenames and Path(mod['filename']).name == mod['filename'] and mod['filename'].endswith('.jar'), 'Duplicate/unsafe mod filename')
            require(mod['side'] in ('both','client','server'), 'Invalid mod side')
            require(project in REQUIRED|{EMBEDDIUM}, 'Unexpected project; review allowlist before changing pack: '+str(project))
            require(mod['side'] == ('client' if project == EMBEDDIUM else 'both'), 'Wrong side: '+mod['name'])
            projects.add(project); filenames.add(mod['filename']); mods.append(mod)
        else:
            require(rel.startswith('config/') and p.suffix in ('.toml','.yml','.json'), 'Runtime or unsupported file in pack: '+rel)
    require(projects == REQUIRED|{EMBEDDIUM}, 'Missing required projects: '+str((REQUIRED|{EMBEDDIUM})-projects))
    actual = {str(p.relative_to(root)) for p in (root/'mods').glob('*') if p.is_file()}
    require(actual == {x for x in seen if x.startswith('mods/')}, 'Unindexed mod files or binaries present')
    return pack, index, mods

def fetch(mod, cache, local=None):
    target = cache/mod['filename']; meta = mod['download']
    if local and (local/mod['filename']).is_file():
        candidate = local/mod['filename']
        require(digest(candidate,meta['hash-format']) == meta['hash'], 'Local JAR hash mismatch: '+mod['filename'])
        shutil.copyfile(candidate,target)
    if target.exists() and digest(target,meta['hash-format']) == meta['hash']:
        return target
    file_id = str(mod['update']['curseforge']['file-id'])
    # CurseForge's public CDN path identifies the pinned file, never a latest version.
    url = 'https://edge.forgecdn.net/files/'+file_id[:-3]+'/'+str(int(file_id[-3:]))+'/'+urllib.parse.quote(mod['filename'])
    fd, tmp = tempfile.mkstemp(dir=cache); os.close(fd)
    try:
        req = urllib.request.Request(url, headers={'User-Agent':'GlassHousePack/1.0'})
        with urllib.request.urlopen(req,timeout=90) as resp, open(tmp,'wb') as out:
            shutil.copyfileobj(resp,out)
        require(digest(tmp,meta['hash-format']) == meta['hash'], 'Downloaded checksum mismatch: '+mod['filename'])
        os.replace(tmp,target)
    except Exception as exc:
        raise ValueError('Cannot fetch pinned '+mod['filename']+'; no substitution/manual-download fallback. '+str(exc)) from exc
    finally:
        Path(tmp).unlink(missing_ok=True)
    return target

def version_tuple(value):
    return tuple(int(n) for n in re.findall(r'\d+',value))

def in_range(version, spec):
    # Forge commonly uses Maven intervals. Fail closed for complex union ranges.
    if spec in ('','*'): return True
    if spec.startswith(('(', '[')):
        require(spec.count(',') <= 1, 'Unsupported union dependency range: '+spec)
        if ',' not in spec:
            return spec.startswith('[') and spec.endswith(']') and version_tuple(version)==version_tuple(spec[1:-1])
        lo,hi = (x.strip() for x in spec[1:-1].split(',')); v = version_tuple(version)
        def cmp(a,b):
            width=max(len(a),len(b));a=a+(0,)*(width-len(a));b=b+(0,)*(width-len(b));return (a>b)-(a<b)
        return (not lo or cmp(v,version_tuple(lo)) >= (1 if spec[0]=='(' else 0)) and (not hi or cmp(v,version_tuple(hi)) <= (-1 if spec[-1]==')' else 0))
    return version_tuple(version) == version_tuple(spec)

def jar_metadata(path):
    results=[]
    def inspect(z, depth=0, constraint=""):
        if 'META-INF/mods.toml' in z.namelist():
            data=tomllib.loads(z.read('META-INF/mods.toml').decode())
            manifest=z.read('META-INF/MANIFEST.MF').decode(errors='replace') if 'META-INF/MANIFEST.MF' in z.namelist() else ''
            match=re.search(r'^Implementation-Version: (.+)$',manifest,re.M)
            for m in data.get('mods',[]):
                version=str(m.get('version',''))
                if version=='${file.jarVersion}':
                    require(match is not None,'Missing implementation version in '+path.name);version=match.group(1).strip()
                results.append((m['modId'],version,data.get('dependencies',{}).get(m['modId'],[]),depth,constraint))
        if depth==0 and 'META-INF/jarjar/metadata.json' in z.namelist():
            import io
            for nested in json.loads(z.read('META-INF/jarjar/metadata.json')).get('jars',[]):
                with zipfile.ZipFile(io.BytesIO(z.read(nested['path']))) as child: inspect(child,1,nested['version']['range'])
    with zipfile.ZipFile(path) as z: inspect(z)
    require(results,'No Forge mod metadata in '+path.name)
    return results

def dependencies(pack,mods,paths,side):
    present={'minecraft':pack['versions']['minecraft'],'forge':pack['versions']['forge'],'java':'17'}; selected={}; bundled={}
    for mod in mods:
        if mod['side'] not in ('both',side): continue
        for mid,version,deps,depth,constraint in jar_metadata(paths[mod['filename']]):
            if depth == 0:
                require(mid not in selected and mid not in present,'Duplicate top-level mod ID on '+side+': '+mid)
                selected[mid]=(version,deps)
            else:
                bundled.setdefault(mid,[]).append((version,deps,constraint))
    for mid,candidates in bundled.items():
        ranges=[c[2] for c in candidates]
        if mid in selected:
            require(all(in_range(selected[mid][0],r) for r in ranges),'Standalone '+mid+' violates bundled dependency range')
        else:
            suitable=[c for c in candidates if all(in_range(c[0],r) for r in ranges)]
            require(suitable,'No compatible bundled dependency '+mid)
            choice=max(suitable,key=lambda c:version_tuple(c[0]));selected[mid]=choice[:2]
    present.update({mid:v for mid,(v,d) in selected.items()})
    records=[(mid,d) for mid,(v,d) in selected.items()]
    for mid,deps in records:
        for dep in deps:
            if not dep.get('mandatory',False) or dep.get('side','BOTH') not in ('BOTH',side.upper()): continue
            target=dep['modId'];require(target in present,mid+' missing dependency '+target+' on '+side)
            require(in_range(present[target],dep.get('versionRange','')),mid+' needs '+target+' '+dep.get('versionRange','')+'; have '+present[target])
    print('Declared mandatory dependencies OK for '+side)

def check_zip(pack,mods,path):
    expected={(m['update']['curseforge']['project-id'],m['update']['curseforge']['file-id']) for m in mods if m['side'] in ('both','client')}
    with zipfile.ZipFile(path) as z:
        manifest=json.loads(z.read('manifest.json'))
        actual=[(f['projectID'],f['fileID']) for f in manifest['files']]
        require(set(actual)==expected and len(actual)==len(expected),'Incomplete/duplicate CurseForge manifest')
        require(all(f.get('required') for f in manifest['files']),'Every mod must be required')
        require(manifest['version']==pack['version'],'Wrong client version')
        require(manifest['minecraft']['version']=='1.20.1','Wrong client Minecraft')
        require(manifest['minecraft']['modLoaders']==[{'id':'forge-'+pack['versions']['forge'],'primary':True}],'Wrong client Forge')
        require(not any(n.lower().endswith('.jar') for n in z.namelist()),'JAR bundling requires explicit license review')
        allowed={'manifest.json','modlist.html'}
        for n in z.namelist():
            require('..' not in Path(n).parts and not n.startswith('/'),'Unsafe ZIP path')
            require(n in allowed or n.startswith('overrides/config/') or n=='overrides/','Unexpected ZIP content: '+n)
    print('CurseForge ZIP matches all 12 pinned mods and exact loader version')

def install(root,pack,index,mods,data):
    data.mkdir(parents=True,exist_ok=True); statefile=data/'.pack-state.json'
    state=json.loads(statefile.read_text()) if statefile.exists() else {'mods':[],'configs':{}}
    wanted=[m for m in mods if m['side'] in ('both','server')]
    directory=data/'mods';directory.mkdir(exist_ok=True)
    allowed=set(state['mods'])|{m['filename'] for m in wanted}
    require(not any(p.name not in allowed for p in directory.glob('*.jar')),'Unmanaged JARs in /data/mods; move them aside before starting')
    cache=data/'.pack-cache';cache.mkdir(exist_ok=True)
    paths={m['filename']:fetch(m,cache) for m in wanted}
    dependencies(pack,wanted,paths,'server')
    # Validate all config conflicts before changing the active installation.
    entries=[e for e in index['files'] if e['file'].startswith('config/') and e.get('side','both') in ('both','server')]
    for e in entries:
        dest=data/e['file'];prev=state.get('configs',{}).get(e['file'])
        require(not dest.exists() or digest(dest) in {e['hash'],prev},'Managed config edited: '+e['file']+'; reconcile it with the pack before upgrading')
    for name in state['mods']:
        require(Path(name).name==name,'Unsafe prior installation state')
        if name not in {m['filename'] for m in wanted}: (directory/name).unlink(missing_ok=True)
    for m in wanted:
        temp=directory/(m['filename']+'.tmp');shutil.copyfile(paths[m['filename']],temp);os.replace(temp,directory/m['filename'])
    for e in entries:
        dest=data/e['file'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(root/e['file'],dest)
    new={'version':pack['version'],'mods':[m['filename'] for m in wanted],'configs':{e['file']:e['hash'] for e in entries}}
    tmp=statefile.with_suffix('.tmp');tmp.write_text(json.dumps(new,indent=2)+'\n');os.replace(tmp,statefile)
    if os.geteuid() == 0:
        owner=data.stat()
        for base in (directory,cache,data/'config'):
            if base.exists():
                os.chown(base,owner.st_uid,owner.st_gid)
                for child in base.rglob('*'):
                    if not child.is_symlink(): os.chown(child,owner.st_uid,owner.st_gid)
        os.chown(statefile,owner.st_uid,owner.st_gid)
    print('Installed pinned server pack v'+pack['version'])

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    sub=parser.add_subparsers(dest='command',required=True)
    v=sub.add_parser('validate');v.add_argument('--fetch',action='store_true');v.add_argument('--local-mods',type=Path)
    sub.add_parser('version');sub.add_parser('versions')
    z=sub.add_parser('check-zip');z.add_argument('zip',type=Path)
    i=sub.add_parser('install');i.add_argument('--data',type=Path,required=True)
    args=parser.parse_args();root=args.root.resolve();pack,index,mods=read_pack(root)
    if args.command=='version':print(pack['version'])
    elif args.command=='versions': print(pack['versions']['minecraft'],pack['versions']['forge'])
    elif args.command=='check-zip':check_zip(pack,mods,args.zip)
    elif args.command=='install':install(root,pack,index,mods,args.data)
    else:
        if args.fetch or args.local_mods:
            with tempfile.TemporaryDirectory() as t:
                paths={m['filename']:fetch(m,Path(t),args.local_mods) for m in mods}
                for side in ('server','client'):dependencies(pack,mods,paths,side)
        print('Validated 12 pinned mods, sides, loader, safe index, and integrity hashes')

if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('ERROR: '+str(exc),file=sys.stderr);sys.exit(1)
