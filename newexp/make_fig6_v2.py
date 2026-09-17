#!/usr/bin/env python3
"""Figure 7 (v2): (a) stacked bootstrapping-time bars, Ma et al. vs composed, on the nine paper sets;
(b) horizontal comparison with prior work at Ma et al.'s set V.  Output dir = argv[1] (default: final/)."""
import re,glob,os,sys,json
try:
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
except ImportError:
    raise SystemExit("matplotlib is required: pip install matplotlib (on this machine use /usr/bin/python3)")
from matplotlib.ticker import MultipleLocator
here=os.path.dirname(os.path.abspath(__file__)); out=sys.argv[1] if len(sys.argv)>1 else os.path.join(here,'final')
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8.5,'axes.linewidth':0.9,'xtick.direction':'out','ytick.direction':'out',
    'legend.frameon':True,'legend.framealpha':1,'legend.edgecolor':'black','legend.fontsize':7.5,'axes.labelsize':9.5})
# ---- parse logs (same rules as collect.py), keeping linear1/linear2 separately
blocks={}
for f in sorted(x for x in glob.glob(os.path.join(here,'logs','set*_pass*.log')) if 'before' not in x):
    for blk in re.split(r'(?=########## SET )',open(f,errors='replace').read())[1:]:
        h=re.match(r'########## SET (\d+) p=(\d+) m=(\d+) d=(\d+) :: (\w+) :: aux=(-?\d*) :: pass(\d+)(?: :: h=(\d+))?',blk)
        if not h: continue
        idx,p,m,d,mode,aux,ps,hw=h.groups(); hw=int(hw or 12)
        t=re.search(r'time for linear1 = ([\d.]+), linear2 = ([\d.]+), extract = ([\d.]+), total = ([\d.]+)',blk)
        ok='everything ok' in blk and re.search(r'exit=0',blk) and ('COMPOSED' not in mode or 'HELIB_COMPOSED_EVAL active' in blk)
        if t and ok: blocks[(int(idx),mode,int(ps),hw)]=tuple(map(float,t.groups()))
fr=json.load(open(os.path.join(here,'final','final_rows.json')))
sets=[('IV',8191,12),('V',65537,12),('80-A',19183,12),('80-B',2521,12),('80-C',13457,12),('80-D',3307,12),('128-A',8101,26),('128-B',14401,26),('128-C',2917,26)]
data=[]
for lab,p,h in sets:
    r=[x for x in fr['h12' if h==12 else 'h26'] if x['p']==p][0]
    base=blocks[(r['idx'],'BASELINE',r['pas'],h)]
    comp=blocks[(r['idx'],'ORDER%d_COMPOSED'%r['rs'],r['pas'],h)]
    assert abs(base[2]-r['eb'])<0.05 and abs(comp[2]-r['ec'])<0.05, (p,base,comp,r['eb'],r['ec'])
    data.append((lab,p,h,base,comp))
# ---- (a) stacked bars
C={'s2c':'#1f9bd7','c2s':'#f2a900','ext':'#d1461f','oth':'#b8b8b8'}
fig,ax=plt.subplots(figsize=(6.4,3.3)); w=0.36; gap=1.0
xs=[]
for i,(lab,p,h,base,comp) in enumerate(data):
    for k,(t,off) in enumerate(((base,-w/2-0.02),(comp,w/2+0.02))):
        x=i*gap+off; xs.append(x)
        l1,l2,ex,tot=t; oth=max(tot-l1-l2-ex,0)
        ax.bar(x,l1,w,color=C['s2c'],edgecolor='black',linewidth=0.5)
        ax.bar(x,l2,w,bottom=l1,color=C['c2s'],edgecolor='black',linewidth=0.5)
        ax.bar(x,ex,w,bottom=l1+l2,color=C['ext'],edgecolor='black',linewidth=0.5,alpha=1 if k else 0.55,hatch='' if k else '///')
        ax.bar(x,oth,w,bottom=l1+l2+ex,color=C['oth'],edgecolor='black',linewidth=0.5)
        ax.text(x,l1+l2+ex/2,'%.0f'%ex,ha='center',va='center',fontsize=6.2,color='white' if k else 'black')
        ax.text(x,tot+4,'%.0fs'%tot,ha='center',va='bottom',fontsize=6.3)
    ax.text(i*gap,max(base[3],comp[3])+34,'%.2f$\\times$'%(base[3]/comp[3]),ha='center',va='bottom',fontsize=7,color='#1a5f8c',fontweight='bold')
ax.set_xticks([i*gap for i in range(len(data))]); ax.set_xticklabels(['%s\n$p$=%d'%(lab,p) for lab,p,h,_,_ in data],fontsize=7.2)
ax.set_ylabel('Bootstrapping time (s)'); ax.set_ylim(0,max(b[3] for _,_,_,b,_ in data)*1.28); ax.yaxis.set_minor_locator(MultipleLocator(50))
ax.grid(axis='y',ls=':',lw=0.5,color='#999'); ax.set_axisbelow(True)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(fc=C['s2c'],ec='black',lw=0.5,label='SlotToCoeff'),Patch(fc=C['c2s'],ec='black',lw=0.5,label='CoeffToSlot'),
    Patch(fc=C['ext'],ec='black',lw=0.5,alpha=0.55,hatch='///',label='Extract (Ma et al.)'),Patch(fc=C['ext'],ec='black',lw=0.5,label='Extract (composed, ours)'),
    Patch(fc=C['oth'],ec='black',lw=0.5,label='Other')],loc='upper left',ncol=3,columnspacing=1.0,handlelength=1.3)
ax.text(0.99,0.97,'left bar: Ma et al.   right bar: this work',transform=ax.transAxes,ha='right',va='top',fontsize=7,color='#444')
fig.tight_layout(); fig.savefig(os.path.join(out,'fig6a_stacked.pdf')); plt.close(fig)
# ---- (b) prior work at set V: one boxed panel, method names inside the bars
rows=[('Native HElib [HS21]',43200,'>43200s',True,'prior'),('Geelen et al. [GIKV23]',550,'~550s',False,'prior'),
      ('Zhao et al. [ZLW26], thick',599,'599s',False,'prior'),('Ma et al. [MHWW24]',217.6,'217.6s, 1.00x',False,'prior'),
      ('Order-4 [XW26]',152.0,'152.0s, 1.43x',False,'ours1'),('Composed [ours]',103.1,'103.1s, 2.11x',False,'ours2')]
col={'prior':'#9e9e9e','ours1':'#1f9bd7','ours2':'#1a5f8c'}; L=10
fig,ax=plt.subplots(figsize=(5.0,3.0)); y=list(range(len(rows)))[::-1]
for yi,(lab,v,txt,brk,kind) in zip(y,rows):
    ax.barh(yi,v-L,0.64,left=L,color=col[kind],edgecolor='black',linewidth=0.5)
    ax.text(L*1.12,yi,lab,va='center',ha='left',fontsize=7.2,color='white' if kind!='prior' else 'black')
    ax.text(v*1.08,yi,txt,va='center',ha='left',fontsize=7.2)
    if brk:
        ax.plot([9000,12000],[yi-0.36,yi+0.36],color='white',lw=4,zorder=3); ax.plot([8700,11600],[yi-0.36,yi+0.36],color='black',lw=1,zorder=4); ax.plot([9300,12400],[yi-0.36,yi+0.36],color='black',lw=1,zorder=4)
ax.set_yticks([]); ax.set_ylim(-0.7,len(rows)-0.3)
ax.set_xscale('log'); ax.set_xlim(L,300000); ax.set_xticks([10,100,1000,10000,100000]); ax.set_xticklabels(['10','100','1k','10k','100k'])
ax.set_xticks([20,50,200,500,2000,5000,20000,50000],minor=True); ax.tick_params(which='minor',length=2)
ax.set_xlabel('Total bootstrapping time at set V ($p=65537$, $m=50731$), seconds')
ax.grid(axis='x',which='major',ls=':',lw=0.5,color='#999'); ax.set_axisbelow(True)
ax.legend(handles=[Patch(fc=col['prior'],ec='black',lw=0.5,label='Prior work'),Patch(fc=col['ours2'],ec='black',lw=0.5,label='This work')],loc='lower right',ncol=1,fontsize=7.5)
fig.tight_layout(); fig.savefig(os.path.join(out,'fig6b_prior.pdf')); plt.close(fig)
print('ok',[(d[0],d[1],round(d[3][3]/d[4][3],2)) for d in data])
