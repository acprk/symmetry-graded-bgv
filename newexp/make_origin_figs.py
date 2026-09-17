#!/usr/bin/python3
"""Origin-style figures for §6: (a) grouped bars on six representative rings; (b) speedup vs slot degree for all rings."""
import json,os,sys
try:
    import matplotlib
except ImportError:
    sys.exit("matplotlib is required for the figures in this script. On this machine it lives in\n"
             "/usr/bin/python3, not in every interpreter on PATH; run\n"
             "    /usr/bin/python3 %s\n"
             "or install it (pip install matplotlib)." % os.path.basename(__file__))
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import AutoMinorLocator
here=os.path.dirname(os.path.abspath(__file__)); out=sys.argv[1] if len(sys.argv)>1 else here
d=json.load(open(os.path.join(here,'final/final_rows.json'))); rows=d['h12']; rows26=d['h26']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.linewidth':1.1,'xtick.direction':'in','ytick.direction':'in',
    'xtick.major.size':4,'ytick.major.size':4,'xtick.minor.size':2,'ytick.minor.size':2,'xtick.top':True,'ytick.right':True,
    'legend.frameon':False,'axes.labelsize':10,'legend.fontsize':8.5})
C=['#7f7f7f','#2f6fb2','#c8102e']; H=['','//','xx']
sel=[8191,65537,19183,2521,13457]
S=[r for p in sel for r in rows if r['p']==p]
S.append([r for r in rows26 if r['p']==8101][0])
fig,ax=plt.subplots(figsize=(4.3,2.45)); x=list(range(len(S))); w=0.26
labs=['Ma et al. (odd filter, PS)','order-$r^\\star$ filter, PS','composed $(r^\\star,d)$']
for k,key in enumerate(('eb','es','ec')):
    ax.bar([i+(k-1)*w for i in x],[r[key] for r in S],w,color=C[k],edgecolor='black',linewidth=0.8,hatch=H[k],label=labs[k])
for i,r in enumerate(S):
    ax.text(i+w,r['ec']+7,'%.1f$\\times$'%(r['eb']/r['ec']),ha='center',va='bottom',fontsize=7.5,color=C[2])
ax.set_xticks(x); ax.set_xticklabels([f"{r['p']}\n$d$={r['d']}\n$h$={r['h']}" for r in S],fontsize=7.5); ax.set_xlabel('plaintext prime $p$',fontsize=9)
ax.set_ylabel('Digit-extraction time (s)'); ax.set_ylim(0,max(r['eb'] for r in S)*1.55)
ax.yaxis.set_minor_locator(AutoMinorLocator(2)); ax.legend(loc='upper left',ncol=2,fontsize=7.2,columnspacing=0.8,handlelength=1.4)
ax.text(0.01,1.02,'(a)',transform=ax.transAxes,fontsize=10,fontweight='bold')
fig.tight_layout(); fig.savefig(os.path.join(out,'fig6a_bars.pdf'))
fig,ax=plt.subplots(figsize=(4.3,2.45))
mk={7:('o','$p\\equiv7$ (mod 12), order six'),1:('s','$p\\equiv1$ (mod 12), order four'),5:('^','$p\\equiv5$ (mod 12), order four')}
for c,(m_,lab) in mk.items():
    D=[r for r in rows if r['cls']==c]
    if D:
        ax.plot([r['d'] for r in D],[r['eb']/r['ec'] for r in D],m_,ms=6.5,mfc=C[2],mec='black',mew=0.6,ls='none',label='composed, '+lab)
        ax.plot([r['d'] for r in D],[r['eb']/r['es'] for r in D],m_,ms=6.5,mfc='white',mec=C[1],mew=1.1,ls='none')
ax.plot([r['d'] for r in rows26],[r['eb']/r['ec'] for r in rows26],'D',ms=6,mfc='#2e8b57',mec='black',mew=0.6,ls='none',label='composed, $h=26$')
ax.plot([],[],'o',ms=6.5,mfc='white',mec=C[1],mew=1.1,ls='none',label='order-$r^\\star$ filter alone')
ax.axhline(1,color='black',lw=0.8,ls=':')
ax.set_xscale('log',base=2); ax.set_xticks([2,4,8,16]); ax.set_xticklabels(['2','4','8','16']); ax.minorticks_off()
ax.set_xlabel('Slot degree $d=\\mathrm{ord}_m(p)$'); ax.set_ylabel('Speedup over Ma et al.'); ax.set_ylim(0.8,7.6)
ax.legend(loc='upper left',ncol=2,fontsize=7.2,columnspacing=0.8,handlelength=1.2,handletextpad=0.4); ax.text(0.01,1.02,'(b)',transform=ax.transAxes,fontsize=10,fontweight='bold')
fig.tight_layout(); fig.savefig(os.path.join(out,'fig6b_speedup.pdf'))
# compact results table
L=[r"\begin{table}[t]\centering\caption{End-to-end thin bootstrapping on six representative rings (seconds, single-threaded; every run decryption-verified). ``lin.'' is the linear-transform time, identical across evaluators up to machine noise; ``cap.'' the capacity (bits) consumed by digit extraction; speedup is on digit extraction / on the total, relative to Ma et al.}\label{tab:results}\renewcommand{\arraystretch}{1.08}\setlength{\tabcolsep}{4pt}\footnotesize",
   r"\begin{tabular}{@{}llrrrrr@{}}\toprule",
   r"\textbf{Ring} & \textbf{Evaluator} & \textbf{lin.} & \textbf{Extract} & \textbf{Total} & \textbf{cap.} & \textbf{Speedup}\\\midrule"]
for r in S:
    tag=f"$p={r['p']}$, $m={r['m']}$\\\\ $d={r['d']}$, $h={r['h']}$, $r^\\star={r['rs']}$"
    L.append(r"\multirow{3}{*}{\shortstack[l]{"+tag+"}} & Ma et al.\\ (odd filter) & $%.0f$ & $%.1f$ & $%.1f$ & $%.0f$ & $1.00\\times$ / $1.00\\times$\\\\"%(r['lin'],r['eb'],r['tb'],r['capb']))
    L.append(r" & order-$%d$ filter, PS & & $%.1f$ & $%.1f$ & & $%.2f\times$ / --\\"%(r['rs'],r['es'],r['tb']-r['eb']+r['es'],r['eb']/r['es']))
    L.append(r" & \textbf{composed} $(%d,%d)$ & & \cellcolor{green!15}$\mathbf{%.1f}$ & \cellcolor{green!15}$\mathbf{%.1f}$ & $%.0f$ & \cellcolor{green!15}$\mathbf{%.2f\times}$ / $\mathbf{%.2f\times}$\\"%(r['rs'],r['d'],r['ec'],r['tc'],r['capc'],r['eb']/r['ec'],r['tb']/r['tc']))
    L.append(r"\midrule")
L[-1]=r"\bottomrule\end{tabular}\end{table}"
open(os.path.join(out,'tab_results_compact.tex'),'w').write("\n".join(L)+"\n")
# parameter table for the six rings
P=[r"\begin{table}[t]\centering\caption{Representative parameter sets ($h'=120$). $\lambda^\ast$ is the Lattice Estimator minimum over six attacks for the main and the encapsulated key at the chain \HElib{} built; $|A|$ is the integer representative of the order-$r^\star$ radix used by the pipeline.}\label{tab:params}\renewcommand{\arraystretch}{1.08}\setlength{\tabcolsep}{4pt}\footnotesize",
   r"\begin{tabular}{@{}rlrrrrrrrr@{}}\toprule",
   r"$p$ ($p\bmod12$) & $m=q_1\cdot q_2$ & $\varphi(m)$ & $d$ & slots & $h$ & $B$ & $r^\star$, $|A|$ & chain & $\lambda^\ast$\\\midrule"]
meta={}
for f in ('sets.tsv','sets128.tsv','cases.tsv'):
    for l in open(os.path.join(here,f)):
        if l.startswith('#'): continue
        c=l.rstrip('\n').split('\t'); meta[int(c[0])]=dict(q1=c[4],q2=c[5],aux4=c[9],aux6=c[10])
import csv
phim={}
for row in csv.DictReader(open(os.path.join(here,'results.csv'))):
    if row['phim']: phim[(int(row['idx']))]=row['phim']
for r in S:
    m=meta[r['idx']]; A=m['aux6'] if r['rs']==6 else m['aux4']
    P.append(f"${r['p']}$ ({r['cls']}) & ${m['q1']}\\cdot{m['q2']}$ & ${phim[r['idx']]}$ & ${r['d']}$ & ${r['ns']}$ & ${r['h']}$ & ${r['B']}$ & ${r['rs']}$, ${A}$ & ${r['chain']}$ & ${r['lam']:.1f}$\\\\")
P+=[r"\bottomrule\end{tabular}\end{table}"]
open(os.path.join(out,'tab_params_compact.tex'),'w').write("\n".join(P)+"\n")
print("ok", [ (r['p'],r['h']) for r in S])
