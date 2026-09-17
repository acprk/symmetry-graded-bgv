#!/usr/bin/python3
"""Appendix D tables that are not produced by make_final.py: tab:offline, tab:sec_full, tab:passes.

Inputs : results.csv (written by collect.py), security/est_*.json, sets.tsv / sets128.tsv / cases.tsv.
Output : <outdir>/tab_offline.tex, tab_sec_full.tex, tab_passes.tex  (default outdir: ./final).

Row selection follows make_final.py: for a ring, the pass whose BASELINE linear-transform time is
smallest, and within it the composed arm with the smaller extraction time when both order four and
order six are available.  The offline columns (|A|, B, deg P_A, deg Q, n', deg C, c, search) are read
off that composed arm, since they describe the polynomial it actually evaluated.
"""
import csv, json, glob, os, sys

here = os.path.dirname(os.path.abspath(__file__))
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, 'final')
os.makedirs(out, exist_ok=True)

R = [r for r in csv.DictReader(open(os.path.join(here, 'results.csv'))) if r['valid'] == 'True']
S = {}
for f in glob.glob(os.path.join(here, 'security', 'est_*.json')):
    for row in json.load(open(f)):
        S[(row['p'], row['m'], row['h'])] = row
meta = {}
for f in ('sets.tsv', 'sets128.tsv', 'cases.tsv'):
    for l in open(os.path.join(here, f)):
        if l.startswith('#'):
            continue
        c = l.rstrip('\n').split('\t')
        meta[int(c[0])] = dict(p=int(c[1]), cls=int(c[2]), m=int(c[3]), q1=int(c[4]), q2=int(c[5]),
                               d=int(c[6]), ns=int(c[7]), req=int(c[8]))


def ring(i, h):
    """(baseline arm, scalar arm, composed arm, r*) for ring i at key weight h, or None."""
    rows = [r for r in R if int(r['idx']) == i and int(r['h']) == h]
    base = [r for r in rows if r['mode'] == 'BASELINE']
    if not base:
        return None
    ps = min(base, key=lambda r: float(r['lin']))['pas']
    A = {r['mode']: r for r in rows if r['pas'] == ps}
    if 'BASELINE' not in A:
        return None
    if meta[i]['cls'] == 7:
        sc, cp, rs = A.get('ORDER6'), A.get('ORDER6_COMPOSED'), 6
    else:
        c4, c6 = A.get('ORDER4_COMPOSED'), A.get('ORDER6_COMPOSED')
        cand = [x for x in (c4, c6) if x]
        cp = min(cand, key=lambda r: float(r['ext'])) if cand else None
        rs = 4 if cp is c4 else 6
        sc = A.get('ORDER4') if rs == 4 else A.get('ORDER6')
    if not (sc and cp):
        return None
    return A['BASELINE'], sc, cp, rs


HDR = (r"\begin{table}[t]\centering\caption{%s}\label{%s}\scriptsize\setlength{\tabcolsep}{%s}")


def offline():
    cap = (r"Offline data of \textsc{Select} and \Cref{alg:construction} per ring: the radix "
           r"representative $|A|$ used by the pipeline, the digit bound $B$, the degrees of $P_A$, "
           r"of the folded $Q$ and of the norm-form factor $C$, the accepted coset index $c$ and the "
           r"search time, the requested and built chain, and the capacity (bits) consumed by digit "
           r"extraction under the baseline and the composed evaluator.")
    L = [HDR % (cap, 'tab:offline', '2.5pt'),
         r"\resizebox{\linewidth}{!}{\begin{tabular}{@{}rrrrrrrrrrrrrr@{}}\toprule",
         r"$p$ & $m=q_1\cdot q_2$ & $h$ & $r^\star$ & $|A|$ & $B$ & $\deg P_A$ & $\deg Q$ & $n'$ & "
         r"$\deg C$ & $c$ & search (s) & chain req./built & capacity Ma / comp.\\\midrule"]
    for h, idxs in ((12, [i for i in sorted(meta) if i <= 28]),
                    (26, [i for i in sorted(meta) if i >= 29])):
        for i in idxs:
            got = ring(i, h)
            if not got:
                continue
            b, _, cp, rs = got
            m = meta[i]
            L.append(" & ".join([
                str(m['p']), "$%d\\cdot%d$" % (m['q1'], m['q2']), str(h), str(rs), cp['aux'],
                cp['B'], cp['degP'], cp['degQ'], cp['npad'], cp['degC'], cp['cnorm'],
                "%.1f" % float(cp['search']), "%d/%d" % (m['req'], int(b['bits'])),
                "%.0f / %.0f" % (float(b['capdrop']), float(cp['capdrop']))]) + r"\\")
    L += [r"\bottomrule\end{tabular}}\end{table}"]
    return "\n".join(L) + "\n"


def sec_full():
    cap = (r"Per-ring security of the main key ($h'=120$, modulus $Q$ = the chain \HElib{} built) and "
           r"of the encapsulated key (weight $h$, modulus $q_{\mathrm{boot}}$), in bits, for the six "
           r"attacks of the Lattice Estimator (uSVP, BDD, primal hybrid with and without Babai "
           r"rounding, dual, dual hybrid) at their optimised parameters; $\lambda^\ast$ is the minimum "
           r"of the two instances. All figures are at the built chain, not the requested one.")
    L = [HDR % (cap, 'tab:sec_full', '2.2pt'),
         r"\resizebox{\linewidth}{!}{\begin{tabular}{@{}rrrr|rrrrrrr|rrrrrrr|r@{}}\toprule",
         r" & & & & \multicolumn{7}{c|}{\textbf{main key} ($h'=120$)} & "
         r"\multicolumn{7}{c|}{\textbf{encapsulated key} (weight $h$)} & \\",
         r"$p$ & $m$ & $\varphi(m)$ & $h$ & $\log_2Q$ & uSVP & BDD & hyb & hyb-nb & dual & d-hyb & "
         r"$\log_2q_{\mathrm{boot}}$ & uSVP & BDD & hyb & hyb-nb & dual & d-hyb & $\lambda^\ast$\\\midrule"]
    keys = ['primal_usvp', 'primal_bdd', 'primal_hybrid', 'primal_hybrid_nb', 'dual', 'dual_hybrid']
    f1 = lambda v: "--" if v is None else "%.1f" % v
    for row in sorted(S.values(), key=lambda r: (r['h'], r['p'])):
        cells = [str(row['p']), str(row['m']), str(row['phim']), str(row['h']),
                 "%d" % int(row['log2Q'] + 0.5)]
        cells += [f1(row['main'].get(k)) for k in keys]
        cells += ["%.1f" % row['log2qboot']]
        cells += [f1(row['encap'].get(k)) for k in keys]
        cells += ["\\textbf{%.1f}" % row['lam_min']]
        L.append(" & ".join(cells) + r"\\")
    L += [r"\bottomrule\end{tabular}}\end{table}"]
    return "\n".join(L) + "\n"


def passes():
    cap = (r"Reproducibility: the four rings measured in two independent passes. ``lin.'' is the "
           r"linear-transform time, a load reference; ``norm.'' is $\mathrm{extract}/\mathrm{lin.}$.")
    L = [HDR % (cap, 'tab:passes', '3pt'),
         r"\begin{tabular}{@{}lr|rrr|rrr@{}}\toprule",
         r" & & \multicolumn{3}{c|}{pass 1} & \multicolumn{3}{c}{pass 2}\\ "
         r"$p$ & evaluator & lin. & extract & norm. & lin. & extract & norm.\\\midrule"]
    for i in sorted(meta):
        rows = [r for r in R if int(r['idx']) == i and int(r['h']) == 12]
        ps = sorted({r['pas'] for r in rows if r['mode'] == 'BASELINE'})
        if len(ps) < 2:
            continue
        six = meta[i]['cls'] == 7
        arms = [('Ma et al.', 'BASELINE'),
                ('order six' if six else 'order four', 'ORDER6' if six else 'ORDER4'),
                ('composed', 'ORDER6_COMPOSED' if six else 'ORDER4_COMPOSED')]
        for k, (lab, mode) in enumerate(arms):
            cells = [str(meta[i]['p']) if k == 0 else "", lab]
            for p_ in ps:
                r = next(x for x in rows if x['mode'] == mode and x['pas'] == p_)
                lin, ext = float(r['lin']), float(r['ext'])
                cells += ["%.1f" % lin, "%.1f" % ext, "%.2f" % (ext / lin)]
            L.append(" & ".join(cells) + r"\\")
    L += [r"\bottomrule\end{tabular}\end{table}"]
    return "\n".join(L) + "\n"


for name, text in (('tab_offline.tex', offline()), ('tab_sec_full.tex', sec_full()),
                   ('tab_passes.tex', passes())):
    open(os.path.join(out, name), 'w').write(text)
    print("wrote", os.path.join(out, name))
