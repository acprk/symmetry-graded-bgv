#!/usr/bin/env python3
"""Fix the composed-branch evaluation inside the pipeline: Horner -> BSGS.

The first integration evaluated C by a sequential Horner chain in x^4, which costs degC
multiplications at multiplicative DEPTH degC (~17 levels). That inverted the capacity
story: the pipeline run showed the composed arm consuming 784 bits of capacity against
the baseline's 354, contradicting the standalone benchmark (394 vs 905) where BSGS was
used. Same multiplication count, wrong depth. This patch replaces Horner with the same
baby-step/giant-step evaluation the benchmarks use, operating on the slot-encoded
coefficients.
"""
F = "/home/luck/xzy/0424project/github_order4_cleaner/src/HElib_auxradix_opt/src/extractDigits.cpp"
s = open(F).read()
assert "HELIB_COMPOSED_EVAL" in s, "composed patch missing"
if "composedBsgsEnc" in s:
    print("already fixed"); raise SystemExit

# ---- helper: BSGS over encoded constants (mirrors bench_m13's bsgs) ----
helper = r'''
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
'''
anchor = "static Ctxt composedOrbitProduct(const Ctxt& A0, long d) {"
assert anchor in s
s = s.replace(anchor, helper + "\n" + anchor, 1)

# ---- replace the Horner chain with the BSGS call ----
old = """    Ctxt acc(x.getPubKey(), x.getPtxtSpace()); acc.clear();
    bool first = true;
    for (long i = (long)P.ck.size() - 1; i >= 0; i--) {   // Horner in x4
      if (!first) { acc.multiplyBy(x4); acc.reLinearize(); }
      Ctxt term(x.getPubKey(), x.getPtxtSpace());
      term.clear(); term.addConstant(P.ck[i]);
      acc += term; first = false;
    }
    Ctxt orb = composedOrbitProduct(acc, P.d);"""
new = """    Ctxt acc = composedBsgsEnc(x4, P.ck);   // BSGS: depth O(log degC), not degC
    Ctxt orb = composedOrbitProduct(acc, P.d);"""
assert old in s
s = s.replace(old, new, 1)
open(F, "w").write(s)
print("Horner -> BSGS fixed in", F)
