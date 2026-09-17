# Artifact: Symmetry-Graded Digit Extraction for Faster BGV/BFV Bootstrapping

Everything behind the evaluation section of the paper: the patch that turns vanilla HElib into
the composed `(r,d)` evaluator, the driver that measures it, the 22-ring sweep, the security
estimates, the raw logs, and the scripts that turn the logs into the tables.

```
README.md                  this file
VERIFICATION.md            the four measurement rules, and a worked case of one catching an error
selector/select.py         standalone (r,d) selector; --self-test replays the paper's rows
baselines/README.md        pinned commits and build recipes for the three prior implementations
ours/
  README.md                the two-layer patch, the build, how to run one arm
  apply_all.sh             vanilla HElib 3e337a6 -> layer 1 -> layer 2, byte-verified against src/
  patches/                 the two layers, as three .patch files
  src/                     extractDigits.cpp and recryption.cpp in full, post-patch
  fatboot-driver/          the thin-bootstrapping driver; presets i=3,4 are Ma et al.'s sets IV/V,
                           i=14..33 the new rings
  dev_history/             development patches and the vanilla extractDigits.cpp, for transparency
newexp/
  README.md                arms, environment variables, how to run a pass, what did not work
  PARAMETERS.md            how every ring, digit bound, radix, chain and security figure was derived
  sets.tsv sets128.tsv cases.tsv   the 22 parameter sets
  run_batch.sh arms.sh     the driver harness
  collect.py               logs/ -> results.csv
  make_final.py make_appendix_tables.py make_origin_figs.py parse_logs.py
  logs/                    unedited driver output of every run
  final/                   final_rows.json and the LaTeX tables and figures
  security/                estimate_security.py and its per-ring output
experiments/               census, obstruction, monodromy, density, shared-context scripts
results/raw_logs/          unedited stdout of the shared-context runs and of the prior artifacts
```

Absolute paths of the machine the runs were made on have been replaced throughout by the
placeholders `$ARTIFACT`, `$HELIB_SRC`, `$ORDER4_SRC`, `$ZHAO_SRC` and `$LATTICE_ESTIMATOR`, and
the timezone abbreviation in two copied logs by `TZ`. Nothing else in any log was edited.

## Start here

The selector is the only piece with no heavy dependencies. It answers the question the paper's
`Procedure SELECT` poses — given `(p, m, B)`, which order `r*` and which slot degree `d` give the
cheapest digit extraction — before any ciphertext exists, in under a second.

```bash
cd selector
pip install sympy
python3 select.py --self-test                                # replays every selector row; prints ALL PASS
python3 select.py --p 8191 --m 65536 --B 17 --support hex    # r*=6 at a Mersenne prime
```

Everything else needs HElib built with the patch in `ours/` (see `ours/README.md`), and the
baseline comparisons additionally need the three repositories pinned in `baselines/README.md`.

## Where each table comes from

Numbers refer to the current manuscript. Every file named here exists in this repository.

| Paper | What it is | Produced by | Raw data |
|---|---|---|---|
| Table 3 (`tab:params`) | the nine representative sets, with security | `newexp/security/estimate_security.py`; derivation in `newexp/PARAMETERS.md` | `newexp/security/est_*.json`, `newexp/logs/` |
| Table 4 (`tab:results`) | three evaluators on those nine sets | `newexp/collect.py` → `newexp/make_final.py` | `newexp/logs/set*_pass*.log` |
| Table 5 (`tab:comparison`) | prior implementations at set V | hand-assembled from the four sources at right | `newexp/logs/set4_p65537_pass1.log` (Ma, Xiong–Wang, ours), `results/raw_logs/build_and_run.log` and `ma_baseline_five_presets.log` (Zhao et al. vs Ma, set V) |
| Fig. 7 (`fig:results`) | stage breakdown, and set V against prior work | not reproduced by any script here (see note below) | `newexp/final/final_rows.json` |
| Table 9 (`tab:offline`) | per-ring offline data: radix, degrees, coset index, search time, chains, capacity | `newexp/make_appendix_tables.py` | `newexp/results.csv` |
| Table 10 (`tab:sec_full`) | six attacks on both LWE instances, every ring | `newexp/make_appendix_tables.py` | `newexp/security/est_*.json` |
| Table 11 (`tab:e2e`) | all 17 rings at `h=12` | `newexp/make_final.py` → `newexp/final/tables_final.tex` | `newexp/logs/` |
| Table 12 (`tab:po2`) | scalar axis on `m=2^16` | — | `results/raw_logs/sweep_po2_ma_sets.log` (2000 bits), `sweep_po2_deep.log` (the † rows, 3600 bits) |
| Table 13 (`tab:composed`) | composed evaluator against the scalar axis | — | `results/raw_logs/sweep_composed.log` (rows 1–3), `sweep_composed_4003.log` (row 4), `v_rerun_bsgs.log` (row 5) |
| Table 14 (`tab:e2e128`) | the five rings at `h=26` | `newexp/make_final.py` → `newexp/final/tables_final.tex` | `newexp/logs/set2*_h26_*.log`, `set3*_h26_*.log` |
| Table 15 (`tab:passes`) | the four rings measured twice | `newexp/make_appendix_tables.py` | `newexp/results.csv` |
| Table 6 (`tab:census`) | exhaustive census of the folded coset | `experiments/01_full_census_naive.cpp`, `02_full_census_fast.cpp`, `07_make_census_table.py` | `results/raw_logs/CENSUS*.txt` |
| Table 7 (`tab:monodromy`) | monodromy certificates H1–H4 | `experiments/05_monodromy_certificate.cpp` | `results/raw_logs/MONODROMY.txt` |
| Table 8 (`tab:select`) | `Select` output at `B=17` | `selector/select.py --self-test` | — |
| Lemma, obstruction at `r=2` | `gcd(Q, Gamma)` of degree `2B` | `experiments/04_obstruction_check.cpp` | — |

Three caveats on that table, none of which affect Tables 3, 4, 9, 10, 11, 14 or 15.

Fig. 7 of the manuscript uses `figs/fig6a_stacked.pdf` and `figs/fig6b_prior.pdf`; both come
from `newexp/make_fig6_v2.py`, which reads the stage timings straight out of `newexp/logs/`
and the speedups out of `final_rows.json`. `make_origin_figs.py` and `make_final.py` produce
the two earlier pairs, `fig6a_bars.pdf`/`fig6b_speedup.pdf` and
`fig_extract_time.pdf`/`fig_speedup_vs_d.pdf`, from the same data.

In Table 12, the multiplication count and the time in a row are each the minimum over the
Paterson–Stockmeyer parameter kappa, and on two rows they come from different kappa: at
`p=8191, r=2` the log has 43 mults at 49.92 s (kappa=20) and 44 mults at 48.95 s (kappa=26), and
at `p=8191, r=3` it has 37 mults at 38.50 s (kappa=16) and 39 mults at 37.60 s (kappa=12). The
four daggered counts (43, 59, 50, 68) are likewise kappa-minima from the 3600-bit rerun, because
those four arms crashed at 2000 bits with `Decrypting with too much noise`.

The last row of Table 13 (`p=65537`, `m=50731`) is a different kind of measurement from the other
four. The first four come from the stage-level harness, which reports its own multiplication
count and time per row; the last comes from a full recryption, `results/raw_logs/v_rerun_bsgs.log`,
where the times are the `extract` field (84.02 s order four, 36.64 s composed) and the counts are
HElib's own `multiplyBy` counter (`multiplyBy: 38.865 / 21` and `multiplyBy: 28.1643 / 16`). That
run predates the sweep and used a different build, which is why its times differ from the 92.72 s
and 41.41 s that Tables 4, 5 and 11 report for the same ring out of
`newexp/logs/set4_p65537_pass1.log`. There is also a stage-level run on that ring,
`results/raw_logs/sweep_aligned65537.log`, but it has no composed arm.

## Raw logs

`results/raw_logs/` holds the runs that are not part of the `newexp/` sweep.

| file | what it is |
|---|---|
| `build_and_run.log` | Zhao et al.'s artifact rebuilt and run at their presets `p=8191` and `p=65537`, thick bootstrapping |
| `zhao_repro_p17_p127_p257.log` | the same, at their remaining three presets `p=17`, `127`, `257` |
| `ma_baseline_five_presets.log` | Ma et al.'s baseline at all five of those presets, same session |
| `sweep_po2_ma_sets.log` | scalar axis on `m=2^16` at 2000 bits, `p=131071/8191/65537`, orders 6/3/2/1 and 4/2/1 |
| `sweep_po2_deep.log` | the four arms that exhausted the 2000-bit budget, rerun at 3600 bits |
| `sweep_composed.log`, `sweep_composed_4003.log` | composed evaluator against the scalar axis on the same contexts |
| `sweep_aligned65537.log` | order-4/2/1 scalar axis on `m=50731`, `p=65537` |
| `O6_backtoback.log`, `CASE4_clean.log`, `ORDER6_case4.log`, `O6_smoke.log` | Case IV back-to-back arms |
| `v_rerun_bsgs.log`, `VERIFY_pass2.log` | Case V arms, and the second verification pass |
| `zhao_thin24.log`, `zhao_t-1_probe.log` | Zhao et al.'s evaluator on the thin path, both aborts |
| `table_unified.log`, `table_fix.log` | earlier unified table runs, superseded by `newexp/` |
| `CENSUS*.txt`, `MONODROMY.txt` | census and monodromy certificate output |

The comparison with Zhao et al. quoted in Section 6 as `1.15x-2.37x` is the ratio of Ma et al.'s
digit-extraction time to theirs, preset by preset, and can be checked directly:

```bash
cd results/raw_logs
grep -h "time for linear1" ma_baseline_five_presets.log | sort -u     # 677.08 2542.73 1477.28 429.34 689.12
grep -h "time for linear1" build_and_run.log zhao_repro_p17_p127_p257.log | sort -u
```

which gives, in the order `p = 17, 127, 257, 8191, 65537`, extraction times of
677.08 / 2542.73 / 1477.28 / 429.34 / 689.12 s for Ma et al. against
549.10 / 1072.90 / 689.31 / 373.77 / 422.66 s for Zhao et al., so ratios of
1.23, 2.37, 2.14, 1.15 and 1.63. The 1.63 at `p=65537` is the figure in Table 5. These are
extraction-only ratios; on total bootstrapping time the same five runs give 1.23, 2.14, 1.83,
1.04 and 1.37.

## Correctness discipline

Every ciphertext number in the paper is subject to the four rules in `VERIFICATION.md`: the
evaluator under test must announce itself at *evaluation* time and every log is grep-checked for
that announcement before its numbers are used; every run ends with HElib's all-slot decryption
check and a failure is reported as a failure; cross-arm ratios are measured back to back in one
session with the untouched linear transform as a load reference; and the plaintext-constant cache
is treated as a measurement hazard. `VERIFICATION.md` walks through one case where the first rule
caught a wrong result before it reached the paper.

The machine-checked Lean 4 proofs of the algebraic core and of the noise model live in the
companion repository `symmetry-graded-lean`.
