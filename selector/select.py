#!/usr/bin/env python3
"""select.py -- the closed-form (r,d) selector of the paper, Procedure SELECT.

Given a plaintext prime p, a cyclotomic index m, and a digit bound B, this script
searches for the cost-optimal symmetry-graded evaluator (r*, d) WITHOUT running any
homomorphic encryption: it is pure arithmetic over Z, runs in milliseconds, and needs
only `sympy`. It is meant to be run BEFORE any ciphertext experiment, to decide which
configuration to build and measure -- exactly the workflow the paper's Section 7
("What the selector predicts") documents.

Nothing here is hard-coded to r in {4,6}. The search ranges over EVERY divisor r of
p-1 up to --rmax, and for each candidate radix A of that order it:
  1. builds the digit region T (box / hexagon / Euclidean ball) at radius B;
  2. encodes T under x -> eta*A + lambda and requires the encoding to be injective
     (Definition: B-injectivity);
  3. walks the FULL <A>-orbit of every point of T and checks that the covariant
     low-digit propagation P(A w) = A^{-1}(P(w) - w) is single-valued along the whole
     orbit, not just one step (a one-step check is vacuous for large r and would
     wrongly accept orders that do not actually close on T);
  4. from the surviving candidates, computes the effective order
         rho(A) = r * |T| / |Omega_A|,   Omega_A = orbit closure of T under x -> Ax,
     which is what the evaluator actually spends (rho = r iff T is already A-stable;
     otherwise the orbit closure inflates the region and eats part of the sparsity);
  5. combines the scalar saving with the Galois slot degree d = ord_m(p) via the
     graded cost function cost(D; rho, d) of Definition 8 in the paper, and returns
     the (r, d) pair of minimal cost.

Two structural facts fall out of the search rather than being assumed by it: the
feasible radices are exactly the ones whose companion matrix has finite order in
GL_2(Z) (the crystallographic restriction, order in {1,2,3,4,6}, which is where the
"p mod 12" rule of Corollary 6 comes from), and the effective order rho is capped by
the SHAPE of the region T, not by r alone (order 4 attains rho=4 on a box; order 6
attains rho=6 on a hexagon and only rho=4 on the orbit closure of a box).

Usage
-----
    python3 select.py --p 65537 --m 50731 --B 17
    python3 select.py --p 8191  --m 65536 --B 17 --support hex --json
    python3 select.py --self-test        # replays every row of Tables 6 and 12

Output
------
Human-readable report by default; pass --json for a machine-readable dict suitable
for feeding into the experiment-launcher scripts in ../experiments/.
"""
import argparse
import json
import math
import sys

from sympy import factorint, isprime, n_order

CRYSTALLOGRAPHIC_ORDERS = (1, 2, 3, 4, 6)   # phi(r) <= 2; the only orders a rank-2
                                             # scalar rotation can realise (Thm 4).


# --------------------------------------------------------------------------------
# digit regions
# --------------------------------------------------------------------------------
def region(shape, B):
    """The digit-extraction input region T, as a list of (eta, lambda) pairs."""
    if shape == "box":     # independent coordinate bounds -- Ma et al. EUROCRYPT'24
        return [(e, l) for e in range(-B, B + 1) for l in range(-B, B + 1)]
    if shape == "hex":     # Eisenstein-symmetric region -- this work's order-6 filter
        return [(e, l) for e in range(-B, B + 1) for l in range(-B, B + 1)
                if abs(e + l) <= B]
    if shape == "ball":    # Euclidean (canonical-norm) region
        return [(e, l) for e in range(-B, B + 1) for l in range(-B, B + 1)
                if e * e + l * l <= B * B]
    raise ValueError(f"unknown support shape {shape!r}")


def divisors(n):
    d = [1]
    for q, e in factorint(n).items():
        d = [x * q ** i for x in d for i in range(e + 1)]
    return sorted(d)


def primitive_root(p):
    fac = list(factorint(p - 1))
    for g in range(2, p):
        if all(pow(g, (p - 1) // q, p) != 1 for q in fac):
            return g
    raise RuntimeError(f"no primitive root found mod {p}")


def elements_of_order(r, p, g, cap):
    """Up to `cap` distinct elements of exact multiplicative order r mod p."""
    base = pow(g, (p - 1) // r, p)
    out = []
    for j in range(1, max(r, 2)):
        if math.gcd(j, r) == 1:
            out.append(pow(base, j, p))
            if len(out) >= cap:
                break
    return out or [base]


def companion(A, p, lim=6):
    """If A^2 = u*A + v (mod p) for small |u|,|v| <= lim, return (u,v); else None.

    A finite-order companion matrix [[0,-v],[1,u]] has det = -v and trace = u; the
    crystallographic restriction (Thm 4) forces v = +-1 and |u| <= 2 for A to be a
    genuine rank-2 rotation, i.e. its characteristic polynomial cyclotomic.
    """
    A2 = A * A % p
    for u in range(-lim, lim + 1):
        v = (A2 - u * A) % p
        vc = v - p if v > p // 2 else v
        if abs(vc) <= lim:
            return u, vc
    return None


# --------------------------------------------------------------------------------
# the scalar axis: search for every admissible radix, scored by effective order
# --------------------------------------------------------------------------------
def scalar_candidates(p, B, shape, rmax, cap_per_order):
    T_pairs = region(shape, B)
    g = primitive_root(p)
    out = []

    # r = 2 (the odd/bounded-support filter of Ma et al.) is a special case: its
    # symmetry is negation x -> -x, which is automatic on ANY B-injective, origin-
    # symmetric region T = -T -- it is not "an order-2 element used as the encoding
    # radix" (that would be A = -1 itself, an entirely different and useless
    # degenerate encoding). Correspondingly Proposition 9 states r=2 is available for
    # EVERY odd p, independent of p mod 12. We therefore test it once, using the
    # smallest B-injective radix available (any works, by Lemma "Injectivity
    # criterion"; we reuse the largest-order candidate's radix if one exists, else
    # search directly), rather than via elements_of_order(2, ...).
    if 2 <= rmax:
        A2 = None
        for cand_r in sorted(divisors(p - 1), reverse=True):
            if cand_r < 3:
                continue
            for A in elements_of_order(cand_r, p, g, 1):
                low = {}
                ok = True
                for e, l in T_pairs:
                    x = (e * A + l) % p
                    if x in low and low[x] != l % p:
                        ok = False
                        break
                    low[x] = l % p
                if ok:
                    A2 = A
                    break
            if A2 is not None:
                break
        if A2 is None:
            # fall back to a direct search over small radices for the degenerate
            # all-orders-collide case (only ever happens at pathologically large B)
            for A in range(2, p):
                low, ok = {}, True
                for e, l in T_pairs:
                    x = (e * A + l) % p
                    if x in low and low[x] != l % p:
                        ok = False
                        break
                    low[x] = l % p
                if ok:
                    A2 = A
                    break
        if A2 is not None:
            low = {(e * A2 + l) % p: l % p for e, l in T_pairs}
            T = set(low)
            neg_ok = all(((-x) % p in low) and low[(-x) % p] == (-low[x]) % p for x in low)
            if neg_ok:
                out.append(dict(r=2, A=A2, nT=len(T), nS=len(T), inflation=1.0,
                                 rho=2.0, companion=(0, 1)))

    for r in divisors(p - 1):
        if r < 2 or r > rmax:
            continue
        for A in elements_of_order(r, p, g, cap_per_order):
            low, injective = {}, True
            for e, l in T_pairs:
                x = (e * A + l) % p
                if x in low and low[x] != l % p:
                    injective = False
                    break
                low[x] = l % p
            if not injective:
                continue
            T = set(low)
            Ainv = pow(A, p - 2, p)
            # Full-orbit consistency: propagate the covariant low-digit relation
            # P(Aw) = A^{-1}(P(w) - w) around the ENTIRE <A>-orbit of every point of
            # T, not just one step. A one-step check is vacuous for large r (a
            # generic orbit almost never returns to T after a single multiplication)
            # and would falsely accept orders that do not actually close on T.
            S, seen, consistent = set(), set(), True
            for w0 in T:
                if w0 in seen:
                    continue
                w, val = w0, low[w0]
                for _ in range(r):
                    seen.add(w)
                    S.add(w)
                    if w in T and low[w] != val:
                        consistent = False
                        break
                    val = Ainv * (val - w) % p
                    w = w * A % p
                if not consistent:
                    break
            if not consistent:
                continue
            rho = r * len(T) / len(S)
            out.append(dict(r=r, A=A, nT=len(T), nS=len(S),
                             inflation=len(S) / len(T), rho=rho,
                             companion=companion(A, p)))
    out.sort(key=lambda z: -z["rho"])
    return out


# --------------------------------------------------------------------------------
# the joint (r,d) graded cost -- Definition 8 of the paper
# --------------------------------------------------------------------------------
def cost_rd(D, rho, d, nu=0.0):
    """Non-scalar multiplications of the (rho,d)-graded evaluator, cost(D; rho, d).

    nu is the bounded additive base-two alignment penalty (Prop. 12): the norm-map
    doubling schedule emits power-of-two auxiliary monomials for free, so folding by
    an r that is not itself a power of two costs at most O(1) extra products. It is
    never a feasibility condition, only a constant added to an otherwise dominant
    sqrt(1/r) saving.
    """
    if d >= 2 and D / rho <= d:
        return math.log2(d) + nu
    if d >= 2:
        return 2 * math.sqrt(D / (rho * d)) + math.log2(max(D / rho, 2)) + nu
    return 2 * math.sqrt(D / rho) + nu


def select(p, m, B, shape="box", rmax=4096, cap_per_order=4, use_galois=True):
    """Procedure SELECT(p, m, B, shape) of the paper. Returns a result dict."""
    assert isprime(p), f"p={p} is not prime"
    d = n_order(p, m) if (m and m % p) else 1
    cands = scalar_candidates(p, B, shape, rmax, cap_per_order)
    generic_T = len(region(shape, B))
    D = generic_T - 1
    rows = []
    for c in cands:
        nu = 0.0 if (c["r"] & (c["r"] - 1)) == 0 else 1.0    # r a power of two -> free
        eff_d = d if use_galois else 1
        rows.append(dict(c, d=eff_d, cost=cost_rd(D, c["rho"], eff_d, nu)))
    baseline = cost_rd(D, 1.0, 1)
    rows.sort(key=lambda z: z["cost"])
    best = rows[0] if rows else dict(r=1, A=None, rho=1.0, d=1,
                                      cost=baseline, companion=None)
    return dict(p=p, m=m, B=B, shape=shape, d=d, D=D, nT=generic_T,
                baseline=baseline, rows=rows,
                r_star=best["r"], rho_star=best["rho"],
                A_star=best["A"], cost_star=best["cost"],
                speedup=baseline / best["cost"])


def report(res, top=8):
    print(f"p = {res['p']}   m = {res['m']}   d = ord_m(p) = {res['d']}   "
          f"B = {res['B']}   support = {res['shape']}   |T| = {res['nT']}")
    print(f"generic Paterson-Stockmeyer baseline: 2*sqrt(D) = {res['baseline']:.1f} mults")
    if not res["rows"]:
        print("  no admissible scalar filter beyond generic: r* = 1")
        return
    print(f"  {'r':>5} {'A':>8} {'|S|':>7} {'infl':>6} {'rho':>6} "
          f"{'cost(r,d)':>10} {'speedup':>8}  companion A^2=uA+v")
    print("  " + "-" * 76)
    for z in res["rows"][:top]:
        c = z["companion"]
        cs = f"u={c[0]:>2}, v={c[1]:>2}" if c else "no small (u,v)"
        print(f"  {z['r']:>5} {z['A']:>8} {z['nS']:>7} {z['inflation']:>6.2f} "
              f"{z['rho']:>6.2f} {z['cost']:>10.1f} "
              f"{res['baseline']/z['cost']:>7.2f}x  {cs}")
    print(f"  => r* = {res['r_star']}  (A = {res['A_star']}, "
          f"effective order rho = {res['rho_star']:.2f}), d = {res['d']}, "
          f"predicted cost = {res['cost_star']:.1f}")


# --------------------------------------------------------------------------------
# self-test: replay Table "plan" and Table "select" of the paper exactly
# --------------------------------------------------------------------------------
SELF_TEST_CASES = [
    # (p,        m,      B,  shape, expected_r, expected_cost)
    (65537,  65536, 17, "box", 4, 35.0),   # Table 6, row 65537/2^16 (Ma et al.'s own set)
    (131071, 65536, 17, "hex", 6, 25.8),   # Table 6, row 131071/2^16
    (8191,   65536, 17, "hex", 6, 17.0),   # Table 6, row 8191/2^16 (Mersenne)
    (4003,  209833, 17, "hex", 6, 18.4),   # Table 12, row 4003
    (65537,  50731, 17, "box", 4, 16.5),   # Table 12, row 65537/50731 (Case V)
    (65521,  72507, 17, "box", 4, 28.5),   # Table 12, row 65521
    (2521,   18915, 17, "box", 4, 33.0),   # Table 12, row 2521, box
    (2521,   18915, 17, "hex", 6, 25.8),   # Table 12, row 2521, hexagon
    (100019,     0, 17, "box", 2, 49.5),   # p = 11 (mod 12): only r=2 is ever available
    (100019,     0, 17, "hex", 2, 42.8),   # (Corollary 6); regression test for the r=2
                                            # special case (negation, not an order-2 radix).
]


def self_test():
    ok = True
    print(f"{'p':>8} {'m':>8} {'shape':>5}  r*(exp/got)  cost(exp/got)   verdict")
    for p, m, B, shape, exp_r, exp_cost in SELF_TEST_CASES:
        res = select(p, m, B, shape)
        got_r, got_cost = res["r_star"], res["cost_star"]
        pass_ = (got_r == exp_r) and (abs(got_cost - exp_cost) < 0.05)
        ok &= pass_
        verdict = "OK" if pass_ else "MISMATCH"
        print(f"{p:>8} {m:>8} {shape:>5}  {exp_r:>3} / {got_r:<3}     "
              f"{exp_cost:>5.1f} / {got_cost:<5.1f}      {verdict}")
    print()
    print("ALL PASS" if ok else "SOME MISMATCHES -- do not trust downstream tables")
    return 0 if ok else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--p", type=int, help="plaintext prime")
    ap.add_argument("--m", type=int, default=0, help="cyclotomic index (0 = scalar axis only)")
    ap.add_argument("--B", type=int, default=17, help="digit bound (support radius)")
    ap.add_argument("--support", default="box", choices=["box", "hex", "ball"])
    ap.add_argument("--rmax", type=int, default=4096)
    ap.add_argument("--no-galois", action="store_true", help="score the scalar axis alone")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--self-test", action="store_true",
                     help="replay Tables 6 and 12 of the paper and check exact agreement")
    a = ap.parse_args()

    if a.self_test:
        sys.exit(self_test())

    if a.p is None:
        ap.error("--p is required unless --self-test is given")
    res = select(a.p, a.m, a.B, a.support, a.rmax, use_galois=not a.no_galois)
    if a.json:
        out = {k: v for k, v in res.items() if k != "rows"}
        out["rows"] = [{kk: vv for kk, vv in row.items()} for row in res["rows"]]
        print(json.dumps(out, indent=2))
    else:
        report(res)
