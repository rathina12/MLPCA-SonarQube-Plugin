from __future__ import annotations
import argparse, json, os, shlex
from pathlib import Path
from .core import Analyzer, DEFAULT_CONFIG, issues_to_sonar

def load_config(path):
    cfg=dict(DEFAULT_CONFIG)
    if path and Path(path).exists(): cfg.update(json.loads(Path(path).read_text()))
    return cfg

def compile_db_args(root):
    p=Path(root)/'compile_commands.json'
    if not p.exists(): return {}
    rows=json.loads(p.read_text())
    out={}
    for r in rows:
        f=str(Path(r['file']).resolve())
        args=r.get('arguments') or shlex.split(r.get('command',''))
        safe=[]; skip=False
        for a in args[1:]:
            if skip: skip=False; continue
            if a in ('-o','-MF','-MT','-MQ'): skip=True; continue
            if a==r['file'] or os.path.abspath(a)==f: continue
            if a.startswith('-c'): continue
            safe.append(a)
        out[f]=safe
    return out

def main():
    ap=argparse.ArgumentParser(description='MLPCA: partial-call-path memory leak analyzer for C/C++')
    ap.add_argument('path', nargs='?', default='.')
    ap.add_argument('--config', default='mlpca.json')
    ap.add_argument('--output', default='.mlpca/issues.json')
    ap.add_argument('--fail-on-issues', action='store_true')
    ns=ap.parse_args()
    root=Path(ns.path).resolve(); cfg=load_config(ns.config); db=compile_db_args(root)
    files=[root] if root.is_file() else [p for p in root.rglob('*') if p.suffix.lower() in {'.c','.cc','.cpp','.cxx'} and not any(x in p.parts for x in ('.git','build','node_modules','vendor'))]
    analyzer=Analyzer(cfg); failures=[]
    for f in files:
        try: analyzer.analyze_file(str(f),db.get(str(f.resolve()),[]))
        except Exception as e: failures.append({'file':str(f),'error':str(e)})
    payload=issues_to_sonar(analyzer.issues,str(root if root.is_dir() else root.parent))
    payload['mlpca']={'analyzedFiles':len(files),'issues':len(payload['issues']),'parseFailures':failures}
    out=Path(ns.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(payload,indent=2))
    print(f"MLPCA analyzed {len(files)} file(s): {len(payload['issues'])} issue(s), {len(failures)} parse failure(s).")
    if failures:
        for x in failures: print(f"WARN {x['file']}: {x['error'].splitlines()[0]}")
    return 2 if ns.fail_on_issues and payload['issues'] else (1 if failures else 0)

if __name__=='__main__': raise SystemExit(main())
