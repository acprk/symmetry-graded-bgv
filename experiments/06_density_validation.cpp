// Density of irreducible F_c = Q + c*G among c in F_p^*, as a function of the scalar
// filter order r. Plaintext only: no HElib context, no ciphertexts.
//
// Q is the folded interpolant of the low-digit map on the order-r support, G the
// vanishing polynomial of the folded support. Since G vanishes there, F_c computes the
// same function as Q for every c; Okada/Zhao need one c making F_c irreducible, so that
// F_c becomes a norm form and the Galois orbit product applies. This measures how often
// that succeeds, as a function of r.
//
// build: g++ -O2 -std=c++17 normdens.cpp -o normdens -lntl -lgmp -pthread
// run:   ./normdens p A B hexagon cmax
#include <NTL/ZZ_pX.h>
#include <NTL/ZZ_pXFactoring.h>
#include <NTL/vec_vec_ZZ_p.h>
#include <cstdio>
#include <cstdlib>
#include <map>
#include <vector>
using namespace NTL;
using namespace std;

int main(int argc, char** argv) {
  if (argc < 6) { printf("usage: normdens p A B hexagon cmax\n"); return 1; }
  long p = atol(argv[1]), A = atol(argv[2]), B = atol(argv[3]);
  long hexagon = atol(argv[4]), cmax = atol(argv[5]);
  long dslot = (argc > 6) ? atol(argv[6]) : 0;   // slot degree d
  ZZ_p::init(conv<ZZ>(p));
  printf("p=%ld A=%ld B=%ld support=%s  scanning c=1..%ld\n",
         p, A, B, hexagon ? "hexagon" : "box", cmax);
  printf("d = %ld\n", dslot);
  printf("%4s %7s %7s | %6s %9s | %6s %9s | %6s %9s | %9s %9s\n",
         "r","n'","degQ","IRR","dens","NORM","dens","ZHAO","dens","1/n","1/d");
  long rs[3] = {2, 3, 6};
  for (int ri = 0; ri < 3; ri++) {
    long r = rs[ri];
    map<long,long> low;
    bool ok = true;
    for (long e = -B; e <= B && ok; e++)
      for (long l = -B; l <= B && ok; l++) {
        if (hexagon && labs(e + l) > B) continue;
        long x = ((((e % p) * (A % p)) % p + (l % p)) % p + p) % p;
        long lv = ((l % p) + p) % p;
        map<long,long>::iterator it = low.find(x);
        if (it != low.end() && it->second != lv) ok = false; else low[x] = lv;
      }
    if (!ok) { printf("%4ld   radix not B-injective\n", r); continue; }
    long A2 = MulMod(A % p, A % p, p), den = ((1 - A2) % p + p) % p;
    long c1 = (r >= 3 && den != 0) ? InvMod(den, p) : 0, u = r - 1;
    map<long,long> qv;
    for (map<long,long>::iterator kv = low.begin(); kv != low.end(); ++kv) {
      long x = kv->first, lv = kv->second; if (!x) continue;
      long y = PowerMod(x, r, p);
      long t = SubMod(lv, MulMod(x, c1, p), p);
      long v = MulMod(t, InvMod(PowerMod(x, u, p), p), p);
      map<long,long>::iterator jt = qv.find(y);
      if (jt != qv.end() && jt->second != v) { ok = false; break; }
      qv[y] = v;
    }
    if (!ok) { printf("%4ld   order-%ld structure does not close\n", r, r); continue; }
    long n = (long)qv.size();
    vec_ZZ_p xs, ys; xs.SetLength(n); ys.SetLength(n);
    long i = 0;
    for (map<long,long>::iterator kv = qv.begin(); kv != qv.end(); ++kv) {
      xs[i] = conv<ZZ_p>(kv->first); ys[i] = conv<ZZ_p>(kv->second); i++; }
    ZZ_pX Q = interpolate(xs, ys);
    // PAD the vanishing set with points off the support until its degree is a multiple
    // of d. G must vanish on the support; its degree beyond that is free, and the orbit
    // product needs d | deg F. Without this, d | n fails generically and NO c can work.
    long ntar = dslot ? ((n + dslot - 1) / dslot) * dslot : n;
    if (ntar <= (long)deg(Q)) ntar += dslot;
    vec_ZZ_p roots; roots.SetLength(ntar);
    { map<long,long> used;
      long i2 = 0;
      for (map<long,long>::iterator kv = qv.begin(); kv != qv.end(); ++kv) {
        roots[i2++] = conv<ZZ_p>(kv->first); used[kv->first] = 1; }
      long z = 0;
      while (i2 < ntar) { while (used.count(z)) z++;
                          roots[i2++] = conv<ZZ_p>(z); used[z] = 1; z++; } }
    ZZ_pX G; BuildFromRoots(G, roots);
    // Three targets, in increasing order of permissiveness:
    //  IRR  : F irreducible  (what a naive reading of Okada/Zhao suggests)
    //  NORM : F squarefree and EVERY irreducible factor has degree divisible by d
    //         -- this is the exact condition for F to be a norm from GR(p^e,d)[t],
    //         and irreducibility is only its single-factor special case
    //  ZHAO : F has exactly k = floor(deg/d) distinct irreducible factors of degree d
    //         (their TargetDecomp, Definition 1)
    long irr = 0, nrm = 0, zha = 0, tried = 0;
    long dd = dslot, kk = deg(G) / (dslot ? dslot : 1);
    for (long c = 1; c <= cmax; c++) {
      ZZ_pX F = Q + conv<ZZ_p>(c) * G;
      if (deg(F) != deg(G)) continue;
      MakeMonic(F); tried++;
      if (DetIrredTest(F)) { irr++; if (dd && deg(F) % dd == 0) { nrm++; } continue; }
      if (!dd) continue;
      ZZ_pX gg = GCD(F, diff(F));
      if (deg(gg) != 0) continue;                    // not squarefree
      vec_pair_ZZ_pX_long fac; CanZass(fac, F);
      bool allDiv = true; long cntd = 0;
      for (long i = 0; i < fac.length(); i++) {
        if (deg(fac[i].a) % dd != 0) { allDiv = false; break; }
        if (deg(fac[i].a) == dd) cntd += fac[i].b;
      }
      if (allDiv) nrm++;
      if (cntd == kk) zha++;
    }
    printf("%4ld %7ld %7ld | %6ld %9.5f | %6ld %9.5f | %6ld %9.5f | %9.5f %9.5f\n",
           r, ntar, (long)deg(Q), irr, tried ? (double)irr/tried : 0.0,
           nrm, tried ? (double)nrm/tried : 0.0,
           zha, tried ? (double)zha/tried : 0.0,
           1.0/(double)deg(G), dd ? 1.0/(double)dd : 0.0);
    fflush(stdout);
  }
  return 0;
}
