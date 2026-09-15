# Artifact: Symmetry-Graded Digit Extraction for Faster BGV/BFV Bootstrapping

This repository is the experimental artifact for the paper. It contains:

1. **`selector/`** — a standalone, dependency-light (r,d) selector (`select.py`). Given a
   plaintext prime `p`, a cyclotomic index `m`, and a digit bound `B`, it searches for and
   returns the cost-optimal symmetry-graded configuration `(r*, d)` *before any ciphertext
   is created*. This is the "advance-determination script" the paper's Section 7 documents
   as `Procedure SELECT`. It needs no HElib and runs in milliseconds.
2. **`baselines/`** — build recipes pinning the exact upstream commits of the three
   constructions this paper is measured against, so that the comparison is against the
   authors' own code, not our reimplementation of it.
3. **`ours/`** — the two-layer patch that turns vanilla HElib into the composed `(r,d)` evaluator
   (order-4, order-6, and the Galois-norm composition), plus the thin-bootstrapping driver
   used to measure it.
4. **`experiments/`** — the exact scripts used to produce every table in the paper's
   evaluation section, from the pure-arithmetic selector predictions (`tab:offline`) to the
   full-census exhaustive verification of the density theorem (`tab:census`).
5. **`newexp/`** — the extended sweep of Section 6 and Appendix D: 17 general cyclotomic rings at `h=12` and five at `h=26`, every arm on identical ring, chain, key and support, with the per-ring Lattice Estimator security, the raw logs and the scripts that produce every table and figure.
6. **`results/raw_logs/`** — the actual, unedited stdout logs from the runs that produced
   the numbers in the paper. Every number quoted in the tables can be grepped out of these
   files; nothing here is a summary or a simulation.

## Correspondence between paper tables and this repository

Numbering refers to the current manuscript (Section 6 and Appendices C, D).

| Paper table / figure | What it measures | Where it comes from |
|---|---|---|
| Table 3 (`tab:results`), Fig. 7 | Six representative rings: parameters, security, three evaluators end to end | `newexp/final/final_rows.json`, `newexp/make_origin_figs.py`; raw logs `newexp/logs/set*_pass*.log` |
| Table 4 (`tab:comparison`) | Prior implementations at Ma et al.'s set V | `newexp/logs/` (Ma / Xiong–Wang / ours), `results/raw_logs/zhao_thin24.log`, `build_and_run.log` (Zhao et al.'s artifact), `baselines/README.md` |
| App. D, `tab:offline` | Selector output per ring: radix, degrees, coset index, search time, chains, capacity | `newexp/collect.py`, `newexp/make_final.py` → `newexp/final/tab_offline.tex` |
| App. D, `tab:sec_full` | Lattice Estimator, six attacks, main and encapsulated key, every ring | `newexp/security/estimate_security.py`, `newexp/security/est_h*_slice*.json` |
| App. D, `tab:e2e`, `tab:e2e128` | All 17 rings at h=12 and 5 rings at h=26 | `newexp/final/tables_final.tex` |
| App. D, `tab:po2`, `tab:composed` | Scalar axis and composed evaluator on shared contexts | `experiments/11_table_po2_composed_backtoback.sh`, `results/raw_logs/O6_backtoback.log` |
| App. D, `tab:passes` | Reproducibility across two passes | `newexp/final/tab_passes.tex` |
| App. C, `tab:census` | Exhaustive census of the folded coset (obstruction + density) | `experiments/01_full_census_naive.cpp` / `02_full_census_fast.cpp`, `07_make_census_table.py` |
| App. C, monodromy certificate | Hypotheses H1–H4 for the composed pencil | `experiments/05_monodromy_certificate.cpp` |
| Lemma "obstruction at r = 2" | `gcd(Q, Γ)` of degree 2B for the unfiltered polynomial | `experiments/04_obstruction_check.cpp` |
| Selector `Select` | Cost-optimal `(r*, d)` before any ciphertext exists | `selector/select.py` |

The machine-checked Lean 4 proofs of the algebraic core and of the noise model live in the
companion repository `symmetry-graded-lean`.

## Quick start

```bash
# 1. The selector needs nothing but Python + sympy. Try it now:
cd selector
pip install sympy
python3 select.py --self-test               # replays every selector row in the paper
python3 select.py --p 8191 --m 65536 --B 17 --support hex   # predicts r*=6 for a Mersenne prime

# 2. Everything downstream of step 1 needs HElib built with our patch (see ours/README.md)
#    and, for the baseline comparisons, the three repositories in baselines/ (see below).
```

## Correctness discipline

Every number in the paper that comes from a ciphertext experiment is subject to the
verification discipline documented in `VERIFICATION.md`: (i) the evaluator under test must
announce itself *at evaluation time*, not merely when a plan is built, and every log in
`results/raw_logs/` is `grep`-checked for that announcement before its numbers are trusted;
(ii) every bootstrapping run ends with HElib's own all-slot decryption check, and a run
that fails it is reported as a failure, never silently dropped; (iii) ratios that must be
compared across arms are always measured back-to-back in one session on one machine, with
the accompanying (unmodified) linear-transform time recorded as a load barometer.
`VERIFICATION.md` walks through one complete example end to end.

## Repository layout

```
.
├── README.md                  (this file)
├── VERIFICATION.md            (measurement discipline, with a worked example)
├── selector/select.py         (standalone (r,d) selector; --self-test replays the paper's rows)
├── baselines/README.md        (pinned commits + build recipes for Ma'24, Xiong–Wang'26, Zhao'26, Geelen'23)
├── ours/
│   ├── README.md              (two-layer patch structure, build, how to run one arm)
│   ├── apply_all.sh           (vanilla HElib 3e337a6 → layer 1 → layer 2, byte-verified against src/)
│   ├── patches/               (layer1_infrastructure, layer2_order456_composed_extractDigits, layer2_explicit_aux_recryption)
│   ├── src/                   (extractDigits.cpp, recryption.cpp in full)
│   ├── fatboot-driver/        (thin-bootstrapping driver `fatboot`, presets 3/4 = Ma et al.'s sets IV/V, 14–33 = new rings)
│   └── dev_history/           (incremental development patches and the legacy single patch, for transparency)
├── newexp/                    (the extended sweep behind Section 6 and Appendix D)
│   ├── README.md              (arms, environment variables, parameter sets)
│   ├── sets.tsv, sets128.tsv, cases.tsv   (rings at h=12, h=26, and Ma et al.'s sets)
│   ├── run_batch*.sh, run_pool.sh, arms.sh (drivers; set ARTIFACT to this directory's parent if not auto-detected)
│   ├── collect.py, make_final.py, make_origin_figs.py (log parsing, pass selection, tables and figures)
│   ├── logs/                  (unedited driver output of every run)
│   ├── final/                 (final_rows.json and every LaTeX table and figure in the paper)
│   └── security/              (estimate_security.py and the estimator output per ring; needs LATTICE_ESTIMATOR=<checkout>)
├── experiments/               (census, obstruction, monodromy, density, shared-context scripts)
└── results/raw_logs/          (unedited stdout of the shared-context and Zhao-artifact runs)
```

Absolute paths of the machine the runs were made on have been replaced by the
placeholders `$ARTIFACT`, `$HELIB_SRC`, `$ORDER4_SRC`, `$ZHAO_SRC`, `$LATTICE_ESTIMATOR`
in scripts and logs; nothing else in the logs was edited.
