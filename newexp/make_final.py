#!/usr/bin/python3
"""Final §6 artefacts: tables.tex (h=12 and h=26 end-to-end tables) and two figures. Pass rule: for each ring use the
pass whose baseline linear-transform time is smallest (lowest machine load); all arms of a ring come from that pass."""
import csv,json,glob,os,math,sys
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
here=os.path.dirname(os.path.abspath(__file__)); out=sys.argv[1] if len(sys.argv)>1 else here
R=[r for r in csv.DictReader(open(os.path.join(here,'results.csv'))) if r['valid']=='True']
S={}
for f in glob.glob(os.path.join(here,'security','est_*.json')):
    for row in json.load(open(f)): S[(row['p'],row['m'],row['h'])]=row
meta={}
for f in ('sets.tsv','sets128.tsv','cases.tsv'):
    for l in open(os.path.join(here,f)):
        if l.startswith('#'): continue
        c=l.rstrip('\n').split('\t'); meta[int(c[0])]=dict(p=int(c[1]),cls=int(c[2]),m=int(c[3]),q1=int(c[4]),q2=int(c[5]),d=int(c[6]),ns=int(c[7]))
def arms(i,h):
    rows=[r for r in R if int(r['idx'])==i and int(r['h'])==h]
    passes=sorted({int(r['pas']) for r in rows if r['mode']=='BASELINE'},key=lambda ps: float([r for r in rows if r['mode']=='BASELINE' and int(r['pas'])==ps][0]['lin']))
    if not passes: return None
    ps=passes[0]; A={r['mode']:r for r in rows if int(r['pas'])==ps}
    if 'BASELINE' not in A: return None
    m=meta[i]
    if m['cls']==7: sc,cp,rs=A.get('ORDER6'),A.get('ORDER6_COMPOSED'),6
    else:
        c4,c6=A.get('ORDER4_COMPOSED'),A.get('ORDER6_COMPOSED')
        cp=min([x for x in (c4,c6) if x],key=lambda r:float(r['ext'])) if (c4 or c6) else None
        rs=4 if (cp is c4) else 6; sc=A.get('ORDER4') if rs==4 else A.get('ORDER6')
    if not (sc and cp): return None
    b=A['BASELINE']; s=S.get((m['p'],m['m'],h))
    return dict(idx=i,p=m['p'],cls=m['cls'],m=m['m'],q1=m['q1'],q2=m['q2'],d=m['d'],ns=m['ns'],h=h,pas=ps,B=int(b['B']),chain=int(b['bits']),
        lam=s['lam_min'] if s else None,lam_main=s['main']['min'] if s else None,lam_enc=s['encap']['min'] if s else None,rs=rs,degC=int(cp['degC']),lin=float(b['lin']),
        eb=float(b['ext']),es=float(sc['ext']),ec=float(cp['ext']),tb=float(b['tot']),tc=float(cp['tot']),capb=float(b['capdrop']),capc=float(cp['capdrop']))
rows12=[x for x in (arms(i,12) for i in sorted(meta) if i<=28) if x]
rows26=[x for x in (arms(i,26) for i in sorted(meta) if i>=29) if x]
json.dump(dict(h12=rows12,h26=rows26),open(os.path.join(out,'final_rows.json'),'w'),indent=1)
G=lambda x: "\\cellcolor{green!15}$\\mathbf{"+x+"}$"
def table(rows,label,caption):
    L=[r"\begin{table}[t]\centering\caption{%s}\label{%s}\renewcommand{\arraystretch}{1.12}\setlength{\tabcolsep}{2.5pt}\footnotesize"%(caption,label),
       r"\resizebox{\linewidth}{!}{\begin{tabular}{@{}lrrrrrrc|r|rrr|rr|rr@{}}\toprule",
       r" & & & & & \multicolumn{2}{c}{\textbf{security}} & & \textbf{lin.} & \multicolumn{3}{c|}{\textbf{Digit extraction (s)}} & \multicolumn{2}{c|}{\textbf{Total (s)}} & \multicolumn{2}{c}{\textbf{Speedup}}\\",
       r"$p$ ($p\bmod12$) & $m$ & $d$ & slots & chain & main & encap. & $r^\star$ & (s) & Ma et al. & order-$r^\star$ & \textbf{composed} & Ma et al. & \textbf{composed} & extract & total\\\midrule"]
    for r in rows:
        tag = "\\,$^\\dagger$" if r['idx'] in (3,4) else ""
        L.append(" & ".join([f"${r['p']}$ ({r['cls']}){tag}",f"${r['m']}$",f"${r['d']}$",f"${r['ns']}$",f"${r['chain']}$",f"${r['lam_main']:.1f}$" if r['lam_main'] else "--",f"${r['lam_enc']:.1f}$" if r['lam_enc'] else "--",f"${r['rs']}$",f"${r['lin']:.0f}$",
            f"${r['eb']:.1f}$",f"${r['es']:.1f}$",G(f"{r['ec']:.1f}"),f"${r['tb']:.1f}$",G(f"{r['tc']:.1f}"),G(f"{r['eb']/r['ec']:.2f}\\times"),G(f"{r['tb']/r['tc']:.2f}\\times")])+"\\\\")
    L+=[r"\bottomrule\end{tabular}}\end{table}"]; return "\n".join(L)
cap12=(r"Thin bootstrapping on $17$ general cyclotomic rings at $h=12$ ($h'=120$, $B=17$; $B=16$ at $p=4423$): built chain (bits), "
       r"security $\lambda^\ast$, selected order, linear-transform time (load reference), and digit-extraction and total times of Ma et al.'s evaluator, "
       r"the order-$r^\star$ filter with Paterson--Stockmeyer, and the composed $(r^\star,d)$ evaluator, run back to back on one ring, chain, key and support. "
       r"$^\dagger$Ma et al.'s own sets IV and V.")
cap26=(r"The same measurement at $h=26$ ($B=24$, $\deg P_A=2399$) on rings of the $128$-bit tier.")
open(os.path.join(out,'tables_final.tex'),'w').write(table(rows12,'tab:e2e',cap12)+"\n\n"+table(rows26,'tab:e2e128',cap26)+"\n")
# ---- figures ----
plt.rcParams.update({'font.size':7.5,'axes.labelsize':8,'legend.fontsize':7,'xtick.labelsize':6.5,'ytick.labelsize':7})
D=sorted(rows12,key=lambda r:(r['d'],r['p']))
fig,ax=plt.subplots(figsize=(3.4,1.45)); x=range(len(D)); w=0.27
ax.bar([i-w for i in x],[r['eb'] for r in D],w,label='Ma et al. (odd filter, P--S)',color='#9e9e9e')
ax.bar([i for i in x],[r['es'] for r in D],w,label='order-$r^\\star$ filter, P--S',color='#5b9bd5')
ax.bar([i+w for i in x],[r['ec'] for r in D],w,label='composed $(r^\\star,d)$',color='#c0392b')
ax.set_xticks(list(x)); ax.set_xticklabels([f"{r['p']} ({r['d']})" for r in D],rotation=90,fontsize=6)
ax.set_ylabel('digit extraction (s)'); ax.set_xlabel('prime $p$ (slot degree $d$)'); ax.text(-0.2,1.27,'(a)',transform=ax.transAxes,fontsize=8)
ax.legend(frameon=False,loc='upper center',ncol=2,bbox_to_anchor=(0.55,1.32)); ax.set_ylim(0,max(r['eb'] for r in D)*1.08)
fig.tight_layout(); fig.savefig(os.path.join(out,'fig_extract_time.pdf'))
fig,ax=plt.subplots(figsize=(3.4,1.45))
mk={7:('o','$p\\equiv7$: order six'),1:('s','$p\\equiv1$: order four'),5:('^','$p\\equiv5$: order four')}
for c,(m_,lab) in mk.items():
    Dc=[r for r in D if r['cls']==c]
    if Dc: ax.scatter([r['d'] for r in Dc],[r['eb']/r['ec'] for r in Dc],marker=m_,s=24,color='#c0392b',label='composed, '+lab,zorder=3)
    if Dc: ax.scatter([r['d'] for r in Dc],[r['eb']/r['es'] for r in Dc],marker=m_,s=24,facecolors='none',edgecolors='#5b9bd5',zorder=3)
D26=rows26
if D26: ax.scatter([r['d'] for r in D26],[r['eb']/r['ec'] for r in D26],marker='D',s=22,color='#2e8b57',label='composed, $h=26$',zorder=3)
ax.scatter([],[],marker='o',facecolors='none',edgecolors='#5b9bd5',label='order-$r^\\star$ filter alone')
ax.axhline(1,color='k',lw=0.5,ls=':'); ax.set_xscale('log',base=2); ax.set_xticks([2,4,8,16]); ax.set_xticklabels(['2','4','8','16'])
ax.set_xlabel('slot degree $d=\\mathrm{ord}_m(p)$'); ax.set_ylabel('speedup over Ma et al.'); ax.text(-0.2,1.02,'(b)',transform=ax.transAxes,fontsize=8); ax.legend(frameon=False,loc='upper left')
fig.tight_layout(); fig.savefig(os.path.join(out,'fig_speedup_vs_d.pdf'))
print(len(rows12),"rings at h=12;",len(rows26),"at h=26")
for r in rows12+rows26: print(r['p'],r['cls'],'d',r['d'],'h',r['h'],'pass',r['pas'],'lam',r['lam'] and round(r['lam'],1),'ext %.1f/%.1f/%.1f'%(r['eb'],r['es'],r['ec']),'tot %.1f/%.1f'%(r['tb'],r['tc']),'sp %.2f/%.2f'%(r['eb']/r['ec'],r['tb']/r['tc']))
