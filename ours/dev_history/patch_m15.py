#!/usr/bin/env python3
"""bench_m15 = bench_m14 + the RELAXED norm criterion.

bench_m14 accepts c only when F_c = Q + c*Gamma is irreducible. That is sufficient but
not necessary: F is a norm from GR(p^e,d)[t] exactly when F is squarefree and every
irreducible factor has degree divisible by d. Irreducibility is the single-factor case.

Under the relaxed criterion we build C by taking ONE factor from each F_p-irreducible
factor's Frobenius orbit and multiplying them; Orb_d is multiplicative, so Orb_d(C) = F
still holds and deg C = deg F / d is unchanged. The point of this build is to check on
ciphertexts that the relaxation costs nothing.
"""
src = open("src/bench_m14.cpp").read()

old = '''      NTL::MakeMonic(F);
      if (NTL::DetIrredTest(F)) { cfound = c;
        NTL::ZZ_pX Gslot; NTL::conv(Gslot, ea.getAlMod().getFactorsOverZZ()[0]);
        NTL::ZZ_pEPush push2(Gslot);
        NTL::ZZ_pEX Fe = NTL::conv<NTL::ZZ_pEX>(F);
        NTL::vec_pair_ZZ_pEX_long fac; NTL::CanZass(fac, Fe);
        long k = NTL::deg(fac[0].a);
        printf("norm-form: c=%ld found in %.2fs, deg F=%ld -> %ld factors of degree %ld"
               " (want %ld x %ld)\\n", c, now_s() - ts, ntar, (long)fac.length(), k, d, ntar / d);
        if (k != ntar / d || fac.length() != d) { printf("norm-form: unexpected split, skipping orbit arm\\n"); break; }
        NTL::ZZ_pEX C = fac[0].a;'''

new = '''      NTL::MakeMonic(F);
      // --- norm criterion ---
      // strict (relaxed=0): F irreducible.
      // relaxed(relaxed=1): F squarefree and every irreducible factor of F over F_p has
      //   degree divisible by d. This is the EXACT condition for F to be a norm from
      //   GR(p^e,d)[t]; irreducibility is only the single-factor special case. Orb_d is
      //   multiplicative, so taking one factor per Frobenius orbit and multiplying them
      //   gives a C of the SAME degree deg F / d, hence the same evaluation cost.
      bool accept = false;
      NTL::vec_pair_ZZ_pX_long facp;
      if (NTL::DetIrredTest(F)) accept = true;
      else if (relaxed) {
        NTL::ZZ_pX gg = NTL::GCD(F, NTL::diff(F));
        if (NTL::deg(gg) == 0) {                      // squarefree
          NTL::CanZass(facp, F);
          accept = true;
          for (long i = 0; i < facp.length(); i++)
            if (facp[i].b != 1 || NTL::deg(facp[i].a) % d != 0) { accept = false; break; }
        }
      }
      if (accept) { cfound = c;
        NTL::ZZ_pX Gslot; NTL::conv(Gslot, ea.getAlMod().getFactorsOverZZ()[0]);
        NTL::ZZ_pEPush push2(Gslot);
        NTL::ZZ_pEX C;
        long k = 0, nfac = 0;
        if (facp.length() <= 1) {                     // strict path: F itself irreducible
          NTL::ZZ_pEX Fe = NTL::conv<NTL::ZZ_pEX>(F);
          NTL::vec_pair_ZZ_pEX_long fac; NTL::CanZass(fac, Fe);
          k = NTL::deg(fac[0].a); nfac = fac.length();
          if (k != ntar / d || nfac != d) { printf("norm-form: unexpected split, skipping\\n"); break; }
          C = fac[0].a;
        } else {                                      // relaxed path: one factor per orbit
          NTL::set(C);
          for (long i = 0; i < facp.length(); i++) {
            NTL::ZZ_pEX hje = NTL::conv<NTL::ZZ_pEX>(facp[i].a);
            NTL::vec_pair_ZZ_pEX_long fj; NTL::CanZass(fj, hje);
            if (fj.length() != d) { printf("norm-form: factor %ld did not split into d\\n", i); C = NTL::ZZ_pEX(); break; }
            C *= fj[0].a;
          }
          if (NTL::deg(C) != ntar / d) { printf("norm-form: relaxed C has wrong degree\\n"); break; }
          k = NTL::deg(C); nfac = facp.length();
        }
        printf("norm-form: c=%ld found in %.2fs, deg F=%ld, %s, %ld F_p-factor(s),"
               " deg C=%ld (want %ld)\\n", c, now_s() - ts, ntar,
               facp.length() <= 1 ? "IRREDUCIBLE" : "RELAXED(all factor degs divisible by d)",
               facp.length() <= 1 ? 1L : (long)facp.length(), (long)NTL::deg(C), ntar / d);'''

assert old in src, "anchor not found"
src = src.replace(old, new, 1)

# the old code continued with the coefficient encoding; keep it, but k is now set above
src = src.replace('''        sgnF = ((k * d) % 2 == 0) ? 1 : -1;''',
                  '''        sgnF = ((ntar) % 2 == 0) ? 1 : -1;''', 1)

# new flag
src = src.replace('long orbit = 1;   // also run the composed (r,d) arm when d >= 2',
 'long orbit = 1;   // also run the composed (r,d) arm when d >= 2\n  long relaxed = 1; // accept the exact norm criterion, not just irreducibility')
src = src.replace('.arg("orbit", orbit).parse(argc, argv);',
                  '.arg("orbit", orbit).arg("relaxed", relaxed).parse(argc, argv);', 1)
src = src.replace('printf("=== m14 done ===\\n");', 'printf("=== m15 done ===\\n");', 1)

open("src/bench_m15.cpp", "w").write(src)
print("bench_m15.cpp written:", len(src), "bytes")

cm = open("CMakeLists.txt").read()
if "bench_m15" not in cm:
    cm += "\nadd_executable(bench_m15 src/bench_m15.cpp)\ntarget_link_libraries(bench_m15 helib)\n"
    open("CMakeLists.txt", "w").write(cm)
    print("CMakeLists patched")
