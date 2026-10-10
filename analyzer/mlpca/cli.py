from __future__ import annotations
import argparse, json, os, shlex
from pathlib import Path
from .core import Analyzer, DEFAULT_CONFIG, issues_to_sonar

def load_config(path):
    cfg=dict(DEFAULT_CONFIG)
    if path and Path(path).exists(): cfg.update(json.loads(Path(path).read_text()))
    return cfg

def compile_db_args(root):
    """Read compilation commands, normalizing file paths and argument order.

    The clang invocation already supplies -x, -std, -fsyntax-only and the
    source file, so discard conflicting compiler/driver-only arguments.
    """
    p = Path(root) / 'compile_commands.json'
    if not p.is_file():
        return {}
    rows = json.loads(p.read_text(encoding='utf-8'))
    out = {}
    for row in rows:
        cwd = Path(row.get('directory', str(root))).resolve()
        src = Path(row['file'])
        source = (cwd / src).resolve() if not src.is_absolute() else src.resolve()
        raw = row.get('arguments') or shlex.split(row.get('command', ''))
        if not raw:
            continue
        safe = []
        skip_next = False
        for arg in raw[1:]:
            if skip_next:
                skip_next = False
                continue
            if arg in ('-o', '-MF', '-MT', '-MQ', '-x', '-std',
                       '-include-pch', '-isysroot', '--sysroot'):
                skip_next = True
                continue
            if arg in ('-c', '-S', '-E', '-fsyntax-only'):
                continue
            if arg.startswith(('-o', '-MF', '-MT', '-MQ', '-std=', '-x')):
                continue
            candidate = Path(arg)
            if arg == row['file'] or (not arg.startswith('-')
                                      and (cwd / candidate).resolve() == source):
                continue
            safe.append(arg)
        # Preserve the compilation directory's relative include paths.
        safe.insert(0, '-I' + str(cwd))
        out[str(source)] = safe
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
