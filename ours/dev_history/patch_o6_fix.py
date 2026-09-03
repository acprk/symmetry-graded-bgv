#!/usr/bin/env python3
"""Rebuild the order-six construction basis-free, and protect the baseline path.

The first version assumed a coordinate convention for the digit pair and built the
orbit closure in its own radix, which disagreed with the radix the surrounding
recryption uses to recombine digits. This version works directly with field elements:
it starts from the honest box in the pipeline's own parameterisation and propagates
values along the orbit by the covariance relation P(Ax) = A^{-1}(P(x) - x), declining
if any orbit closes inconsistently. It also only deviates from the established
polynomial when the filter is actually switched on, so the baseline arm is untouched.
"""
F = "/home/luck/xzy/0424project/github_order4_cleaner/src/HElib_auxradix_opt/src/extractDigits.cpp"
s = open(F).read()

i = s.index("long compute_prime_aux_poly_order6(NTL::ZZX& poly, long p, long r, long B)")
j = s.index("\n// ==================== composed (r,d) evaluation", i)
new = r'''long compute_prime_aux_poly_order6(NTL::ZZX& poly, long p, long r, long B, long aux)
{
  if (p % 3 != 1) return 0;
  NTL::ZZ p_ZZ(p);
  NTL::ZZ_pPush push(p_ZZ);

  // The order-six unit is whichever of +-aux is a primitive 6th root of unity: the
  // pipeline's digit decomposition uses aux, and -aux spans the same lattice.
  long A6 = 0;
  long cand[2] = { ((aux % p) + p) % p, ((p - (aux % p)) % p) };
  for (int t = 0; t < 2; t++)
    if (((NTL::MulMod(cand[t], cand[t], p) - cand[t]) % p + 1) % p == 0) { A6 = cand[t]; break; }
  if (!A6) {
    std::cout << "HELIB_ORDER6: aux=" << aux << " is not an order-six radix mod p=" << p << "\n";
    return 0;
  }
  long Ainv = NTL::InvMod(A6, p);

  // S0: the honest box in the pipeline's own parameterisation, value = low digit.
  std::map<long, long> val;
  std::vector<long> frontier;
  for (long hi = -B; hi <= B; hi++)
    for (long lo = -B; lo <= B; lo++) {
      long x = ((((hi % p) * (aux % p)) % p + lo) % p + p) % p;
      long v = ((lo % p) + p) % p;
      std::map<long, long>::iterator it = val.find(x);
      if (it != val.end()) {
        if (it->second != v) {
          std::cout << "HELIB_ORDER6: box not injective at aux=" << aux << "\n"; return 0; }
      } else { val[x] = v; frontier.push_back(x); }
    }

  // Orbit closure under x -> A6*x, values propagated by P(Ax) = A^{-1}(P(x) - x).
  // An inconsistent collision means the order-six structure does not close on this
  // region, and we decline rather than emit a wrong polynomial.
  for (int step = 0; step < 6 && !frontier.empty(); step++) {
    std::vector<long> next;
    for (size_t k = 0; k < frontier.size(); k++) {
      long x = frontier[k], v = val[x];
      long ax = NTL::MulMod(x, A6, p);
      long av = NTL::MulMod(NTL::SubMod(v, x, p), Ainv, p);
      std::map<long, long>::iterator it = val.find(ax);
      if (it == val.end()) { val[ax] = av; next.push_back(ax); }
      else if (it->second != av) {
        std::cout << "HELIB_ORDER6: covariance inconsistent at x=" << x << "\n"; return 0; }
    }
    frontier.swap(next);
  }

  NTL::vec_ZZ_p xs, ys; xs.SetLength(val.size()); ys.SetLength(val.size());
  { long i2 = 0;
    for (std::map<long, long>::iterator it = val.begin(); it != val.end(); ++it) {
      xs[i2] = NTL::conv<NTL::ZZ_p>(it->first);
      ys[i2] = NTL::conv<NTL::ZZ_p>(it->second); i2++; } }
  NTL::ZZX interp = NTL::conv<NTL::ZZX>(NTL::interpolate(xs, ys));

  long bad = 0;
  for (long i2 = 0; i2 <= NTL::deg(interp); i2++)
    if (!NTL::IsZero(NTL::coeff(interp, i2)) && i2 != 1 && (i2 % 6) != 5) bad++;
  if (bad) {
    std::cout << "HELIB_ORDER6: " << bad << " off-pattern terms; declining\n"; return 0; }

  poly = interp;
  g_filterOrder = 6; g_filterRadix = A6;
  g_foldSupport.clear();
  for (std::map<long, long>::iterator it = val.begin(); it != val.end(); ++it)
    if (it->first) g_foldSupport.insert(NTL::PowerMod(it->first, 6L, p));
  std::cout << "HELIB_ORDER6: A=" << A6 << " aux=" << aux << " |closure|=" << val.size()
            << " (inflation " << (double)val.size() / (double)((2*B+1)*(2*B+1))
            << ") deg(P)=" << NTL::deg(poly)
            << " |folded|=" << g_foldSupport.size() << "\n";
  return A6;
}
'''
s = s[:i] + new + s[j:]

old = """      long a6 = 0;
      { const char* fo = getenv("HELIB_FILTER_ORDER");
        long want = fo ? atol(fo) : ((p % 4 == 3 && p % 3 == 1) ? 6 : 4);
        if (want == 6) a6 = compute_prime_aux_poly_order6(extractPolys[0], p, r, bnd);
        if (want == 6 && !a6)
          std::cout << "HELIB_ORDER6: unavailable at p=" << p
                    << "; falling back to the order-four path\\n"; }"""
new2 = """      long a6 = 0;
      { const char* fo = getenv("HELIB_FILTER_ORDER");
        // Only deviate from the established path when the filter is switched on: the
        // baseline arm must build exactly the polynomial it always built.
        bool filterOn = envFlagEnabled("HELIB_AUX_ORDER4_EVAL");
        long want = fo ? atol(fo) : 4;
        if (filterOn && want == 6)
          a6 = compute_prime_aux_poly_order6(extractPolys[0], p, r, bnd, aux);
        if (filterOn && want == 6 && !a6)
          std::cout << "HELIB_ORDER6: unavailable at p=" << p
                    << "; falling back to the order-four path\\n"; }"""
assert old in s
s = s.replace(old, new2, 1)
open(F, "w").write(s)
print("order-6 builder rewritten basis-free; baseline path protected")
