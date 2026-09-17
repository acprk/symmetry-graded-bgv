# Experiment scripts, by paper table

Three kinds of script live here. Scripts `01`–`07` are **pure arithmetic**: they need a C++
compiler and NTL, or Python, but no HElib and no ciphertexts, because they check statements
about polynomials over `F_p` directly (the obstruction, the monodromy certificate, the exact
census of the folded coset). Scripts `10`–`14` are **end-to-end ciphertext experiments**: they
require the patched HElib of `../ours/` to be built first, and they follow the discipline of
`../VERIFICATION.md`. `bench/` is the **stage-level harness** behind Tables 12 and 13: it links
against vanilla HElib and times the digit-extraction polynomial on its own, outside a
recryption, which is what lets those two tables report a multiplication count per
Paterson–Stockmeyer parameter `kappa`.

## Pure arithmetic (no HElib needed)

| Script | Produces | Runtime |
|---|---|---|
| `01_full_census_naive.cpp` | Table 6 (`tab:census`), first (independent) implementation | ~10 min per row at `p=8191` |
| `02_full_census_fast.cpp` | Table 6, second implementation with an early-exit optimisation (agrees with `01` on every row; used to cross-check the `r=2` rows, which `01` alone would take hours on) | seconds to minutes |
| `03_census_predict.py` | The exact cycle-type prediction column of Table 6, `Pi_d(n') * p`, via the generating-function coefficient `[x^n'] prod (1+x^m)^{N(p,m)}` — no sampling, no Monte Carlo | instant |
| `04_obstruction_check.cpp` | Verifies `thm:obstruction`: `deg gcd(Q, Gamma) = B` for the odd filter, `= 0` for `r >= 3`, at the two primes used in the paper | seconds |
| `05_monodromy_certificate.cpp` | Table 7 (`tab:monodromy`): checks hypotheses (H1)–(H4) of `thm:monodromy` (three gcds and one discriminant per row) for every pencil the paper actually uses | seconds |
| `06_density_validation.cpp` | Three-level density check (irreducible / norm-form / Zhao et al.'s stricter multi-factor criterion), with the padding construction of `sec:algo:eval`. This is the `normdens` tool that `13_table_e2e_case5_bsgsfix.sh` invokes: `./normdens p A B hexagon cmax [d]` | seconds |
| `07_make_census_table.py` | Renders `01`/`02`'s raw output plus `03`'s predictions into Table 6's LaTeX | instant |

Build each `.cpp` with e.g. `g++ -O2 -std=c++17 05_monodromy_certificate.cpp -o mono -lntl -lgmp -pthread`.

```bash
g++ -O2 -std=c++17 02_full_census_fast.cpp -o census2 -lntl -lgmp -pthread
./census2 8191 91 17 1 "6,3,2" "2,7,14"     # p A B hexagon? r-list d-list
# compare against results/raw_logs/CENSUS_p8191.txt
```

## Stage-level harness, Tables 12 and 13 (needs vanilla HElib, not `../ours/`)

`bench/` holds `bench_m12.cpp` … `bench_m15.cpp`, the harness that produced the
`sweep_po2_*.log` and `sweep_composed*.log` files in `../results/raw_logs/`, together with one
runner script per log and its own `CMakeLists.txt`. `bench/README.md` says which generation
produced which log, how to read the `RESULT` / `ORBIT` rows, and what every command-line
argument means. In short:

| Runner | Produces | Binary |
|---|---|---|
| `bench/run_po2.sh` | Table 12 (`tab:po2`), the 2000-bit rows | `bench_m13` |
| `bench/run_po2_deep.sh` | Table 12, the four daggered rows (3600-bit rerun) | `bench_m14` |
| `bench/run_composed.sh` | Table 13 (`tab:composed`), rows 1–3 | `bench_m14` |
| `bench/run_composed_4003.sh` | Table 13, row 4 | `bench_m14` |
| `bench/run_aligned65537.sh` | the aligned-ring run quoted in Sec. 6 | `bench_m12` |

Table 13's fifth row is not from this harness: it is a full recryption produced by
`13_table_e2e_case5_bsgsfix.sh` below. See the top-level `README.md`.

## End-to-end ciphertext experiments (need `../ours/` built)

| Script | Produces | Notes |
|---|---|---|
| `10_smoke_test_order6.sh` | A correctness smoke test of the order-six construction at a Mersenne prime, before trusting any timing from it | run this first |
| `11_table_po2_composed_backtoback.sh` | `../results/raw_logs/O6_backtoback.log`: the Case IV ring (`p=8191`) run end to end as BASELINE / ORDER6 / ORDER6_COMPOSED, two passes, one context per arm. It is the back-to-back cross-check behind the Case IV ratio, **not** the source of Tables 12 and 13 — those are `bench/` above | ~10–40 min per arm |
| `12_table_e2e_case4_order6.sh` | The Case IV row (`p=8191`) of Tables 4 and 11: baseline / order-six / composed, back to back, two passes | ~1 hour |
| `13_table_e2e_case5_bsgsfix.sh` | The Case V row (`p=65537`) of Tables 4, 5 and 11: baseline / order-four / composed with the BSGS-not-Horner fix (see `../VERIFICATION.md` rule 4 and `../ours/dev_history/patch_bsgs_fix.py` for why this matters), plus a same-session probe of the Zhao et al. artifact and a preliminary census pass | several hours (it is a queue of everything) |
| `14_table_e2e_case5_pass2.sh` | An independent second pass of Case V, used to compute the load-normalised, cross-pass-stable numbers actually quoted in the paper (Appendix D, "Reproducibility and capacity") | ~1 hour |

Each script sets `HELIB_ZZX_CACHE_DIR` per arm (see `../VERIFICATION.md` rule 4) and appends
`echo "exit=$? ($MODE)"` after every run so a truncated or crashed arm is visible in the log
rather than silently missing. Before trusting any number out of a log these scripts produce,
run the checks in `../VERIFICATION.md`.

Set `OURS_ROOT` and `ZHAO_ROOT` if your checkout does not match the layout in the top-level
`README.md`; the defaults are `../ours` and `../baselines/_upstream/artifact-helib`, the latter
being where `../baselines/setup.sh` clones Zhao et al.'s artifact. `OURS_ROOT` is the root of
the patched HElib tree, so the driver is looked for at
`$OURS_ROOT/fatboot-driver/build/fatboot`, which is where `../ours/README.md`'s build puts it;
set `FATBOOT` to a full path if you built it somewhere else. All five scripts resolve their
paths from their own location, so they can be run from any working directory, and all five
refuse to start with a one-line message rather than failing mid-queue if the driver is missing.
`13_table_e2e_case5_bsgsfix.sh` additionally skips — with a message, not an error — the Zhao et
al. probe if that artifact is not built, and builds `normdens` from `06_density_validation.cpp`
itself (set `CXX` if your default compiler's ABI does not match your NTL).

These five scripts predate the `newexp/` sweep and write into their own logs; the end-to-end
numbers in the paper now come from `newexp/`, which runs the same arms over 22 rings rather than
two.
