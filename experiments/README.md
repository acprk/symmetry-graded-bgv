# Experiment scripts, by paper table

Two kinds of script live here. Scripts `01`–`07` are **pure arithmetic**: they need a C++
compiler and NTL, or Python, but no HElib and no ciphertexts, because they check statements
about polynomials over `F_p` directly (the obstruction, the monodromy certificate, the exact
census of the folded coset). Scripts `10`–`14` are **real ciphertext experiments**: they
require the patched HElib of `../ours/` to be built first, and they follow the discipline of
`../VERIFICATION.md`.

## Pure arithmetic (no HElib needed)

| Script | Produces | Runtime |
|---|---|---|
| `01_full_census_naive.cpp` | Table 9, first (independent) implementation | ~10 min per row at `p=8191` |
| `02_full_census_fast.cpp` | Table 9, second implementation with an early-exit optimisation (agrees with `01` on every row; used to cross-check the `r=2` rows, which `01` alone would take hours on) | seconds to minutes |
| `03_census_predict.py` | The exact cycle-type prediction column of Table 9, `Pi_d(n') * p`, via the generating-function coefficient `[x^n'] prod (1+x^m)^{N(p,m)}` — no sampling, no Monte Carlo | instant |
| `04_obstruction_check.cpp` | Verifies `thm:obstruction`: `deg gcd(Q, Gamma) = B` for the odd filter, `= 0` for `r >= 3`, at the two primes used in the paper | seconds |
| `05_monodromy_certificate.cpp` | Table 11: checks hypotheses (H1)–(H4) of `thm:monodromy` (three gcds and one discriminant per row) for every pencil the paper actually uses | seconds |
| `06_density_validation.cpp` | Three-level density check (irreducible / norm-form / Zhao et al.'s stricter multi-factor criterion), with the padding construction of `sec:algo:eval` | seconds |
| `07_make_census_table.py` | Renders `01`/`02`'s raw output plus `03`'s predictions into Table 9's LaTeX | instant |

Build each `.cpp` with e.g. `g++ -O2 -std=c++17 05_monodromy_certificate.cpp -o mono -lntl -lgmp -pthread`.

```bash
g++ -O2 -std=c++17 02_full_census_fast.cpp -o census2 -lntl -lgmp -pthread
./census2 8191 91 17 1 "6,3,2" "2,7,14"     # p A B hexagon? r-list d-list
# compare against results/raw_logs/CENSUS_p8191.txt
```

## Real ciphertext experiments (need `../ours/` built)

| Script | Produces | Notes |
|---|---|---|
| `10_smoke_test_order6.sh` | A correctness smoke test of the order-six construction at a Mersenne prime, before trusting any timing from it | run this first |
| `11_table_po2_composed_backtoback.sh` | Tables 7 and 8: scalar axis alone vs. composed, back to back in one context per row | ~10–40 min per row |
| `12_table_e2e_case4_order6.sh` | Table 5, Case IV (`p=8191`): baseline / order-six / composed, back to back, two passes | ~1 hour |
| `13_table_e2e_case5_bsgsfix.sh` | Table 5, Case V (`p=65537`): baseline / order-four / composed with the BSGS-not-Horner fix (see `../VERIFICATION.md` rule 4 and `../ours/dev_history/patch_bsgs_fix.py` for why this matters), plus a same-session probe of the Zhao et al. artifact and a preliminary census pass | several hours (it is a queue of everything) |
| `14_table_e2e_case5_pass2.sh` | An independent second pass of Case V, used to compute the load-normalised, cross-pass-stable numbers actually quoted in the paper (§8, "Measurement discipline") | ~1 hour |

Each script sets `HELIB_ZZX_CACHE_DIR` per arm (see `../VERIFICATION.md` rule 4) and appends
`echo "exit=$? ($MODE)"` after every run so a truncated or crashed arm is visible in the log
rather than silently missing. Before trusting any number out of a log these scripts produce,
run the checks in `../VERIFICATION.md`.

Set `OURS_ROOT` and `ZHAO_ROOT` (default `./ours` and `./baselines/zhao2026`) if your checkout
does not match the layout in the top-level `README.md`.
