/* Copyright (C) 2012-2020 IBM Corp.
 * This program is Licensed under the Apache License, Version 2.0
 * (the "License"); you may not use this file except in compliance
 * with the License. You may obtain a copy of the License at
 *   http://www.apache.org/licenses/LICENSE-2.0
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License. See accompanying LICENSE file.
 */
/* EncryptedArray.cpp - Data-movement operations on arrays of slots
 */
#include <set>
#include <map>
#include <vector>
#include <utility>
#include <algorithm>
#include <NTL/ZZ.h>
#include <NTL/ZZ_p.h>
#include <helib/EncryptedArray.h>
#include <helib/polyEval.h>
#include <helib/debugging.h>
#include <cstdlib>
#include <iostream>
#include <NTL/ZZ_pE.h>
#include <NTL/ZZ_pEX.h>
#include <NTL/ZZ_pXFactoring.h>
#include <NTL/ZZ_pEXFactoring.h>
#include <set>

namespace helib {

// Compute a degree-p polynomial poly(x) s.t. for any t<e and integer z of the
// form z = z0 + p^t*z1 (with 0<=z0<p), we have poly(z) = z0 (mod p^{t+1}).
//
// We get poly(x) by interpolating a degree-(p-1) polynomial poly'(x)
// s.t. poly'(z0)=z0 - z0^p (mod p^e) for all 0<=z0<p, and then setting
// poly(x) = x^p + poly'(x).
void buildDigitPolynomial(NTL::ZZX& result, long p, long e)
{
  if (p < 2 || e <= 1)
    return; // nothing to do
  HELIB_TIMER_START;
  long p2e = NTL::power_long(p, e); // the integer p^e

  // Compute x - x^p (mod p^e), for x=0,1,...,p-1
  NTL::vec_long x(NTL::INIT_SIZE, p);
  NTL::vec_long y(NTL::INIT_SIZE, p);
  long bottom = -(p / 2);
  for (long j = 0; j < p; j++) {
    long z = bottom + j;
    x[j] = z;
    y[j] =
        z - NTL::PowerMod((z < 0 ? z + p2e : z), p, p2e); // x - x^p (mod p^e)

    while (y[j] > p2e / 2)
      y[j] -= p2e;
    while (y[j] < -(p2e / 2))
      y[j] += p2e;
  }
  interpolateMod(result, x, y, p, e);
  // interpolating p points, should get deg<=p-1
  assertTrue(deg(result) < p, "Interpolation error.  Degree too high.");
  SetCoeff(result, p); // return result = x^p + poly'(x)
  //  cerr << "# digitExt mod "<<p<<"^"<<e<<"="<<result<<endl;
  HELIB_TIMER_STOP;
}

// extractDigits assumes that the slots of *this contains integers mod p^r
// i.e., that only the free terms are nonzero. (If that assumptions does
// not hold then the result will not be a valid ciphertext anymore.)
//
// It returns in the slots of digits[j] the j'th-lowest digits from the
// integers in the slots of the input. Namely, the i'th slot of digits[j]
// contains the j'th digit in the p-base expansion of the integer in the
// i'th slot of the *this. The plaintext space of digits[j] is mod p^{r-j},
// and all the digits are at the same level.

int fhe_watcher = 0;

void extractDigits(std::vector<Ctxt>& digits, const Ctxt& c, long r)
{
  const Context& context = c.getContext();
  long rr = c.effectiveR();
  if (r <= 0 || r > rr)
    r = rr; // how many digits to extract

  long p = context.getP();

  assertTrue(r == context.getDebugRR(), "rr doesn't match");

  const NTL::ZZX& x2p = context.getLiftPoly();
  // if (p > 3) {
  //   buildDigitPolynomial(x2p, p, r);
  // }

  Ctxt tmp(c.getPubKey(), c.getPtxtSpace());
  digits.resize(r, tmp); // allocate space

#ifdef HELIB_DEBUG
  fprintf(stderr, "***\n");
#endif
  for (long i = 0; i < r; i++) {
    tmp = c;
    for (long j = 0; j < i; j++) {

      if (p == 2)
        digits[j].square();
      else if (p == 3)
        digits[j].cube();
      else
        polyEval(digits[j], x2p, digits[j]);
        // "in spirit" digits[j] = digits[j]^p

#ifdef HELIB_DEBUG
      fprintf(stderr, "%5ld", digits[j].bitCapacity());
#endif

      tmp -= digits[j];
      tmp.divideByP();
    }
    digits[i] = tmp; // needed in the next round

#ifdef HELIB_DEBUG
    if (dbgKey) {
      double ratio = log(embeddingLargestCoeff(digits[i], *dbgKey) /
                         digits[i].getNoiseBound()) /
                     log(2.0);
      fprintf(stderr, "%5ld [%f]", digits[i].bitCapacity(), ratio);
      if (ratio > 0)
        fprintf(stderr, " BAD-BOUND");
      fprintf(stderr, "\n");
    } else {
      fprintf(stderr, "%5ld\n", digits[i].bitCapacity());
    }
#endif
  }

#ifdef HELIB_DEBUG
  fprintf(stderr, "***\n");
#endif
}

static void compute_a_vals(NTL::Vec<NTL::ZZ>& a, long p, long e)
// computes a[m] = a(m)/m! for m = p..(e-1)(p-1)+1,
// as defined by Chen and Han.
// a.length() is set to (e-1)(p-1)+2

{
  NTL::ZZ p_to_e = NTL::power_ZZ(p, e);
  NTL::ZZ p_to_2e = NTL::power_ZZ(p, 2 * e);

  long len = (e - 1) * (p - 1) + 2;

  NTL::ZZ_pPush push(p_to_2e);

  NTL::ZZ_pX x_plus_1_to_p = power(NTL::ZZ_pX(NTL::INIT_MONO, 1) + 1, p);
  NTL::ZZ_pX denom =
      InvTrunc(x_plus_1_to_p - NTL::ZZ_pX(NTL::INIT_MONO, p), len);
  NTL::ZZ_pX poly = MulTrunc(x_plus_1_to_p, denom, len);
  poly *= p;

  a.SetLength(len);

  NTL::ZZ m_fac(1);
  for (long m = 2; m < p; m++) {
    m_fac = MulMod(m_fac, m, p_to_2e);
  }

  for (long m = p; m < len; m++) {
    m_fac = MulMod(m_fac, m, p_to_2e);
    NTL::ZZ c = rep(coeff(poly, m));
    NTL::ZZ d = GCD(m_fac, p_to_2e);
    if (d == 0 || d > p_to_e || c % d != 0)
      throw RuntimeError("cannot divide");
    NTL::ZZ m_fac_deflated = (m_fac / d) % p_to_e;
    NTL::ZZ c_deflated = (c / d) % p_to_e;
    a[m] = MulMod(c_deflated, InvMod(m_fac_deflated, p_to_e), p_to_e);
  }
}

// This computes Chen and Han's magic polynomial G, which
// has the property that G(x) = (x mod p) (mod p^e).
// Here, (x mod p) is in the interval [0,1] if p == 2,
// and otherwise, is in the interval (-p/2, p/2).
void compute_magic_poly(NTL::ZZX& poly1, long p, long e)
{
  HELIB_TIMER_START;

  // NOTE: this can be really time-consuming for large p
  // thus, we store the computed value into files
  // and load them later
  const char* cacheDir = std::getenv("HELIB_ZZX_CACHE_DIR");
  if (cacheDir == nullptr || cacheDir[0] == '\0')
    cacheDir = "cache/saved_ZZX";
  char buf[512] = "";
  snprintf(buf, sizeof(buf), "%s/%ld_%ld_ZZX.txt", cacheDir, p, e);
  {
    FILE* file = fopen(buf, "r");
    if (file != nullptr) {
      long tmp;
      long idx = 0;
      while (fscanf(file, "%ld", &tmp) > 0) {
        NTL::SetCoeff(poly1, idx, tmp);
        idx++;
      }
      fclose(file);
      std::cerr << "read file " << buf << '\n';
      return;
    }
  }

  NTL::Vec<NTL::ZZ> a;

  compute_a_vals(a, p, e);

  NTL::ZZ p_to_e = NTL::power_ZZ(p, e);
  long len = (e - 1) * (p - 1) + 2;

  NTL::ZZ_pPush push(p_to_e);

  NTL::ZZ_pX poly(0);
  NTL::ZZ_pX term(1);
  NTL::ZZ_pX X(NTL::INIT_MONO, 1);

  poly = 0;
  term = 1;

  for (long m = 0; m < p; m++) {
    term *= (X - m);
  }

  for (long m = p; m < len; m++) {
    poly += term * NTL::conv<NTL::ZZ_p>(a[m]);
    term *= (X - m);
  }

  // replace poly by poly(X+(p-1)/2) for odd p
  if (p % 2 == 1) {
    NTL::ZZ_pX poly2(0);

    for (long i = deg(poly); i >= 0; i--)
      poly2 = poly2 * (X + (p - 1) / 2) + poly[i];

    poly = poly2;
  }

  poly = X - poly;
  poly1 = NTL::conv<NTL::ZZX>(poly);

  // write to file for large p
  if (p > 1000) {
    // ensure cache directory exists
    std::string dirPath(cacheDir);
    std::string mkdirCmd = "mkdir -p " + dirPath;
    int rc = system(mkdirCmd.c_str());
    (void)rc;

    FILE* file = fopen(buf, "w");
    if (file != nullptr) {
      for (long i = 0; i <= NTL::deg(poly1); i++)
        fprintf(file, "%ld\n", NTL::to_long(poly1[i]));
      fclose(file);
      std::cerr << "write file " << buf << '\n';
    }
  }
}

// return p-valuation of x
static long valuation(long x, long p)
{
  long val = 0;
  while (x % p == 0) {
    val++;
    x /= p;
  }
  return val;
}

// return p-valuation of factorial(n)
static long valuationFactorial(long n, long p)
{
  long i = p;
  long val = 0;
  while (i <= n) {
    val += valuation(i, p);
    i += p;
  }
  return val;
}

// return min(i) s.t. p^e | factorial(i)
// NOTE: seems unused...
// static long smarandache(long p, long e)
// {
//   long i = p;
//   long count = 0;
//   while (true) {
//     count += valuation(i, p);
//     if (count >= e)
//       return i;
//     i += p;
//   }
// }

// return min(i), s.t., p^e | ((n+i)*...*(n+1))
static long truncated_smarandache(long n, long p, long e)
{
  // start from p*ceil((n+1)/p)
  long i = p*(1+n/p);
  long count = 0;
  while (true) {
    count += valuation(i, p);
    if(count >= e)
      return i;
    i += p;
  }
  return i - n;
}

// n consecutive numbers S={i,i+1,...i+n-1}
// compute min(valuation(Prod(S \ {j})), for j in S
static long absent_valuation(long n, long p)
{
  long val = valuationFactorial(n - 1, p);
  val -= floor(log(n - 1) / log(p));
  return val;
}

// compute the local null polynomial
void compute_null_poly(NTL::ZZX& poly,
                       long p,
                       long e,
                       long t,
                       long B,
                       bool isFirstRow)
{
  // assertTrue(t <= 2, "t > 2 not supported");
  // each digit lies in [lo, hi]
  // we assume here p is odd
  long hi = (p - 1) >> 1;
  long lo = -hi;
  // secondDigitHi * p + hi >= B, xxx = ceil((B - hi) / p)
  long secondDigitHi = (B - hi + p - 1) / p;
  // secondDigitLo * p + lo <= -B, xxx = floor((-B - lo) / p)
  // NOTE: negative numbers are rounded toward 0
  long secondDigitLo = (-B - lo - p + 1) / p;

  long curHi = isFirstRow ? B : secondDigitHi;
  long curLo = isFirstRow ? -B : secondDigitLo;

  // the p-valuation of Prod(x-i) for i in [lo,hi]
  long pexp = absent_valuation(curHi - curLo + 1, p) + t;
  long nparts = e / pexp;
  long pexp_total = valuationFactorial(nparts, p) + nparts * pexp;
  while(pexp_total > e) {
    nparts--;
    pexp_total = valuationFactorial(nparts, p) + nparts * pexp;
  }
  // now, increasing nparts by 1 will guarantee pexp_total >= e
  // however, it may not be the optimal strategy
  long trunc_deg = 0;
  if (pexp_total < e){
    long tmp_trunc_deg = truncated_smarandache(curHi - curLo + 1, p, e - pexp_total);
    if (tmp_trunc_deg < (curHi - curLo + 1)){
      trunc_deg = tmp_trunc_deg;
      std::cout << "using truncated smarandache of degree " << tmp_trunc_deg << " < " << (curHi - curLo + 1) << "\n";
    }
    else
      nparts++;
  }
  NTL::ZZ p2e = NTL::power(NTL::ZZ(p), e);
  NTL::ZZ_pPush push(p2e);
  // std::cout << "current ZZ_p modulus " << NTL::ZZ_p::modulus() << "\n";
  NTL::ZZ_pX nullpoly(1), basicPoly(1), tmpPoly;
  NTL::SetCoeff(tmpPoly, 1, 1);
  for (long i = curLo; i <= curHi; i++) {
    NTL::SetCoeff(tmpPoly, 0, -i);
    basicPoly *= tmpPoly;
  }
  long p2pexp = NTL::power_long(p, pexp);
  for (long i = 0; i < nparts; i++) {
    tmpPoly = basicPoly;
    tmpPoly[0] -= i * p2pexp;
    nullpoly *= tmpPoly;
  }
  // finally mult by the truncated poly
  tmpPoly = NTL::ZZ_pX::zero();
  NTL::SetCoeff(tmpPoly, 1, 1);
  for (long i = curHi + 1; i <= curHi + trunc_deg; i++) {
    NTL::SetCoeff(tmpPoly, 0, -i);
    nullpoly *= tmpPoly;
  }
#ifdef HELIB_DEBG
  // XXX: debug
  if (isFirstRow == false) {
    for (long low = curLo; low <= curHi; low++)
      for (long high = 0; high < NTL::power_long(p, e - 1); high++) {
        long xin = high * p + low;
        auto res = NTL::eval(nullpoly, NTL::conv<NTL::ZZ_p>(xin));
        if (res != NTL::ZZ_p::zero())
          assertTrue(false, "not a null poly?");
      }
    std::cout << "is indeed a null poly\n";
  }
  // XXX: debug
#endif
  poly = NTL::conv<NTL::ZZX>(nullpoly);
}

// compute the digit extraction poly for ptxt space p^r and |I| <= B
void compute_prime_aux_poly(NTL::ZZX& poly, long p, long r, long B, long aux)
{
  NTL::ZZ p_ZZ(p);
  // NOTE: NTL::ZZ_pPush push(NTL::ZZ(p)) is buggy?
  NTL::ZZ_pPush push(p_ZZ);
  // std::cout << "current ZZ_p modulus " << NTL::ZZ_p::modulus() << "\n";
  NTL::ZZX interp_poly, diff_poly;
  NTL::vec_ZZ inputs, outputs;
  // long I_range = (2 * B + 1) * (2 * B + 1);

  for (long hi = -B; hi <= B; hi++)
    for (long lo = -B; lo <= B; lo++) {
      inputs.append(NTL::ZZ(hi * aux + lo));
      outputs.append(NTL::ZZ(lo));
    }

  NTL::vec_ZZ_p inputs_p = NTL::conv<NTL::vec_ZZ_p>(inputs);
  interp_poly = NTL::conv<NTL::ZZX>(
      NTL::interpolate(inputs_p, NTL::conv<NTL::vec_ZZ_p>(outputs)));
  // now lift the poly to Z_p^r
  NTL::vec_ZZ diff;
  for (long i = 2; i <= r; i++) {
    NTL::ZZ curMod = NTL::power(NTL::ZZ(p), i);
    NTL::ZZ pfactor = curMod / p;
    { // working modulo p^i
      NTL::ZZ_pPush push_i(curMod);
      NTL::ZZ_pX interp_poly_p = NTL::conv<NTL::ZZ_pX>(interp_poly);
      NTL::vec_ZZ_p diff_p;
      NTL::eval(diff_p, interp_poly_p, NTL::conv<NTL::vec_ZZ_p>(inputs));
      // [f(X)]_p^(i-1) - f(X) == p * I(X) mod p^i
      NTL::sub(diff_p, NTL::conv<NTL::vec_ZZ_p>(outputs), diff_p);
      diff = NTL::conv<NTL::vec_ZZ>(diff_p);

      for (long j = 0; j < diff.length(); j++)
        diff[j] /= pfactor;
    }
    // now the modulus is back to p
    interp_poly +=
        NTL::conv<NTL::ZZX>(
            NTL::interpolate(inputs_p, NTL::conv<NTL::vec_ZZ_p>(diff))) *
        pfactor;
  }
  NTL::ZZ p2r = NTL::power(NTL::ZZ(p), r);
  for (long i = 0; i <= deg(interp_poly); i++)
    interp_poly[i] %= p2r;
  poly = interp_poly;
}


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
long compute_prime_aux_poly_order6(NTL::ZZX& poly, long p, long r, long B, long aux)
{
  if (p % 3 != 1) return 0;
  if (r != 1) {
    // The closure values are general field elements, so the Hensel lift of the
    // order-four builder does not carry over verbatim; decline instead of guessing.
    std::cout << "HELIB_ORDER6: r=" << r << " > 1 not supported by this builder\n";
    return 0;
  }
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

// BSGS evaluation of sum_i ck[i] * X^i at a ciphertext power, over slot-encoded
// constants. Depth O(log deg), unlike a Horner chain whose depth equals the degree.
static Ctxt composedBsgsEnc(const Ctxt& x, const std::vector<NTL::ZZX>& ck) {
  long k = (long)ck.size() - 1;                    // degree
  long kap = 1; while (kap * kap < k + 1) kap++;   // baby-step count ~ sqrt
  std::vector<Ctxt> baby;
  baby.push_back(Ctxt(x.getPubKey(), x.getPtxtSpace()));  // X^0 placeholder
  baby.push_back(x);
  for (long i = 2; i <= kap; i++) {
    long h = i / 2; Ctxt t = baby[h];
    if (i - h == h) { t.square(); t.reLinearize(); }
    else { t.multiplyBy(baby[i - h]); t.reLinearize(); }
    baby.push_back(t);
  }
  long nb = (k + 1 + kap - 1) / kap;
  auto block = [&](long blk) {
    Ctxt part(x.getPubKey(), x.getPtxtSpace()); part.clear(); bool e = true;
    for (long i = 0; i < kap; i++) {
      long idx = blk * kap + i; if (idx > k) break;
      Ctxt t(x.getPubKey(), x.getPtxtSpace());
      if (i == 0) { t.clear(); t.addConstant(ck[idx]); }
      else { t = baby[i]; t.multByConstant(ck[idx]); }
      if (e) { part = t; e = false; } else part += t;
    }
    return part;
  };
  Ctxt acc = block(nb - 1);
  for (long blk = nb - 2; blk >= 0; blk--) {
    acc.multiplyBy(baby[kap]); acc.reLinearize();
    acc += block(blk);
  }
  return acc;
}

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
__attribute__((used)) static void buildComposedPlan(const NTL::ZZX& poly, long p, long B, long aux,
                              long d, const EncryptedArray& ea)
{
  ComposedPlan& P = g_composedPlan;
  if (P.built) return;
  P.built = true; P.d = d;
  if (d < 2) { std::cout << "HELIB_COMPOSED_EVAL: d=" << d
                         << ", Galois axis trivial; staying on P-S\n"; return; }
  NTL::ZZ_pPush push(NTL::conv<NTL::ZZ>(p));

  // folded support { x^ord }: recorded when the order-six polynomial was built,
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
      NTL::SetCoeff(Qp, (i - u) / ord, NTL::conv<NTL::ZZ_p>(NTL::coeff(poly, i)));

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
  std::cout << "HELIB_COMPOSED_EVAL: order=" << ord << " d=" << d
            << " |folded support|=" << n
            << " degQ=" << NTL::deg(Qp) << " padded to n'=" << ntar << "\n";

  double t0 = NTL::GetTime();
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
              << " (search " << NTL::GetTime() - t0 << "s)\n";
    break;
  }
  if (!P.ok) std::cout << "HELIB_COMPOSED_EVAL: no norm form found; staying on P-S\n";
}
// =============================================================================

static bool envFlagEnabled(const char* name)
{
  const char* flag = std::getenv(name);
  return flag != nullptr && flag[0] != '\0' && flag[0] != '0';
}

static long countNonZeroTerms(const NTL::ZZX& poly)
{
  long count = 0;
  for (long i = 0; i <= NTL::deg(poly); i++)
    if (!NTL::IsZero(NTL::coeff(poly, i)))
      count++;
  return count;
}

static bool splitFilterCleaner(NTL::ZZX& q,
                               NTL::ZZ& linearCoeff,
                               const NTL::ZZX& poly,
                               long ord)
{
  const long u = ord - 1;   // P = c1*X + X^u * Q(X^ord)
  q = NTL::ZZX::zero();
  linearCoeff = NTL::ZZ::zero();

  for (long i = 0; i <= NTL::deg(poly); i++) {
    const NTL::ZZ& c = NTL::coeff(poly, i);
    if (NTL::IsZero(c))
      continue;

    if (i == 1) {
      linearCoeff = c;
      continue;
    }

    if (i >= u && (i % ord) == u) {
      NTL::SetCoeff(q, (i - u) / ord, c);
      continue;
    }

    return false;
  }

  q.normalize();
  return NTL::deg(q) >= 0 || !NTL::IsZero(linearCoeff);
}

static bool polyEvalOrderFourCleaner(Ctxt& ret,
                                     const NTL::ZZX& poly,
                                     const Ctxt& x)
{
  const long ord = g_filterOrder, u = ord - 1;
  NTL::ZZX q;
  NTL::ZZ linearCoeff;
  if (!splitFilterCleaner(q, linearCoeff, poly, ord))
    return false;

  // powers x^u (assembly) and x^ord (folding). Only these two are used below;
  // for ord=6 a balanced schedule reaches both in 4 products at depth 3
  // (x^2, x^3=x^2*x, x^6=(x^3)^2, x^5=x^2*x^3) instead of the 5-product,
  // depth-5 sequential chain x^2,x^3,x^4,x^5,x^6. For ord=4 the sequential
  // chain is already minimal (3 products): x^3 is itself a needed stepping
  // stone to x^4 there, unlike x^4 for ord=6.
  std::vector<Ctxt> pw(ord + 1, x);
  if (ord == 6) {
    pw[2] = pw[1]; pw[2].multiplyBy(x); pw[2].reLinearize();       // x^2
    pw[3] = pw[2]; pw[3].multiplyBy(x); pw[3].reLinearize();       // x^3
    pw[6] = pw[3]; pw[6].multiplyBy(pw[3]); pw[6].reLinearize();   // x^6 = (x^3)^2
    pw[5] = pw[2]; pw[5].multiplyBy(pw[3]); pw[5].reLinearize();   // x^5 = x^2*x^3
  } else {
    for (long k = 2; k <= ord; k++) {
      pw[k] = pw[k - 1];
      pw[k].multiplyBy(x);
      pw[k].reLinearize();
    }
  }
  Ctxt& x3 = pw[u];      // the assembly power X^{ord-1}
  Ctxt& x4 = pw[ord];    // the folding power  X^{ord}

  Ctxt qEval(x.getPubKey(), x.getPtxtSpace());

  // ---- composed branch: Q evaluated through the Galois norm map ------------
  if (NTL::deg(q) >= 0 && g_composedPlan.ok) {
    const ComposedPlan& P = g_composedPlan;
    Ctxt acc = composedBsgsEnc(x4, P.ck);   // BSGS: depth O(log degC), not degC
    Ctxt orb = composedOrbitProduct(acc, P.d);
    if (P.sgn < 0) orb.negate();
    orb.multByConstant(NTL::to_ZZ(P.cmul));
    orb.multiplyBy(x3); orb.reLinearize();
    if (!NTL::IsZero(linearCoeff)) {
      Ctxt linear = x; linear.multByConstant(linearCoeff); orb += linear;
    }
    ret = orb;
    static bool pr = false;
    if (!pr) { std::cout << "HELIB_COMPOSED_EVAL active: order=" << ord
                         << " degC=" << P.degC << " d=" << P.d << "\n"; pr = true; }
    return true;
  }
  // -------------------------------------------------------------------------

  if (NTL::deg(q) >= 0) {
    // NOTE: this artifact evaluates Q by the standard Paterson-Stockmeyer path.
    // The paper notes (Related Work) that the scalar filter composes orthogonally
    // with the asymmetric BSGS method of a separate line of work; we do not ship
    // an implementation of that separate method here, since no table in this
    // paper depends on it.
    std::vector<Ctxt*> qRet{&qEval};
    NTL::vec_ZZX qVec;
    qVec.SetLength(1);
    qVec[0] = q;
    polyEvalNew(qRet, qVec, x4);
    qEval.multiplyBy(x3);
    qEval.reLinearize();
  } else {
    qEval.clear();
  }

  if (!NTL::IsZero(linearCoeff)) {
    Ctxt linear = x;
    linear.multByConstant(linearCoeff);
    qEval += linear;
  }

  ret = qEval;

  static bool printed = false;
  if (!printed) {
    std::cout << "HELIB_AUX_ORDER4_EVAL enabled: order=" << ord
              << ", deg(P)=" << NTL::deg(poly)
              << ", terms(P)=" << countNonZeroTerms(poly)
              << ", deg(Q)=" << NTL::deg(q)
              << ", terms(Q)=" << countNonZeroTerms(q) << "\n";
    printed = true;
  }

  return true;
}

// extendExtractDigits assumes that the slots of *this contains integers mod
// p^{r+e} i.e., that only the free terms are nonzero. (If that assumptions
// does not hold then the result will not be a valid ciphertext anymore.)
//
// It returns in the slots of digits[j] the j'th-lowest digits from the
// integers in the slots of the input. Namely, the i'th slot of digits[j]
// contains the j'th digit in the p-base expansion of the integer in the i'th
// slot of the *this.  The plaintext space of digits[j] is mod p^{e+r-j}.
//
// the notation here is slightly different from the outside
// r is the number of lower digits to discard, r = caller botHigh = e - e'
// e is the number of higher digits to keep, e = caller r
void extendExtractDigits(std::vector<Ctxt>& digits,
                         const Ctxt& c,
                         long r,
                         long e)
{
  const Context& context = c.getContext();

  assertTrue(r == context.getDebugRR(), "rr doesn't match");
  assertTrue(e == context.getDebugEE(), "ee doesn't match");

  long p = context.getP();
  const NTL::ZZX& x2p = context.getLiftPoly();
  // if (p > 3) {
  // buildDigitPolynomial(x2p, p, r);
  // }

  // we should pre-compute this table
  // for i = 0..r-1, entry i is G_{e+r-i} in Chen and Han
  const NTL::Vec<NTL::ZZX>& G = context.getExtractPolys();
  // G.SetLength(r);
  // for (long i : range(r)) {
  //   compute_magic_poly(G[i], p, e + r - i);
  // }

  std::vector<Ctxt> digits0;

  Ctxt tmp(c.getPubKey(), c.getPtxtSpace());

  digits.resize(r, tmp); // allocate space
  digits0.resize(r, tmp);

#ifdef HELIB_DEBUG
  fprintf(stderr, "***\n");
#endif
  for (long i : range(r)) {
    tmp = c;
    for (long j : range(i)) {
      if (digits[j].capacity() >= digits0[j].capacity()) {
        // optimization: digits[j] is better than digits0[j],
        // so just use it

        tmp -= digits[j];
#ifdef HELIB_DEBUG
        fprintf(stderr, "%5ld*", digits[j].bitCapacity());
#endif
      } else {
        if (p == 2)
          digits0[j].square();
        else if (p == 3)
          digits0[j].cube();
        else
          polyEval(digits0[j],
                   x2p,
                   digits0[j]); // "in spirit" digits0[j] = digits0[j]^p

        tmp -= digits0[j];
#ifdef HELIB_DEBUG
        fprintf(stderr, "%5ld ", digits0[j].bitCapacity());
#endif
      }
      tmp.divideByP();
    }
    digits0[i] = tmp; // needed in the next round
    polyEval(digits[i], G[i], tmp);

#ifdef HELIB_DEBUG
    if (dbgKey) {
      double ratio = log(embeddingLargestCoeff(digits[i], *dbgKey) /
                         digits[i].getNoiseBound()) /
                     log(2.0);
      fprintf(stderr,
              "%5ld  --- %5ld",
              digits0[i].bitCapacity(),
              digits[i].bitCapacity());
      fprintf(stderr, " [%f]", ratio);
      if (ratio > 0)
        fprintf(stderr, " BAD-BOUND");
      fprintf(stderr, "\n");
    } else {
      fprintf(stderr,
              "%5ld  --- %5ld\n",
              digits0[i].bitCapacity(),
              digits[i].bitCapacity());
    }
#endif
  }
}

void newExtractDigits(std::vector<Ctxt>& digits, const Ctxt& c)
{
  const Context& context = c.getContext();

  long t = context.getT();
  // long aux = context.getAux();
  // long B = ceil(context.boundForRecryption());
  long numExtract = context.getNumExtract();

  Ctxt tmp(c.getPubKey(), c.getPtxtSpace());

#if 1
  if (t < 0) {
    // non-power-of-p aux
    // now the digit extraction is actually interpolation within the lowest
    // digit
    digits.resize(1, tmp);
    const NTL::Vec<NTL::ZZX>& extractPolys = context.getExtractPolys();
    if (!(envFlagEnabled("HELIB_AUX_ORDER4_EVAL") &&
          extractPolys.length() == 1 &&
          polyEvalOrderFourCleaner(digits[0], extractPolys[0], c))) {
      if (envFlagEnabled("HELIB_AUX_ORDER4_EVAL"))
        std::cout << "HELIB_AUX_ORDER4_EVAL skipped: cleaner does not have "
                     "the required order-four support\n";
      std::vector<Ctxt*> ctxt_ptr_vec{&digits[0]};
      polyEvalNew(ctxt_ptr_vec, extractPolys, c);
    }
  } else {
    // power-of-p aux
    // numExtract is either 1 or 2
    digits.resize(numExtract, tmp);
    NTL::vec_ZZX firstRowPolys;
    firstRowPolys.SetLength(1);
    std::vector<Ctxt*> ctxt_ptr_vec;
    firstRowPolys[0] = context.getExtractPolys()[0];
    // compute_magic_poly(firstRowPolys[0], p, eNew);
    if (numExtract == 1) {
      ctxt_ptr_vec.push_back(&digits[0]);
      polyEvalNew(ctxt_ptr_vec, firstRowPolys, c);
    } else if (numExtract == 2) {
      NTL::vec_ZZX secondRowPolys;
      secondRowPolys.SetLength(1);
      // index 0 -> ext poly; index 1 -> lift poly
      firstRowPolys.SetLength(2);
      firstRowPolys[1] = context.getLiftPoly();
      secondRowPolys[0] = context.getExtractPolys()[1];
      // buildDigitPolynomial(firstRowPolys[1], p, 2);
      // compute_magic_poly(secondRowPolys[0], p, eNew - 1);

      // polyEval(tmp, x2p, c);
      ctxt_ptr_vec.push_back(&digits[0]);
      ctxt_ptr_vec.push_back(&tmp);
      polyEvalNew(ctxt_ptr_vec, firstRowPolys, c);

#ifdef HELIB_DEBUG
      // XXX: debug
      {
        long p = context.getP();
        long p2t = NTL::power_long(p, context.getT());
        // long p2eNew = NTL::power_long(p, context.getENew());
        auto ea = context.getRcData().ea;
        std::vector<NTL::ZZX> c_slots, tmp_slots;
        ea->decrypt(c, *dbgKey, c_slots);
        ea->decrypt(tmp, *dbgKey, tmp_slots);
        long n_slots = c_slots.size();
        for (long i = 0; i < n_slots; i++) {
          if (NTL::deg(c_slots[i]) == -1)
            continue;
          long c_val = balRem(NTL::rem(c_slots[i][0], p2t), p2t);
          long tmp_val = balRem(NTL::rem(tmp_slots[i][0], p2t), p2t);
          if (abs(tmp_val) > p / 2)
            assertTrue(false, "tmp_val wrong");
          if ((c_val - tmp_val) % p != 0)
            assertTrue(false, "mod wrong");
          if (std::abs((c_val - tmp_val) / p) > 1)
            assertTrue(false, "high digit wrong");
        }
      }
      // XXX: end debug
#endif

      // tmp = lift(c)
      tmp -= c;
      tmp.negate();
      tmp.divideByP(); // (c - lift(c)) / p, input to the second row

      ctxt_ptr_vec.clear();
      ctxt_ptr_vec.push_back(&digits[1]);
      polyEvalNew(ctxt_ptr_vec, secondRowPolys, tmp);

#ifdef HELIB_DEBUG
      // XXX: debug
      {
        long p = context.getP();
        long p2t = NTL::power_long(p, context.getT());
        long p2eNew = NTL::power_long(p, context.getENew());
        auto ea = context.getRcData().ea;
        std::vector<NTL::ZZX> c_slots, tmp_slots, d0_slots, d1_slots;
        ea->decrypt(c, *dbgKey, c_slots);
        ea->decrypt(tmp, *dbgKey, tmp_slots);
        ea->decrypt(digits[0], *dbgKey, d0_slots);
        ea->decrypt(digits[1], *dbgKey, d1_slots);
        // now check
        // (1) tmp_slots is indeed the second digit
        // (2) digits[1] is ok
        long n_slots = c_slots.size();
        for (long i = 0; i < n_slots; i++) {
          if (NTL::deg(c_slots[i]) == -1)
            continue;
          long c_val = balRem(NTL::rem(c_slots[i][0], p2t), p2t);
          long tmp_val, d0_val, d1_val;
          if (c_val % p != 0) { // check first digit
            d0_val = balRem(NTL::rem(d0_slots[i][0], p2eNew), p2eNew);
            if ((c_val - d0_val) % p != 0)
              assertTrue(false, "d0 wrong");
            c_val = balRem((c_val - d0_val) / p, p);
          } else {
            assertTrue(NTL::deg(d0_slots[i]) == -1, "aaa");
            c_val /= p;
          }
          // check second digit
          if (c_val != 0) {
            tmp_val = balRem(NTL::rem(tmp_slots[i][0], p), p);
            d1_val = balRem(NTL::rem(d1_slots[i][0], p2eNew / p), p2eNew / p);
            if (c_val != tmp_val)
              assertTrue(false, "tmp wrong");
            if (tmp_val != d1_val) {
              // directly evaluate it
              NTL::ZZ curMod(p2eNew / p);
              NTL::ZZ_pPush push(curMod);
              NTL::ZZX secondExtPoly = context.getExtractPolys()[1];
              for (long ii = 0; ii <= NTL::deg(secondExtPoly); ii += 2)
                NTL::SetCoeff(secondExtPoly, ii, 0);
              secondExtPoly.normalize();
              auto polyeval = NTL::eval(NTL::conv<NTL::ZZ_pX>(secondExtPoly),
                                        NTL::conv<NTL::ZZ_p>(tmp_slots[i][0]));
              long polyeval_val =
                  balRem(NTL::rem(NTL::conv<NTL::ZZ>(polyeval), p2eNew / p),
                         p2eNew / p);
              assertTrue(polyeval_val == tmp_val, "......");
              assertTrue(false, "d1 wrong");
            }
          }
        }
      }
      // XXX: end debug
#endif
    } else
      assertTrue(false, "extracting more than 2 digits is not supported");
  }
#else // XXX: only for testing, use the native polynomials

  long p = context.getP();
  long eNew = context.getENew();
  if (t > 0) { // ignore the t < 0 case...
    digits.resize(numExtract, tmp);
    NTL::vec_ZZX firstRowPolys;
    firstRowPolys.SetLength(1);
    std::vector<Ctxt*> ctxt_ptr_vec;
    compute_magic_poly(firstRowPolys[0], p, eNew);
    if (numExtract == 1) {
      ctxt_ptr_vec.push_back(&digits[0]);
      polyEvalNew(ctxt_ptr_vec, firstRowPolys, c);
    } else if (numExtract == 2) {
      NTL::vec_ZZX secondRowPolys;
      secondRowPolys.SetLength(1);
      // index 0 -> ext poly; index 1 -> lift poly
      firstRowPolys.SetLength(2);
      buildDigitPolynomial(firstRowPolys[1], p, 2);
      compute_magic_poly(secondRowPolys[0], p, eNew - 1);

      // polyEval(tmp, x2p, c);
      ctxt_ptr_vec.push_back(&digits[0]);
      ctxt_ptr_vec.push_back(&tmp);
      polyEvalNew(ctxt_ptr_vec, firstRowPolys, c);
      // tmp = lift(c)
      tmp -= c;
      tmp.negate();
      tmp.divideByP(); // (c - lift(c)) / p, input to the second row

      ctxt_ptr_vec.clear();
      ctxt_ptr_vec.push_back(&digits[1]);
      polyEvalNew(ctxt_ptr_vec, secondRowPolys, tmp);
    } else
      assertTrue(false, "extracting more than 2 digits is not supported");
  } else
    assertTrue(false, "not expecting non-power-of-p aux for now");
#endif
}

static void reduceOddPoly(NTL::ZZX& poly)
{
  long deg = NTL::deg(poly);
  for (long i = 0; i <= deg; i += 2)
    NTL::SetCoeff(poly, i, 0);
  poly.normalize();
}

void Context::buildBtsPolys()
{
  // precompute polynomials for bts
  if (!newBtsFlag) { // NOTE: tested ok
    long botHigh = e_param - ePrime_param;
    long r = getR();
    long p = getP();
    long topHigh = botHigh + r - 1;

    bool use_chen_han = false;
    if (r > 1) {
      double chen_han_cost = log(p - 1) + log(r);
      double basic_cost;
      if (p == 2 && r > 2 && botHigh + r > 2)
        basic_cost = (r - 1) * log(p);
      else
        basic_cost = r * log(p);

      // std::cerr << "*** basic: " << basic_cost << "\n";
      // std::cerr << "*** chen/han: " << chen_han_cost << "\n";

      double thresh = 1.5;
      if (p == 2)
        thresh = 1.75;
      // increasing thresh makes chen_han less likely to be chosen.
      // For p == 2, the basic algorithm is just squaring,
      // and so is a bit cheaper, so we raise thresh a bit.
      // This is all a bit heuristic.

      if (basic_cost > thresh * chen_han_cost)
        use_chen_han = true;
    }

    if (fhe_force_chen_han > 0)
      use_chen_han = true;
    else if (fhe_force_chen_han < 0)
      use_chen_han = false;
    ch18Flag = use_chen_han;
#ifdef HELIB_DEBUG
    std::cerr << "CH18 enabled? " << ch18Flag << '\n';
#endif
    // now compute the polynomials
    if (use_chen_han) {
      // ee and rr are the arguments of extendExtractDigits
      long rr = botHigh;
      long ee = r;
      debug_ee = ee;
      debug_rr = rr;
      if (p > 3)
        buildDigitPolynomial(liftPoly, p, rr);
      extractPolys.SetLength(rr);
      for (long i : range(rr)) {
        compute_magic_poly(extractPolys[i], p, ee + rr - i);
      }
    } else { // HS21
      if (p == 2 && r > 2 && topHigh + 1 > 2)
        topHigh--; // For p==2 we sometime get a bit for free
      long rr = topHigh + 1;
      debug_rr = rr;
      // NOTE: we assume ptxtSpace is p2r
      //  and ignore the effectiveR() stuff
      if (p > 3)
        buildDigitPolynomial(liftPoly, p, rr);
    }
  } else { // new bts
    long eNew = eNew_param;
    long p = getP();
    long r = getR();
    long t = getT();
    long aux = getAux();
    long bnd = ceil(boundForRecryption());

    if (t < 0) { // non-power-of-p aux
      extractPolys.SetLength(1);
      // Order selection: the order-four radix needs -1 to be a square, so for
      // p = 7 (mod 12) -- every Mersenne prime above 3 -- only the order-six
      // Eisenstein filter exists. HELIB_FILTER_ORDER overrides the choice.
      long a6 = 0;
      { const char* fo = getenv("HELIB_FILTER_ORDER");
        // Only deviate from the established path when the filter is switched on: the
        // baseline arm must build exactly the polynomial it always built.
        bool filterOn = envFlagEnabled("HELIB_AUX_ORDER4_EVAL");
        long want = fo ? atol(fo) : 4;
        if (filterOn && want == 6)
          a6 = compute_prime_aux_poly_order6(extractPolys[0], p, r, bnd, aux);
        if (filterOn && want == 6 && !a6)
          std::cout << "HELIB_ORDER6: unavailable at p=" << p
                    << "; falling back to the order-four path\n"; }
      if (!a6) compute_prime_aux_poly(extractPolys[0], p, r, bnd, aux);
      if (envFlagEnabled("HELIB_COMPOSED_EVAL"))
        buildComposedPlan(extractPolys[0], p, bnd, aux,
                          getOrdP(), getEA());
      std::cout << "deg of poly for non-power-of-p aux is " << NTL::deg(extractPolys[0]) << "\n";
    } else { // power-of-p aux
      if (numExtract_param == 1) {
        extractPolys.SetLength(1);
        compute_magic_poly(extractPolys[0], p, eNew);

        NTL::ZZX null_poly;
        // when we only need to extract a single digit,
        //  the null poly is modulo p^eNew
        compute_null_poly(null_poly, p, eNew, t, bnd, true);
        std::cout << "degs of poly for the first row and its null poly are " << NTL::deg(extractPolys[0])
          << " / " << NTL::deg(null_poly) << "\n";
        if (deg(null_poly) <= deg(extractPolys[0])) {
          // reduce w.r.t the null poly modulo p2eNew
          NTL::ZZ p2eNew = NTL::power(NTL::ZZ(p), eNew);
          NTL::ZZ_pPush push(p2eNew);
          NTL::ZZ_pX reduced = NTL::conv<NTL::ZZ_pX>(extractPolys[0]);
          NTL::ZZ_pX null_poly_p = NTL::conv<NTL::ZZ_pX>(null_poly);
          NTL::rem(reduced, reduced, null_poly_p);
          extractPolys[0] = NTL::conv<NTL::ZZX>(reduced);
        }
        reduceOddPoly(extractPolys[0]);
      } else if (numExtract_param == 2) {
        // buildDigitPolynomial(liftPoly, p, 2);
        compute_magic_poly(liftPoly, p, 2);
        extractPolys.SetLength(2);
        compute_magic_poly(extractPolys[0], p, eNew);
        compute_magic_poly(extractPolys[1], p, eNew - 1);

        NTL::ZZX lift_null_poly;
        // for the lift poly, null polynomial is computed modulo p^2
        compute_null_poly(lift_null_poly, p, 2, t, bnd, true);
        std::cout << "degs of the lift poly and its null poly are " << NTL::deg(liftPoly)
          << " / " << NTL::deg(lift_null_poly) << "\n";
        NTL::ZZ p2two = NTL::ZZ(p * p);
        if (deg(lift_null_poly) <= deg(liftPoly)) {
          NTL::ZZ_pPush push(p2two);
          NTL::ZZ_pX reduced = NTL::conv<NTL::ZZ_pX>(liftPoly);
          NTL::ZZ_pX null_poly_p = NTL::conv<NTL::ZZ_pX>(lift_null_poly);
          NTL::rem(reduced, reduced, null_poly_p);
          liftPoly = NTL::conv<NTL::ZZX>(reduced);
        }
        reduceOddPoly(liftPoly);
        PolyRed(liftPoly, p2two, false);

        NTL::ZZX null_polys[2];
        // for the first-row ext poly, compute null poly modulo p^eNew
        compute_null_poly(null_polys[0], p, eNew, t, bnd, true);
        // for the second-row ext poly, compute null poly modulo p^(eNew-1)
        compute_null_poly(null_polys[1], p, eNew - 1, t - 1, bnd, false);
        std::cout << "degs of the ext polys and their null polys are " <<
          NTL::deg(extractPolys[0]) << " / " << NTL::deg(null_polys[0]) << ", " <<
          NTL::deg(extractPolys[1]) << " / " << NTL::deg(null_polys[1]) << "\n";

        std::vector<long> p_pows = {eNew, eNew - 1};
        for (long i = 0; i < 2; i++) {
          if (NTL::deg(null_polys[i]) > NTL::deg(extractPolys[i]))
            continue;
          printf("reducing the ext poly for No.%ld row\n", i);
          NTL::ZZ curMod = NTL::power(NTL::ZZ(p), p_pows[i]);
          NTL::ZZ_pPush push(curMod);
          NTL::ZZ_pX reduced = NTL::conv<NTL::ZZ_pX>(extractPolys[i]);
          NTL::ZZ_pX null_poly_p = NTL::conv<NTL::ZZ_pX>(null_polys[i]);
          NTL::rem(reduced, reduced, null_poly_p);
          extractPolys[i] = NTL::conv<NTL::ZZX>(reduced);
        }
        reduceOddPoly(extractPolys[0]);
        reduceOddPoly(extractPolys[1]);
      } else // extraction more than 2 digits is not supported
        assertTrue(false, "something wrong");
    }
  }
}

} // namespace helib
