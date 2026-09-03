#!/usr/bin/env python3
"""Extend the recryption pipeline from order-four-only to a general order-r filter,
so that the order-six (Eisenstein) construction runs end to end at p = 7 mod 12.

Four changes:
  1. compute_prime_aux_poly_order6 -- builds the bounded-support interpolant on the
     ORBIT CLOSURE of the coordinate box under M:(h,l)->(h+l,-h). The closure costs a
     factor 3/2 in support size and buys the order-six monomial pattern {1} u {k=5 mod 6}
     on a box-shaped input region (no hexagonal noise model needed).
  2. splitOrderFourCleaner -> splitFilterCleaner, parameterised by the filter order.
  3. polyEvalOrderFourCleaner -> powers x^2..x^{r-1}, x^r instead of hardcoded x^2,x^3,x^4.
  4. buildComposedPlan -> folds by X^r using the folded support recorded at build time.
"""
F = "/home/luck/xzy/0424project/github_order4_cleaner/src/HElib_auxradix_opt/src/extractDigits.cpp"
s = open(F).read()
if "compute_prime_aux_poly_order6" in s:
    print("already patched"); raise SystemExit

# ---------------------------------------------------------------- 1. builder
anchor = "\n// ==================== composed (r,d) evaluation =============================="
assert anchor in s
builder = r'''
// ---- order-r filter state, set when the extraction polynomial is built ----------
static long g_filterOrder = 4;          // 4 (Gaussian) or 6 (Eisenstein)
static long g_filterRadix = 0;          // the radix actually used
static std::set<long> g_foldSupport;    // { x^ord : x in support }, recorded at build time

// Order-six (Eisenstein) bounded-support polynomial. The order-six rotation
// (h,l) -> (h+l,-h) does not preserve the coordinate box, so we interpolate on the
// ORBIT CLOSURE of the box, which is stable by construction and costs exactly the 3/2
// inflation of the box-closure lemma. The low-digit map extends to the closure as the
// same "return l" function, which is precisely its covariant extension, so the
// interpolant satisfies P(AX) = A^{-1}(P(X) - X) and carries the monomial pattern
// {1} u {k = 5 mod 6}. Returns the radix used, or 0 if no usable one exists.
long compute_prime_aux_poly_order6(NTL::ZZX& poly, long p, long r, long B)
{
  if (p % 3 != 1) return 0;                       // no primitive 6th root of unity
  NTL::ZZ p_ZZ(p);
  NTL::ZZ_pPush push(p_ZZ);

  // primitive cube root of unity w; then A = -w satisfies A^2 - A + 1 = 0
  std::vector<long> cands;
  for (long z = 2; z < p && (long)cands.size() < 2; z++) {
    long w = NTL::PowerMod(z % p, (p - 1) / 3, p);
    if (w == 1) continue;
    long A = (p - w) % p;
    if (((NTL::MulMod(A, A, p) - A) % p + 1) % p != 0) continue;
    if (std::find(cands.begin(), cands.end(), A) == cands.end()) cands.push_back(A);
  }
  if (cands.empty()) return 0;

  for (long A6 : cands) {
    // orbit closure of the box under M
    std::set<std::pair<long, long> > reg;
    for (long h = -B; h <= B; h++)
      for (long l = -B; l <= B; l++) reg.insert(std::make_pair(h, l));
    for (int it = 0; it < 6; it++) {
      std::set<std::pair<long, long> > add;
      for (std::set<std::pair<long, long> >::iterator i = reg.begin(); i != reg.end(); ++i)
        add.insert(std::make_pair(i->first + i->second, -i->first));
      reg.insert(add.begin(), add.end());
    }
    bool stable = true;
    for (std::set<std::pair<long, long> >::iterator i = reg.begin(); i != reg.end(); ++i)
      if (!reg.count(std::make_pair(i->first + i->second, -i->first))) { stable = false; break; }
    if (!stable) continue;

    // encode and check injectivity on the closure
    std::map<long, long> lamOf;
    bool inj = true;
    for (std::set<std::pair<long, long> >::iterator i = reg.begin(); i != reg.end(); ++i) {
      long x = ((((i->first % p) * (A6 % p)) % p + i->second) % p + p) % p;
      long lv = ((i->second % p) + p) % p;
      std::map<long, long>::iterator it = lamOf.find(x);
      if (it != lamOf.end() && it->second != lv) { inj = false; break; }
      lamOf[x] = lv;
    }
    if (!inj || lamOf.size() != reg.size()) continue;

    // interpolate over F_p, then Hensel-lift to Z_{p^r} exactly as the order-four builder
    NTL::vec_ZZ inputs, outputs;
    for (std::map<long, long>::iterator it = lamOf.begin(); it != lamOf.end(); ++it) {
      inputs.append(NTL::ZZ(it->first));
      long lv = it->second; if (lv > p / 2) lv -= p;      // balanced low digit
      outputs.append(NTL::ZZ(lv));
    }
    NTL::vec_ZZ_p inputs_p = NTL::conv<NTL::vec_ZZ_p>(inputs);
    NTL::ZZX interp_poly = NTL::conv<NTL::ZZX>(
        NTL::interpolate(inputs_p, NTL::conv<NTL::vec_ZZ_p>(outputs)));
    NTL::vec_ZZ diff;
    for (long i = 2; i <= r; i++) {
      NTL::ZZ curMod = NTL::power(NTL::ZZ(p), i), pfactor = curMod / p;
      { NTL::ZZ_pPush push_i(curMod);
        NTL::ZZ_pX ip = NTL::conv<NTL::ZZ_pX>(interp_poly);
        NTL::vec_ZZ_p diff_p;
        NTL::eval(diff_p, ip, NTL::conv<NTL::vec_ZZ_p>(inputs));
        NTL::sub(diff_p, NTL::conv<NTL::vec_ZZ_p>(outputs), diff_p);
        diff = NTL::conv<NTL::vec_ZZ>(diff_p);
        for (long j = 0; j < diff.length(); j++) diff[j] /= pfactor; }
      interp_poly += NTL::conv<NTL::ZZX>(
          NTL::interpolate(inputs_p, NTL::conv<NTL::vec_ZZ_p>(diff))) * pfactor;
    }
    NTL::ZZ p2r = NTL::power(NTL::ZZ(p), r);
    for (long i = 0; i <= deg(interp_poly); i++) interp_poly[i] %= p2r;

    // structural check: only k = 1 and k = 5 (mod 6) may survive
    long bad = 0;
    for (long i = 0; i <= NTL::deg(interp_poly); i++)
      if (!NTL::IsZero(NTL::coeff(interp_poly, i)) && i != 1 && (i % 6) != 5) bad++;
    if (bad) {
      std::cout << "HELIB_ORDER6: radix " << A6 << " gives " << bad
                << " off-pattern terms; rejected\n";
      continue;
    }

    poly = interp_poly;
    g_filterOrder = 6; g_filterRadix = A6;
    g_foldSupport.clear();
    for (std::map<long, long>::iterator it = lamOf.begin(); it != lamOf.end(); ++it)
      if (it->first) g_foldSupport.insert(NTL::PowerMod(it->first, 6L, p));
    std::cout << "HELIB_ORDER6: A=" << A6 << " |closure|=" << reg.size()
              << " (inflation " << (double)reg.size() / (double)((2*B+1)*(2*B+1))
              << ") deg(P)=" << NTL::deg(poly)
              << " |folded|=" << g_foldSupport.size() << "\n";
    return A6;
  }
  return 0;
}
''' + anchor
s = s.replace(anchor, builder, 1)

# ------------------------------------------------- 2. generalise the split
old = """static bool splitOrderFourCleaner(NTL::ZZX& q,
                                  NTL::ZZ& linearCoeff,
                                  const NTL::ZZX& poly)
{"""
new = """static bool splitFilterCleaner(NTL::ZZX& q,
                               NTL::ZZ& linearCoeff,
                               const NTL::ZZX& poly,
                               long ord)
{
  const long u = ord - 1;   // P = c1*X + X^u * Q(X^ord)"""
assert old in s; s = s.replace(old, new, 1)
old = """    if (i >= 3 && (i % 4) == 3) {
      NTL::SetCoeff(q, (i - 3) / 4, c);
      continue;
    }"""
new = """    if (i >= u && (i % ord) == u) {
      NTL::SetCoeff(q, (i - u) / ord, c);
      continue;
    }"""
assert old in s; s = s.replace(old, new, 1)

# ------------------------------------------------- 3. generalise the evaluator
old = """static bool polyEvalOrderFourCleaner(Ctxt& ret,
                                     const NTL::ZZX& poly,
                                     const Ctxt& x)
{
  NTL::ZZX q;
  NTL::ZZ linearCoeff;
  if (!splitOrderFourCleaner(q, linearCoeff, poly))
    return false;

  Ctxt x2 = x;
  x2.square();
  x2.reLinearize();

  Ctxt x3 = x2;
  x3.multiplyBy(x);
  x3.reLinearize();

  Ctxt x4 = x2;
  x4.square();
  x4.reLinearize();
"""
new = """static bool polyEvalOrderFourCleaner(Ctxt& ret,
                                     const NTL::ZZX& poly,
                                     const Ctxt& x)
{
  const long ord = g_filterOrder, u = ord - 1;
  NTL::ZZX q;
  NTL::ZZ linearCoeff;
  if (!splitFilterCleaner(q, linearCoeff, poly, ord))
    return false;

  // powers x^2 .. x^u and the folding power x^ord (ord-1 non-scalar products)
  std::vector<Ctxt> pw(ord + 1, x);
  for (long k = 2; k <= ord; k++) {
    pw[k] = pw[k - 1];
    pw[k].multiplyBy(x);
    pw[k].reLinearize();
  }
  Ctxt& x3 = pw[u];      // the assembly power X^{ord-1}
  Ctxt& x4 = pw[ord];    // the folding power  X^{ord}
"""
assert old in s; s = s.replace(old, new, 1)

old = """    std::cout << "HELIB_AUX_ORDER4_EVAL enabled: deg(P)=" << NTL::deg(poly)"""
new = """    std::cout << "HELIB_AUX_ORDER4_EVAL enabled: order=" << ord
              << ", deg(P)=" << NTL::deg(poly)"""
assert old in s; s = s.replace(old, new, 1)
s = s.replace("""    if (!pr) { std::cout << "HELIB_COMPOSED_EVAL active: degC=" << P.degC
                         << " d=" << P.d << "\\n"; pr = true; }""",
"""    if (!pr) { std::cout << "HELIB_COMPOSED_EVAL active: order=" << ord
                         << " degC=" << P.degC << " d=" << P.d << "\\n"; pr = true; }""", 1)

# ------------------------------------------------- 4. generalise the plan builder
old = """  // folded support: { (hi*aux+lo)^4 mod p }
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
      NTL::SetCoeff(Qp, (i - 3) / 4, NTL::conv<NTL::ZZ_p>(NTL::coeff(poly, i)));"""
new = """  // folded support { x^ord }: recorded when the order-six polynomial was built,
  // recomputed from the box when the order-four filter is in use.
  const long ord = g_filterOrder, u = ord - 1;
  std::set<long> fold;
  if (!g_foldSupport.empty()) {
    fold = g_foldSupport;
  } else {
    for (long hi = -B; hi <= B; hi++)
      for (long lo = -B; lo <= B; lo++) {
        long x = (((hi % p) * (aux % p) + lo) % p + p) % p;
        if (x == 0) continue;
        fold.insert(NTL::PowerMod(x, ord, p));
      }
  }
  long n = (long)fold.size();

  // Q from P: coefficient of X^{ord*j+u} becomes coefficient of Y^j
  NTL::ZZ_pX Qp;
  for (long i = u; i <= NTL::deg(poly); i++)
    if ((i % ord) == u && !NTL::IsZero(NTL::coeff(poly, i)))
      NTL::SetCoeff(Qp, (i - u) / ord, NTL::conv<NTL::ZZ_p>(NTL::coeff(poly, i)));"""
assert old in s; s = s.replace(old, new, 1)
s = s.replace("""  std::cout << "HELIB_COMPOSED_EVAL: d=" << d << " |folded support|=" << n""",
              """  std::cout << "HELIB_COMPOSED_EVAL: order=" << ord << " d=" << d
            << " |folded support|=" << n""", 1)

# ------------------------------------------------- 5. selection in buildBtsPolys
old = """      extractPolys.SetLength(1);
      compute_prime_aux_poly(extractPolys[0], p, r, bnd, aux);"""
new = """      extractPolys.SetLength(1);
      // Order selection: the order-four radix needs -1 to be a square, so for
      // p = 7 (mod 12) -- every Mersenne prime above 3 -- only the order-six
      // Eisenstein filter exists. HELIB_FILTER_ORDER overrides the choice.
      long a6 = 0;
      { const char* fo = getenv("HELIB_FILTER_ORDER");
        long want = fo ? atol(fo) : ((p % 4 == 3 && p % 3 == 1) ? 6 : 4);
        if (want == 6) a6 = compute_prime_aux_poly_order6(extractPolys[0], p, r, bnd);
        if (want == 6 && !a6)
          std::cout << "HELIB_ORDER6: unavailable at p=" << p
                    << "; falling back to the order-four path\\n"; }
      if (!a6) compute_prime_aux_poly(extractPolys[0], p, r, bnd, aux);"""
assert old in s; s = s.replace(old, new, 1)

# includes
if "#include <set>" not in s:
    s = s.replace("#include <NTL/ZZ_pX.h>", "#include <NTL/ZZ_pX.h>\n#include <set>\n#include <map>\n#include <algorithm>", 1)
open(F, "w").write(s)
print("order-6 pipeline patch applied")
