#!/usr/bin/env python3
"""Aggregate newexp logs: last *verified* block per (idx, mode, pass, h) -> results.csv (+ stdout table)."""
import re,glob,os,csv,sys
here=os.path.dirname(os.path.abspath(__file__))
rows={}
for f in sorted(x for x in glob.glob(os.path.join(here,'logs','set*_pass*.log')) if 'before' not in x):
    txt=open(f,errors='replace').read()
    for blk in re.split(r'(?=########## SET )',txt)[1:]:
        h=re.match(r'########## SET (\d+) p=(\d+) m=(\d+) d=(\d+) :: (\w+) :: aux=(-?\d*) :: pass(\d+)(?: :: h=(\d+))?',blk)
        if not h: continue
        idx,p,m,d,mode,aux,ps,hw=h.groups(); hw=int(hw or 12)
        t=re.search(r'time for linear1 = ([\d.]+), linear2 = ([\d.]+), extract = ([\d.]+), total = ([\d.]+)',blk)
        b=re.search(r'bits for linear1 = ([\d.]+), linear2 = ([\d.]+), extract = ([\d.]+), min cap = ([\d.]+), after cap = ([\d.]+)',blk)
        g=lambda pat,cast=float: (cast(re.search(pat,blk).group(1)) if re.search(pat,blk) else None)
        r=dict(idx=int(idx),p=int(p),m=int(m),d=int(d),h=hw,mode=mode,aux=aux,pas=int(ps),
            lin=(float(t.group(1))+float(t.group(2))) if t else None, ext=float(t.group(3)) if t else None, tot=float(t.group(4)) if t else None,
            capdrop=float(b.group(3)) if b else None, aftercap=float(b.group(5)) if b else None,
            sec=g(r'security level = ([\d.]+)'), bits=g(r'number of bits = (\d+)',int), nslots=g(r'nslots = (\d+)',int),
            phim=g(r'phi\(m\) = (\d+)',int), B=g(r'bound on I = ([\d.]+)'), degP=g(r'deg of poly for non-power-of-p aux is (\d+)',int),
            order=g(r'HELIB_AUX_ORDER4_EVAL enabled: order=(\d+)',int), degQ=g(r'deg\(Q\)=(\d+)',int),
            degC=g(r'norm form c=\d+ degC=(\d+)',int), cnorm=g(r'norm form c=(\d+)',int), search=g(r'\(search ([\d.]+)s\)'),
            normonly='HELIB_NORMONLY' in blk, composed_active='HELIB_COMPOSED_EVAL active' in blk,
            qks=g(r'final log2\(qks\) = ([\d.]+)'), R=g(r'final log2\(R\) = ([\d.]+)'),
            ok=('everything ok' in blk), exit=g(r'exit=(\d+)',int), wall=g(r'WALL=([\d.]+)'))
        r['B']=int(r['B']+0.999) if r['B'] else None
        r['valid']=bool(r['ok'] and r['exit']==0 and (r['mode']!='NORMONLY' or r['normonly']) and ('COMPOSED' not in r['mode'] or r['composed_active']))
        key=(r['idx'],r['mode'],r['pas'],hw)
        if r['valid'] or key not in rows: rows[key]=r     # last valid block wins; keep a failure only if nothing valid yet
rows=[rows[k] for k in sorted(rows)]
fields=list(rows[0].keys())
with open(os.path.join(here,'results.csv'),'w',newline='') as fh:
    w=csv.DictWriter(fh,fieldnames=fields); w.writeheader(); [w.writerow(r) for r in rows]
if '-q' not in sys.argv:
    print("idx p d h mode pass valid | lin ext tot | capdrop | degC")
    for r in rows: print(f"{r['idx']:2d} {r['p']:6d} {r['d']:2d} {r['h']:2d} {r['mode']:16s} {r['pas']} {int(r['valid'])} | {(r['lin'] or 0):7.2f} {(r['ext'] or 0):7.2f} {(r['tot'] or 0):7.2f} | {(r['capdrop'] or 0):6.1f} | {r['degC']}")
