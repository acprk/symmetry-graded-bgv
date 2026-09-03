#!/usr/bin/env python3
"""Generate the census LaTeX table from CENSUS_p8191.txt + exact predictions."""
import subprocess, sys, os
CEN = sys.argv[1] if len(sys.argv) > 1 else "/tmp/CENSUS_p8191.txt"
HERE = os.path.dirname(os.path.abspath(__file__))
rows = []
for line in open(CEN):
    t = line.split()
    if len(t) == 7 and t[0].isdigit():
        rows.append(tuple(int(x) for x in t))          # r n' d scanned IRR NORM gcd

def pred(p, n, d):
    out = subprocess.run([sys.executable, os.path.join(HERE, "census_predict.py"),
                          str(p), str(n), str(d)], capture_output=True, text=True).stdout
    irr = norm = 0.0
    for ln in out.splitlines():
        if "P_irr" in ln:  irr  = float(ln.split("trials:")[1])
        if "P_norm" in ln: norm = float(ln.split("trials:")[1])
    return irr, norm

body = []
for (r, n, d, sc, irr, nrm, g) in sorted(rows, key=lambda x: (-x[0], x[2])):
    pi, pn = pred(8191, n, d)
    ratio = f"${nrm/pn:.2f}$" if pn > 0.05 else "---"
    obs_n = r"$\mathbf{0}$" if nrm == 0 else f"${nrm}$"
    obs_i = r"$\mathbf{0}$" if irr == 0 else f"${irr}$"
    body.append(f"${r}$ & ${n}$ & ${d}$ & ${sc}$ & {obs_i} & ${pi:.1f}$ & {obs_n} & ${pn:.1f}$ & {ratio} & ${g}$\\\\")

print(r"""\begin{table}[t]
\centering
\caption{Full census of the folded coset at $p=8191$ (a Mersenne prime, $m=45193$, hexagonal
support at $B=17$): \emph{every} $c\in\Fp^{\times}$ is enumerated and its member $Q+c\Gamma$
factored, so the observed columns are exact counts, not samples. Predictions are the exact
cycle-type probabilities for uniform monic polynomials of the same degree, scaled by the number of
members scanned. The last column is $\deg\gcd(Q,\Gamma)$, the fixed divisor of
\Cref{thm:obstruction}.}
\label{tab:census}
\small
\begin{tabular}{@{}rrrrrrrrrr@{}}
\toprule
& & & & \multicolumn{2}{c}{irreducible} & \multicolumn{2}{c}{norm form} & &\\
\cmidrule(lr){5-6}\cmidrule(lr){7-8}
$r$ & $n'$ & $d$ & scanned & obs.\ & pred.\ & obs.\ & pred.\ & obs./pred.\ & $\deg\gcd$\\
\midrule""")
print("\n".join(body))
print(r"""\bottomrule
\end{tabular}
\end{table}""")
