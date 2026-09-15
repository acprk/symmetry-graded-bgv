#!/usr/bin/env python3
import re,sys,glob,os
rows=[]
for f in sorted(glob.glob(os.path.join(os.path.dirname(__file__),'logs','set*_pass*.log'))):
    txt=open(f,errors='replace').read()
    for blk in re.split(r'(?=########## SET )',txt)[1:]:
        h=re.match(r'########## SET (\d+) p=(\d+) m=(\d+) d=(\d+) :: (\w+) :: aux=(-?\d+) :: pass(\d+)',blk)
        if not h: continue
        idx,p,m,d,mode,aux,ps=h.groups()
        t=re.search(r'time for linear1 = ([\d.]+), linear2 = ([\d.]+), extract = ([\d.]+), total = ([\d.]+)',blk)
        b=re.search(r'bits for linear1 = ([\d.]+), linear2 = ([\d.]+), extract = ([\d.]+), min cap = ([\d.]+), after cap = ([\d.]+)',blk)
        sec=re.search(r'security level = ([\d.]+)',blk); bits=re.search(r'number of bits = (\d+)',blk)
        ns=re.search(r'nslots = (\d+)',blk); B=re.search(r'bound on I = ([\d.]+)',blk)
        deg=re.search(r'deg of poly for non-power-of-p aux is (\d+)',blk)
        ann=re.search(r'HELIB_AUX_ORDER4_EVAL enabled: order=(\d+), deg\(P\)=(\d+), terms\(P\)=(\d+), deg\(Q\)=(\d+)',blk)
        skipped='skipped' in blk
        ex=re.search(r'exit=(\d+)',blk); wall=re.search(r'WALL=([\d.]+)',blk)
        rows.append(dict(idx=int(idx),p=int(p),m=int(m),d=int(d),mode=mode,aux=aux,pas=ps,
            lin=(float(t.group(1))+float(t.group(2))) if t else None, ext=float(t.group(3)) if t else None, tot=float(t.group(4)) if t else None,
            capdrop=float(b.group(3)) if b else None, aftercap=float(b.group(5)) if b else None,
            sec=sec.group(1) if sec else None, bits=bits.group(1) if bits else None, nslots=ns.group(1) if ns else None,
            B=B.group(1) if B else None, degP=deg.group(1) if deg else None, order=ann.group(1) if ann else None, degQ=ann.group(4) if ann else None,
            skipped=skipped, exit=ex.group(1) if ex else '?', wall=wall.group(1) if wall else None))
print("idx p m d mode aux pass | lin(s) extract(s) total(s) | extract/lin | cap_drop after_cap | sec bits nslots B degP order degQ skipped exit wall")
for r in rows:
    norm=(r['ext']/r['lin']) if (r['ext'] and r['lin']) else None
    print(f"{r['idx']:2d} {r['p']:6d} {r['m']:6d} {r['d']:2d} {r['mode']:16s} {r['aux']:>4} {r['pas']} | "
          f"{(r['lin'] or 0):7.2f} {(r['ext'] or 0):8.2f} {(r['tot'] or 0):8.2f} | {(norm or 0):5.2f} | "
          f"{(r['capdrop'] or 0):6.1f} {(r['aftercap'] or 0):7.1f} | {r['sec']} {r['bits']} {r['nslots']} {r['B']} {r['degP']} {r['order']} {r['degQ']} {r['skipped']} {r['exit']} {r['wall']}")
