#!/usr/bin/env python3
"""Wire the composed (r,d) evaluator into the bootstrapping pipeline.

The order-four artifact already hooks extractDigits: with HELIB_AUX_ORDER4_EVAL it splits
the cleaner as P = c1*X + X^3*Q(X^4) and evaluates Q by Paterson-Stockmeyer. That is the
SCALAR axis alone. This patch adds a parallel branch, HELIB_COMPOSED_EVAL, evaluating the
same Q through the Galois norm map, so that both axes act inside the real pipeline.

The one thing that must be got right is Gamma. F = Q + c*Gamma computes the same function
as Q only if Gamma VANISHES ON THE FOLDED SUPPORT. The support is
    S = { hi*aux + lo : |hi|,|lo| <= B }        (compute_prime_aux_poly)
and the folded support is { x^4 : x in S }. Both B and aux are in scope where the cleaner
is built, so the plan is constructed there and consumed at evaluation time.

Gamma's degree above |folded support| is free, so we pad with points off the support until
d | deg F, which the orbit product requires.
"""
import re, sys

F = "/home/luck/xzy/0424project/github_order4_cleaner/src/HElib_auxradix_opt/src/extractDigits.cpp"
s = open(F).read()
if "HELIB_COMPOSED_EVAL" in s:
    print("already patched"); sys.exit(0)

# ---------------------------------------------------------------- includes
m = re.search(r"(#include [^\n]+\n)(?!#include)", s)
s = s.replace(m.group(1), m.group(1) + """#include <NTL/ZZ_pE.h>
#include <NTL/ZZ_pEX.h>
#include <NTL/ZZ_pXFactoring.h>
#include <NTL/ZZ_pEXFactoring.h>
#include <set>
""", 1)

# ---------------------------------------------------------------- plan + helpers
helper = r'''
// ==================== composed (r,d) evaluation ==============================
// Built once from (p, B, aux, d) where the cleaner is built, consumed at evaluation
// time. Q is pinned only as a FUNCTION on the folded support, so F = Q + c*Gamma agrees
// with it there for every c, provided Gamma vanishes on that support. Choosing c so that
// F is a norm from GR(p^e,d)[t] replaces the degree-(deg F) evaluation by a
// degree-(deg F / d) one plus an O(log d) Frobenius orbit.
struct ComposedPlan {
  bool built = false, ok = false;
  long d = 0, cmul = 1, nprime = 0, degC = 0, sgn = 1;
  std::vector<NTL::ZZX> ck;          // coefficients of C, already slot-encoded
};
static ComposedPlan g_composedPlan;
static long g_composedAutos = 0;

// N(x) = prod_{i<d} Frob^i(x), by binary doubling: O(log d) non-scalar multiplications.
static Ctxt composedOrbitProduct(const Ctxt& A0, long d) {
  if (d <= 1) return A0;
  long tb = 0; while ((1L << (tb + 1)) <= d) tb++;
  Ctxt B = A0; long cur = 1;
  for (long b = tb - 1; b >= 0; b--) {
    Ctxt t = B; t.frobeniusAutomorph(cur); g_composedAutos++;
    B.multiplyBy(t); B.reLinearize(); cur *= 2;
    if ((d >> b) & 1L) {
      Ctxt u = A0; u.frobeniusAutomorph(cur); g_composedAutos++;
      B.multiplyBy(u); B.reLinearize(); cur += 1;
    }
  }
  return B;
}

// Build the plan. `poly` is the cleaner P; the folded Q is P's k=3 mod 4 part.
static void buildComposedPlan(const NTL::ZZX& poly, long p, long B, long aux,
                              long d, const EncryptedArray& ea)
{
  ComposedPlan& P = g_composedPlan;
  if (P.built) return;
  P.built = true; P.d = d;
  if (d < 2) { std::cout << "HELIB_COMPOSED_EVAL: d=" << d
                         << ", Galois axis trivial; staying on P-S\n"; return; }
  NTL::ZZ_pPush push(NTL::conv<NTL::ZZ>(p));

  // folded support: { (hi*aux+lo)^4 mod p }
  std::set<long> fold;
  for (long hi = -B; hi <= B; hi++)
    for (long lo = -B; lo <= B; lo++) {
      long x = (((hi % p) * (aux % p) + lo) % p + p) % p;
      if (x == 0) continue;
      fold.insert(NTL::PowerMod(x, 4L, p));
    }
  long n = (long)fold.size();

  // Q from P: coefficient of X^{4j+3} becomes coefficient of Y^j
  NTL::ZZ_pX Qp;
  for (long i = 3; i <= NTL::deg(poly); i++)
    if ((i % 4) == 3 && !NTL::IsZero(NTL::coeff(poly, i)))
      NTL::SetCoeff(Qp, (i - 3) / 4, NTL::conv<NTL::ZZ_p>(NTL::coeff(poly, i)));

  // Gamma vanishes on the folded support; pad with points off it until d | deg Gamma
  long ntar = ((n + d - 1) / d) * d;
  if (ntar <= NTL::deg(Qp)) ntar += d;
  NTL::vec_ZZ_p roots; roots.SetLength(ntar);
  { long i = 0;
    for (long y : fold) roots[i++] = NTL::conv<NTL::ZZ_p>(y);
    long z = 0;
    while (i < ntar) { while (fold.count(z)) z++; roots[i++] = NTL::conv<NTL::ZZ_p>(z);
                       fold.insert(z); z++; } }
  NTL::ZZ_pX Gam; NTL::BuildFromRoots(Gam, roots);
  std::cout << "HELIB_COMPOSED_EVAL: d=" << d << " |folded support|=" << n
            << " degQ=" << NTL::deg(Qp) << " padded to n'=" << ntar << "\n";

  double t0 = GetTime();
  for (long c = 1; c < p; c++) {
    NTL::ZZ_pX Fc = Qp + NTL::conv<NTL::ZZ_p>(c) * Gam;
    if (NTL::deg(Fc) != ntar) continue;
    NTL::MakeMonic(Fc);
    if (!NTL::DetIrredTest(Fc)) continue;
    NTL::ZZ_pX Gslot; NTL::conv(Gslot, ea.getAlMod().getFactorsOverZZ()[0]);
    NTL::ZZ_pEPush push2(Gslot);
    NTL::ZZ_pEX Fe = NTL::conv<NTL::ZZ_pEX>(Fc);
    NTL::vec_pair_ZZ_pEX_long fac; NTL::CanZass(fac, Fe);
    if (fac.length() != d || NTL::deg(fac[0].a) != ntar / d) continue;
    NTL::ZZ_pEX C = fac[0].a;
    for (long i = 0; i <= NTL::deg(C); i++) {
      NTL::ZZX cz; NTL::conv(cz, NTL::rep(NTL::coeff(C, i)));
      std::vector<NTL::ZZX> sv(ea.size(), cz);
      NTL::ZZX enc; ea.encode(enc, sv); P.ck.push_back(enc);
    }
    P.ok = true; P.cmul = c; P.nprime = ntar; P.degC = ntar / d;
    P.sgn = (ntar % 2 == 0) ? 1 : -1;
    std::cout << "HELIB_COMPOSED_EVAL: norm form c=" << c << " degC=" << P.degC
              << " (search " << GetTime() - t0 << "s)\n";
    break;
  }
  if (!P.ok) std::cout << "HELIB_COMPOSED_EVAL: no norm form found; staying on P-S\n";
}
// =============================================================================
'''
anchor = "static bool envFlagEnabled(const char* name)"
assert anchor in s
s = s.replace(anchor, helper + "\n" + anchor, 1)

# ---------------------------------------------------------------- build the plan
old_build = """      extractPolys.SetLength(1);
      compute_prime_aux_poly(extractPolys[0], p, r, bnd, aux);"""
new_build = """      extractPolys.SetLength(1);
      compute_prime_aux_poly(extractPolys[0], p, r, bnd, aux);
      if (envFlagEnabled("HELIB_COMPOSED_EVAL"))
        buildComposedPlan(extractPolys[0], p, bnd, aux,
                          getContext().getOrdP(), getContext().getEA());"""
assert old_build in s
s = s.replace(old_build, new_build, 1)

# ---------------------------------------------------------------- the branch
old = """  Ctxt qEval(x.getPubKey(), x.getPtxtSpace());
  if (NTL::deg(q) >= 0) {
    const char* asymBsgsEnv = getenv("HELIB_ASYM_BSGS");"""
new = """  Ctxt qEval(x.getPubKey(), x.getPtxtSpace());

  // ---- composed branch: Q evaluated through the Galois norm map ------------
  if (NTL::deg(q) >= 0 && g_composedPlan.ok) {
    const ComposedPlan& P = g_composedPlan;
    Ctxt acc(x.getPubKey(), x.getPtxtSpace()); acc.clear();
    bool first = true;
    for (long i = (long)P.ck.size() - 1; i >= 0; i--) {   // Horner in x4
      if (!first) { acc.multiplyBy(x4); acc.reLinearize(); }
      Ctxt term(x.getPubKey(), x.getPtxtSpace());
      term.clear(); term.addConstant(P.ck[i]);
      acc += term; first = false;
    }
    Ctxt orb = composedOrbitProduct(acc, P.d);
    if (P.sgn < 0) orb.negate();
    orb.multByConstant(NTL::to_ZZ(P.cmul));
    orb.multiplyBy(x3); orb.reLinearize();
    if (!NTL::IsZero(linearCoeff)) {
      Ctxt linear = x; linear.multByConstant(linearCoeff); orb += linear;
    }
    ret = orb;
    static bool pr = false;
    if (!pr) { std::cout << "HELIB_COMPOSED_EVAL active: degC=" << P.degC
                         << " d=" << P.d << "\\n"; pr = true; }
    return true;
  }
  // -------------------------------------------------------------------------

  if (NTL::deg(q) >= 0) {
    const char* asymBsgsEnv = getenv("HELIB_ASYM_BSGS");"""
assert old in s
s = s.replace(old, new, 1)

open(F, "w").write(s)
print("patched", F, len(s), "bytes")
