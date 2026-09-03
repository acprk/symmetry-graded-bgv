#!/usr/bin/env python3
"""Add a `skipirr` diagnostic flag to bench_m15.

The relaxed norm criterion is a SUPERSET of irreducibility, so a scan in increasing c
always stops at the first irreducible F and the relaxed path never executes. To measure
whether the relaxed path costs anything on ciphertexts we need to force it, by rejecting
irreducible F outright. skipirr=1 does exactly that; it is a diagnostic switch, never a
mode one would deploy.
"""
p = "src/bench_m15.cpp"
s = open(p).read()

a = 'long relaxed = 1; // accept the exact norm criterion, not just irreducibility'
assert a in s
s = s.replace(a, a + '\n  long skipirr = 0; // diagnostic: REJECT irreducible F, exercising only the relaxed path', 1)

b = '.arg("relaxed", relaxed).parse(argc, argv);'
assert b in s
s = s.replace(b, '.arg("relaxed", relaxed).arg("skipirr", skipirr).parse(argc, argv);', 1)

c = '      if (NTL::DetIrredTest(F)) accept = true;\n      else if (relaxed) {'
assert c in s
s = s.replace(c, '      if (NTL::DetIrredTest(F)) { if (!skipirr) accept = true; }\n      else if (relaxed) {', 1)

open(p, "w").write(s)
print("skipirr added to", p)
