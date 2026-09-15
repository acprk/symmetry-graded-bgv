#!/usr/bin/python3
"""Two side-by-side figures from results.csv (h=12 tier, pass 1 unless pass 2 exists):
 (a) digit-extraction time per ring, four evaluators, rings ordered by slot degree d;
 (b) measured speedup over the baseline vs d: scalar-only (flat) and composed (grows with d), with the cost-model curve."""
import csv,os,math,sys
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
here=os.path.dirname(os.path.abspath(__file__)); out=sys.argv[1] if len(sys.argv)>1 else here
R=[r for r in csv.DictReader(open(os.path.join(here,'results.csv'))) if r['valid']=='True' and r['h']=='12']
def pick(idx,mode):
    c=[r for r in R if int(r['idx'])==idx and r['mode']==mode]
    return float(sorted(c,key=lambda r:int(r['pas']))[0]['ext']) if c else None
sets=sorted({int(r['idx']) for r in R})
info={int(r['idx']):(int(r['p']),int(r['d']),int(r['p'])%12) for r in R}
data=[]
for i in sets:
    p,d,c=info[i]; base=pick(i,'BASELINE'); 
    if not base: continue
    scal=pick(i,'ORDER6') if c==7 else (pick(i,'ORDER4') or pick(i,'ORDER6'))
    comp=pick(i,'ORDER6_COMPOSED') if c==7 else (pick(i,'ORDER4_COMPOSED') or pick(i,'ORDER6_COMPOSED'))
    zhao=pick(i,'NORMONLY')
    if scal and comp: data.append(dict(idx=i,p=p,d=d,cls=c,base=base,scal=scal,comp=comp,zhao=zhao))
data.sort(key=lambda x:(x['d'],x['p']))
plt.rcParams.update({'font.size':8,'axes.labelsize':8,'legend.fontsize':7,'xtick.labelsize':7,'ytick.labelsize':7})
# (a)
fig,ax=plt.subplots(figsize=(3.3,2.55)); x=range(len(data)); w=0.2
ax.bar([i-1.5*w for i in x],[e['base'] for e in data],w,label='Ma et al. (r=2, PS)',color='#9e9e9e')
ax.bar([i-0.5*w for i in x],[e['zhao'] or 0 for e in data],w,label='norm map on $P_A$ (r=1)',color='#c8a2c8')
ax.bar([i+0.5*w for i in x],[e['scal'] or 0 for e in data],w,label='order-$r^\\star$ filter, PS',color='#5b9bd5')
ax.bar([i+1.5*w for i in x],[e['comp'] or 0 for e in data],w,label='composed $(r^\\star,d)$',color='#c0392b')
ax.set_xticks(list(x)); ax.set_xticklabels([f"{e['p']}\n$d$={e['d']}" for e in data],rotation=90)
ax.set_ylabel('digit extraction (s)'); ax.legend(frameon=False,loc='upper center',ncol=2,bbox_to_anchor=(0.5,1.28)); ax.set_ylim(0,max(e['base'] for e in data)*1.08)
fig.tight_layout(); fig.savefig(os.path.join(out,'fig_extract_time.pdf'))
# (b)
fig,ax=plt.subplots(figsize=(3.3,2.55))
mk={7:'o',1:'s',5:'^'}; lab={7:'$p\\equiv7$ (order six)',1:'$p\\equiv1$ (order four)',5:'$p\\equiv5$ (order four)'}
for c in (7,1,5):
    D=[e for e in data if e['cls']==c]
    if not D: continue
    ax.scatter([e['d'] for e in D],[e['base']/e['comp'] for e in D],marker=mk[c],s=22,color='#c0392b',label='composed, '+lab[c])
    ax.scatter([e['d'] for e in D],[e['base']/e['scal'] for e in D],marker=mk[c],s=22,facecolors='none',edgecolors='#5b9bd5')
    Z=[e for e in D if e['zhao']]
    if Z: ax.scatter([e['d'] for e in Z],[e['base']/e['zhao'] for e in Z],marker=mk[c],s=22,facecolors='none',edgecolors='#8e44ad')
ax.scatter([],[],marker='o',facecolors='none',edgecolors='#5b9bd5',label='scalar axis only ($r^\\star$, PS)')
ax.scatter([],[],marker='o',facecolors='none',edgecolors='#8e44ad',label='Galois axis only (norm map on $P_A$)')
ax.axhline(1,color='k',lw=0.5,ls=':')
ax.set_xlabel('slot degree $d=\\mathrm{ord}_m(p)$'); ax.set_ylabel('speedup over Ma et al.'); ax.set_xscale('log',base=2)
ax.set_xticks([2,4,8,16]); ax.set_xticklabels(['2','4','8','16']); ax.legend(frameon=False,loc='upper left')
fig.tight_layout(); fig.savefig(os.path.join(out,'fig_speedup_vs_d.pdf'))
print("figures written to",out); [print(e) for e in data]
