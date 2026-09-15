#!/usr/bin/python3
"""LaTeX tables from results.csv + security/est_*.json.  Usage: make_tables.py > tables.tex"""
import csv,json,glob,os,sys
here=os.path.dirname(os.path.abspath(__file__))
R=[r for r in csv.DictReader(open(os.path.join(here,'results.csv'))) if r['valid']=='True']
S={}
for f in glob.glob(os.path.join(here,'security','est_*.json')):
    for row in json.load(open(f)): S[(row['p'],row['m'],row['h'])]=row
meta={}
for f in ('sets.tsv','sets128.tsv','cases.tsv'):
    for l in open(os.path.join(here,f)):
        if l.startswith('#'): continue
        c=l.rstrip('\n').split('\t'); meta[int(c[0])]=dict(p=int(c[1]),cls=int(c[2]),m=int(c[3]),q1=int(c[4]),q2=int(c[5]),d=int(c[6]),ns=int(c[7]),aux4=c[9],aux6=c[10])
def get(idx,mode,h,pas=None):
    c=[r for r in R if int(r['idx'])==idx and r['mode']==mode and int(r['h'])==h and (pas is None or int(r['pas'])==pas)]
    return sorted(c,key=lambda r:int(r['pas']))[0] if c else None
def f1(x): return f"{x:.1f}" if x is not None else "--"
def f2(x): return f"{x:.2f}" if x is not None else "--"
def rstar(cls,idx,h):
    if cls==7: return 6
    if cls==5: return 4
    # p ≡ 1: both exist; report which one is faster composed (should be r=4 by rho: box rho=4 vs hexagon rho=6? -> selector says 6 by rho, but order-4 box has more points). print both
    return '4/6'
def params_table(h,idxs,label,caption):
    out=[r"\begin{table}[!htb]\centering\caption{%s}\label{%s}\renewcommand{\arraystretch}{1.15}\footnotesize\setlength{\tabcolsep}{3.5pt}"%(caption,label),
         r"\resizebox{\linewidth}{!}{\begin{tabular}{@{}rcrrrrrrrrrr@{}}\toprule",
         r"\textbf{$p$} & \textbf{$p\bmod12$} & \textbf{$m=q_1q_2$} & \textbf{$\varphi(m)$} & \textbf{$d$} & \textbf{Slots} & \textbf{$B$} & \textbf{$r^\star$} & \textbf{Chain} & \textbf{$\lambda_{\mathrm{main}}$} & \textbf{$\lambda_{\mathrm{encap}}$} & \textbf{$\lambda^\ast$}\\\midrule"]
    for i in idxs:
        m=meta[i]; b=get(i,'BASELINE',h)
        if not b: continue
        s=S.get((m['p'],m['m'],h))
        lm=s and s['main'].get('min'); le=s and s['encap'].get('min'); ls_=s and s.get('lam_min')
        out.append(f"{m['p']} & {m['cls']} & ${m['q1']}\\cdot{m['q2']}$ & {b['phim']} & {m['d']} & {m['ns']} & {b['B']} & {rstar(m['cls'],i,h)} & {b['bits']} & {f1(lm)} & {f1(le)} & {f1(ls_)}\\\\")
    out+=[r"\bottomrule\end{tabular}}\end{table}"]; return "\n".join(out)
def e2e_table(h,idxs,label,caption):
    out=[r"\begin{table}[!htb]\centering\caption{%s}\label{%s}\renewcommand{\arraystretch}{1.2}\footnotesize\setlength{\tabcolsep}{3pt}"%(caption,label),
         r"\resizebox{\linewidth}{!}{\begin{tabular}{@{}rrrccccccccc@{}}\toprule",
         r" & & & \multicolumn{4}{c}{\textbf{Extract (s)}} & \multicolumn{2}{c}{\textbf{Total (s)}} & \multicolumn{2}{c}{\textbf{Speedup}} & \multicolumn{2}{c}{\textbf{Capacity (bits)}}\\",
         r"\cmidrule(lr){4-7}\cmidrule(lr){8-9}\cmidrule(lr){10-11}\cmidrule(lr){12-13}",
         r"\textbf{$p$} & \textbf{$d$} & \textbf{$\deg C$} & Ma et al. & Norm map & Order-$r^\star$ & \textbf{Composed} & Ma et al. & \textbf{Composed} & \textbf{Extract} & \textbf{Total} & Ma et al. & \textbf{Composed}\\\midrule"]
    for i in idxs:
        m=meta[i]; b=get(i,'BASELINE',h)
        if not b: continue
        z=get(i,'NORMONLY',h)
        if m['cls']==7: sc,cp=get(i,'ORDER6',h),get(i,'ORDER6_COMPOSED',h)
        else:
            c4,c6=get(i,'ORDER4_COMPOSED',h),get(i,'ORDER6_COMPOSED',h)
            cp=min([x for x in (c4,c6) if x],key=lambda r:float(r['ext'])) if (c4 or c6) else None
            sc=get(i,'ORDER4',h) if (cp is c4) else get(i,'ORDER6',h)
        E=lambda r: float(r['ext']) if r else None; T=lambda r: float(r['tot']) if r else None
        sp=E(b)/E(cp) if cp else None; spt=T(b)/T(cp) if cp else None
        G=lambda x: "\\cellcolor{green!15}$\\mathbf{"+x+"}$"
        TX="\\times"
        cells=[str(m['p']),str(m['d']),cp['degC'] if cp else '--',"$%s$"%f1(E(b)),"$%s$"%f1(E(z)),"$%s$"%f1(E(sc)),G(f1(E(cp))),
               "$%s$"%f1(T(b)),G(f1(T(cp))),G(f2(sp)+TX),G(f2(spt)+TX),"$%s$"%f1(float(b['capdrop'])),"$%s$"%(f1(float(cp['capdrop'])) if cp else '--')]
        out.append(" & ".join(cells)+"\\\\")
    out+=[r"\bottomrule\end{tabular}}\end{table}"]; return "\n".join(out)
h12=[i for i in sorted(meta) if i<=28]; h26=[i for i in sorted(meta) if i>=29]
print(params_table(12,h12,'tab:params80',r"Parameter sets, encapsulated key weight $h=12$ ($h^\prime=120$). ``chain'' is the modulus \HElib{} built (bits); $\lambda$ are Lattice-Estimator minima over six attacks at that chain (main key) and at $q_{\mathrm{boot}}$ (encapsulated key); $\lambda^\ast=\min$."))
print(e2e_table(12,h12,'tab:e2e80',r'End-to-end thin bootstrapping at $h=12$: digit-extraction and total times, speedup of the composed evaluator over Ma et al., and capacity consumed by digit extraction.'))
print(params_table(26,h26,'tab:params128',r'Parameter sets at $h=26$.'))
print(e2e_table(26,h26,'tab:e2e128',r'End-to-end thin bootstrapping at $h=26$.'))
