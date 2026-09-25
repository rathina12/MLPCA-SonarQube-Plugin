from __future__ import annotations
import copy, json, os, subprocess, bisect
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = {
    "allocators": ["malloc", "calloc", "aligned_alloc", "valloc"],
    "reallocators": ["realloc", "reallocarray"],
    "deallocators": ["free"],
    "ownership_sinks": [],
    "max_paths_per_function": 64,
    "loop_unroll": 1,
    "include_rules": ["ML001","ML002","ML003","ML004","ML005","ML006","ML007","ML008"]
}

@dataclass
class Allocation:
    id: str
    allocator: str
    file: str
    line: int
    state: str = "ALLOCATED"
    aliases: set[str] = field(default_factory=set)

@dataclass
class Issue:
    rule: str; message: str; file: str; line: int; severity: str = "MAJOR"; function: str = ""; path: list[str] = field(default_factory=list)
    def key(self): return (self.rule, self.file, self.line, self.message)

@dataclass
class State:
    env: dict[str,str] = field(default_factory=dict)
    allocations: dict[str,Allocation] = field(default_factory=dict)
    path: list[str] = field(default_factory=list)
    terminated: bool = False
    def clone(self): return copy.deepcopy(self)

class Analyzer:
    def __init__(self, config: dict[str,Any]|None=None):
        self.config = dict(DEFAULT_CONFIG)
        if config: self.config.update(config)
        self.issues: list[Issue] = []
        self._alloc_seq = 0
        self.source = ""; self.file=""; self.lines=[]
        self.function_summaries: dict[str,dict[str,Any]] = {}

    def analyze_file(self, path: str, clang_args: list[str]|None=None) -> list[Issue]:
        self.file = str(Path(path).resolve())
        self.source = Path(path).read_text(encoding="utf-8", errors="replace")
        self._line_offsets=[0]
        for i,c in enumerate(self.source):
            if c=='\n': self._line_offsets.append(i+1)
        ast = self._clang_ast(path, clang_args or [])
        funcs = [n for n in self._walk(ast) if n.get('kind') in ('FunctionDecl','CXXMethodDecl') and self._is_user_node(n) and self._body(n)]
        self._build_summaries(funcs)
        before=len(self.issues)
        for fn in funcs: self._analyze_function(fn)
        return self.issues[before:]

    def _clang_ast(self, path, extra):
        lang = 'c++' if Path(path).suffix.lower() in ('.cc','.cpp','.cxx','.hpp','.hh','.hxx') else 'c'
        cmd=['clang','-x',lang,'-std=c++17' if lang=='c++' else '-std=c11','-Xclang','-ast-dump=json','-fsyntax-only',path,*extra]
        p=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        if p.returncode!=0:
            raise RuntimeError(f"Clang parse failed for {path}:\n{p.stderr}")
        return json.loads(p.stdout)

    def _walk(self,n):
        yield n
        for c in n.get('inner',[]): yield from self._walk(c)
    def _body(self,n):
        return next((x for x in reversed(n.get('inner',[])) if x.get('kind')=='CompoundStmt'),None)
    def _is_user_node(self,n):
        f=n.get('loc',{}).get('file') or n.get('range',{}).get('begin',{}).get('file')
        return f is None or os.path.abspath(f)==self.file
    def _line(self,n):
        for d in (n.get('loc',{}), n.get('range',{}).get('begin',{})):
            if 'line' in d: return int(d['line'])
            if 'offset' in d: return bisect.bisect_right(self._line_offsets,int(d['offset']))
        return 1
    def _callee(self,n):
        for x in self._walk(n):
            if x.get('kind')=='DeclRefExpr':
                r=x.get('referencedDecl',{})
                if r.get('kind') in ('FunctionDecl','CXXMethodDecl'): return r.get('name','')
        return ''
    def _var_refs(self,n):
        out=[]
        for x in self._walk(n):
            if x.get('kind')=='DeclRefExpr':
                r=x.get('referencedDecl',{})
                if r.get('kind') in ('VarDecl','ParmVarDecl'): out.append(r.get('name',''))
        return [x for x in out if x]
    def _direct_var(self,n):
        while n and n.get('kind') in ('ImplicitCastExpr','ParenExpr','CStyleCastExpr','CXXStaticCastExpr','CXXReinterpretCastExpr'):
            inn=n.get('inner',[]); n=inn[0] if inn else None
        if n and n.get('kind')=='DeclRefExpr':
            r=n.get('referencedDecl',{})
            if r.get('kind') in ('VarDecl','ParmVarDecl'): return r.get('name')
        return None

    def _allocation_call(self,n):
        for x in self._walk(n):
            if x.get('kind') in ('CallExpr','CXXNewExpr'):
                if x.get('kind')=='CXXNewExpr': return ('new[]' if x.get('isArray') else 'new',x)
                c=self._callee(x)
                if c in self.config['allocators'] or c in self.config['reallocators']: return (c,x)
        return None
    def _new_alloc(self,var,allocator,node,state):
        self._alloc_seq+=1; aid=f"A{self._alloc_seq}"
        a=Allocation(aid,allocator,self.file,self._line(node),aliases={var})
        state.allocations[aid]=a; state.env[var]=aid
        state.path.append(f"L{a.line}: {var} <- {allocator}")
        return aid
    def _emit(self,rule,msg,node,fn,state,severity='MAJOR'):
        if rule not in self.config['include_rules']: return
        self.issues.append(Issue(rule,msg,self.file,self._line(node),severity,fn,list(state.path)))

    def _build_summaries(self,funcs):
        for fn in funcs:
            params=[x.get('name','') for x in fn.get('inner',[]) if x.get('kind')=='ParmVarDecl']
            freed=set(); sinks=set(); returns_alloc=False
            body=self._body(fn)
            for x in self._walk(body):
                if x.get('kind')=='CallExpr':
                    c=self._callee(x); refs=self._var_refs(x)
                    if c in self.config['deallocators']:
                        for r in refs:
                            if r in params: freed.add(params.index(r))
                    if c in self.config['ownership_sinks']:
                        for r in refs:
                            if r in params: sinks.add(params.index(r))
                if x.get('kind')=='ReturnStmt' and self._allocation_call(x): returns_alloc=True
            self.function_summaries[fn.get('name','')]={'frees':freed,'sinks':sinks,'returns_alloc':returns_alloc}

    def _analyze_function(self,fn):
        name=fn.get('name','<anonymous>'); init=State(path=[f"enter {name}()"])
        states=self._exec_stmt(self._body(fn),[init],name)
        for s in states:
            if not s.terminated: self._finish_state(s,fn,name,'function exit')

    def _finish_state(self,s,node,fn,reason):
        for aid,a in list(s.allocations.items()):
            if a.state=='ALLOCATED' and a.aliases:
                rule='ML003' if reason=='early return' else 'ML001'
                self._emit(rule,f"Memory allocated by {a.allocator} is not released before {reason}.",node,fn,s)
                a.state='LEAKED'

    def _limit(self,states):
        maxp=int(self.config.get('max_paths_per_function',64))
        uniq={}
        for s in states:
            sig=(s.terminated,tuple(sorted(s.env.items())),tuple(sorted((k,a.state,tuple(sorted(a.aliases))) for k,a in s.allocations.items())))
            uniq.setdefault(sig,s)
        return list(uniq.values())[:maxp]

    def _exec_stmt(self,node,states,fn):
        if not node: return states
        k=node.get('kind')
        if k=='CompoundStmt':
            cur=states
            for ch in node.get('inner',[]):
                active=[s for s in cur if not s.terminated]; done=[s for s in cur if s.terminated]
                cur=done+self._exec_stmt(ch,active,fn)
                cur=self._limit(cur)
            return cur
        if k=='DeclStmt':
            out=[]
            for s in states:
                for d in node.get('inner',[]):
                    if d.get('kind')!='VarDecl': continue
                    v=d.get('name',''); ac=self._allocation_call(d)
                    refs=self._var_refs(d)
                    if ac: self._new_alloc(v,ac[0],d,s)
                    elif refs:
                        src=next((r for r in refs if r!=v and r in s.env),None)
                        if src:
                            aid=s.env[src]; s.env[v]=aid; s.allocations[aid].aliases.add(v); s.path.append(f"L{self._line(d)}: alias {v} -> {src}")
                out.append(s)
            return out
        if k=='IfStmt':
            inn=node.get('inner',[]); then=inn[1] if len(inn)>1 else None; els=inn[2] if len(inn)>2 else None
            out=[]
            for s in states:
                t=s.clone(); t.path.append(f"L{self._line(node)}: if=true")
                f=s.clone(); f.path.append(f"L{self._line(node)}: if=false")
                out += self._exec_stmt(then,[t],fn)
                out += self._exec_stmt(els,[f],fn) if els else [f]
            return self._limit(out)
        if k in ('ForStmt','WhileStmt','DoStmt'):
            body=next((x for x in reversed(node.get('inner',[])) if x.get('kind') in ('CompoundStmt','IfStmt','CallExpr','BinaryOperator','DeclStmt')),None)
            out=[]
            for s in states:
                z=s.clone(); z.path.append(f"L{self._line(node)}: loop skipped"); out.append(z)
                o=s.clone(); o.path.append(f"L{self._line(node)}: loop representative iteration"); out += self._exec_stmt(body,[o],fn)
            return self._limit(out)
        if k=='ReturnStmt':
            out=[]
            for s in states:
                refs=self._var_refs(node)
                for v in refs:
                    aid=s.env.get(v)
                    if aid and s.allocations[aid].state=='ALLOCATED':
                        s.allocations[aid].state='ESCAPED'; s.path.append(f"L{self._line(node)}: ownership returned via {v}")
                self._finish_state(s,node,fn,'early return')
                s.terminated=True; s.path.append(f"L{self._line(node)}: return")
                out.append(s)
            return out
        if k=='BinaryOperator' and node.get('opcode')=='=':
            inn=node.get('inner',[])
            if len(inn)>=2:
                lhs=self._direct_var(inn[0]); rhs=inn[1]
                for s in states:
                    if not lhs: continue
                    old=s.env.get(lhs); ac=self._allocation_call(rhs); rhsrefs=self._var_refs(rhs)
                    if old and s.allocations.get(old) and s.allocations[old].state=='ALLOCATED':
                        s.allocations[old].aliases.discard(lhs)
                        if not s.allocations[old].aliases:
                            self._emit('ML002',f"Pointer '{lhs}' is overwritten before its previous allocation is released.",node,fn,s)
                            s.allocations[old].state='LEAKED'
                    if ac:
                        if ac[0] in self.config['reallocators'] and rhsrefs and lhs in rhsrefs:
                            self._emit('ML008',f"Direct assignment of {ac[0]} to '{lhs}' can lose the original allocation on failure.",node,fn,s,'MINOR')
                        self._new_alloc(lhs,ac[0],node,s)
                    else:
                        src=next((r for r in rhsrefs if r in s.env),None)
                        if src:
                            aid=s.env[src]; s.env[lhs]=aid; s.allocations[aid].aliases.add(lhs)
            return states
        if k=='CallExpr':
            c=self._callee(node); refs=self._var_refs(node)
            for s in states:
                if c in self.config['deallocators']:
                    v=next((r for r in reversed(refs) if r in s.env),None)
                    if v:
                        aid=s.env[v]; a=s.allocations.get(aid)
                        if a:
                            if a.state=='FREED': self._emit('ML006',f"Double free of allocation referenced by '{v}'.",node,fn,s,'CRITICAL')
                            elif a.allocator in ('new','new[]'):
                                self._emit('ML007',f"Allocation created with {a.allocator} is released with {c}.",node,fn,s,'CRITICAL')
                                a.state='FREED'
                            else: a.state='FREED'
                            s.path.append(f"L{self._line(node)}: {c}({v})")
                    return states
                if c in self.config['ownership_sinks']:
                    for v in refs:
                        aid=s.env.get(v)
                        if aid: s.allocations[aid].state='ESCAPED'; s.path.append(f"L{self._line(node)}: ownership escaped via {c}({v})")
                summ=self.function_summaries.get(c)
                if summ:
                    args=self._call_args(node)
                    for idx in summ['frees']:
                        if idx < len(args):
                            vars_=self._var_refs(args[idx]); v=next((r for r in vars_ if r in s.env),None)
                            if v:
                                aid=s.env[v]; a=s.allocations.get(aid)
                                if a and a.state=='ALLOCATED': a.state='FREED'; s.path.append(f"L{self._line(node)}: {c} frees {v}")
                    for idx in summ['sinks']:
                        if idx < len(args):
                            for v in self._var_refs(args[idx]):
                                aid=s.env.get(v)
                                if aid: s.allocations[aid].state='ESCAPED'
            return states
        if k=='CXXDeleteExpr':
            refs=self._var_refs(node)
            for s in states:
                v=next((r for r in refs if r in s.env),None)
                if v:
                    aid=s.env[v]; a=s.allocations[aid]
                    is_array=bool(node.get('isArrayForm'))
                    expected='new[]' if is_array else 'new'
                    if a.state=='FREED': self._emit('ML006',f"Double delete of '{v}'.",node,fn,s,'CRITICAL')
                    elif a.allocator!=expected: self._emit('ML007',f"Mismatched allocation/deallocation: {a.allocator} with {'delete[]' if is_array else 'delete'}.",node,fn,s,'CRITICAL')
                    a.state='FREED'
            return states
        return states

    def _call_args(self,node):
        inn=node.get('inner',[])
        return inn[1:] if len(inn)>1 else []


def issues_to_sonar(issues:list[Issue], base_dir:str) -> dict[str,Any]:
    out=[]
    seen=set(); base=Path(base_dir).resolve()
    for i in issues:
        if i.key() in seen: continue
        seen.add(i.key())
        try: rel=str(Path(i.file).resolve().relative_to(base)).replace('\\','/')
        except Exception: rel=i.file.replace('\\','/')
        out.append({
            "engineId":"mlpca", "ruleId":i.rule, "severity":i.severity, "type":"BUG",
            "primaryLocation":{"message":i.message,"filePath":rel,"textRange":{"startLine":max(1,i.line),"endLine":max(1,i.line)}},
            "effortMinutes":10,
            "secondaryLocations":[]
        })
    return {"issues":out}
