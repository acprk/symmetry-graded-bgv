#!/usr/bin/env python3
"""Exact predicted counts for the census table.

For monic degree-n polynomials over F_p:
  P_irr  = N(p,n)/p^n                            (irreducible)
  P_norm = [x^n] prod_{d | m} (1+x^m)^{N(p,m)} / p^n   over m multiples of d
           (squarefree AND every irreducible-factor degree divisible by d)
Exact big-integer computation; census scans p-1 values of c, so predicted count =
(p-1) * P. Usage: census_predict.py p n d
"""
import sys
from sympy import mobius, divisors

def N(p, m):          # number of monic irreducibles of degree m over F_p
    return int(sum(int(mobius(k)) * p ** (m // k) for k in divisors(m)) // m)

def predict(p, n, d):
    # coefficient DP for prod over m = d, 2d, ... <= n of (1+x^m)^{N_m}, truncated at n
    coeff = [0] * (n + 1); coeff[0] = 1
    m = d
    while m <= n:
        Nm = N(p, m)
        # multiply by (1+x^m)^{Nm} truncated: binomials C(Nm, j)
        new = coeff[:]
        j, binom = 1, Nm
        while j * m <= n:
            for t in range(n - j * m, -1, -1):
                if coeff[t]:
                    new[t + j * m] += coeff[t] * binom
            binom = binom * (Nm - j) // (j + 1)
            j += 1
        coeff = new
        m += d
    import math
    logden = n * math.log(p)
    p_norm = math.exp(math.log(coeff[n]) - logden) if coeff[n] else 0.0
    p_irr = math.exp(math.log(N(p, n)) - logden)
    return p_irr, p_norm

if __name__ == "__main__":
    p, n, d = map(int, sys.argv[1:4])
    pi, pn = predict(p, n, d)
    print(f"p={p} n={n} d={d}")
    print(f"  P_irr  = {pi:.6g}   expected over p-1 trials: {(p-1)*pi:.2f}")
    print(f"  P_norm = {pn:.6g}   expected over p-1 trials: {(p-1)*pn:.2f}")
