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
3. **`ours/`** — the patch that turns vanilla HElib into the composed `(r,d)` evaluator
   (order-4, order-6, and the Galois-norm composition), plus the thin-bootstrapping driver
   used to measure it.
4. **`experiments/`** — the exact scripts used to produce every table in the paper's
   evaluation section, from the pure-arithmetic selector predictions (Table 6) to the
   full-census exhaustive verification of the density theorem (Table 9).
5. **`results/raw_logs/`** — the actual, unedited stdout logs from the runs that produced
   the numbers in the paper. Every number quoted in the tables can be grepped out of these
   files; nothing here is a summary or a simulation.

## Correspondence between paper tables and this repository

| Paper table | What it measures | Where it comes from |
|---|---|---|
| Table 1 (`tab:related_compare`) | Asymptotic comparison, prior work vs. this work | prose / literature, no script |
| Table 3 (`tab:rho`) | Effective order ρ per admissible scalar order and region | `selector/select.py` (the `rho` column) |
| Table 4 (`tab:plan`) | Selector predictions on the state of the art's own sets, *no ciphertext* | `selector/select.py`, `--self-test` |
| Table 12 (`tab:select`) | Selector predictions on 8 parameter sets | `selector/select.py`, `--self-test` |
| Table 5 (`tab:e2e`) | End-to-end thin bootstrapping, 3 baselines + ours | `experiments/12_..._case4_order6.sh`, `13_..._case5_bsgsfix.sh`, `14_..._case5_pass2.sh` |
| Table 6 (`tab:capacity`) | Depth/capacity, our format vs. Zhao et al.'s | `results/raw_logs/table_unified.log`, `table_fix.log` |
| Table 7 (`tab:po2`) | Scalar axis on power-of-two rings, real ciphertexts | `experiments/11_table_po2_composed_backtoback.sh` |
| Table 8 (`tab:composed`) | Composed `(r,d)` evaluator vs. scalar axis alone | `experiments/11_table_po2_composed_backtoback.sh` |
| Table 9 (`tab:census`) | Exhaustive census of the folded coset (obstruction + density) | `experiments/01_full_census_naive.cpp` / `02_full_census_fast.cpp` |
| Table 10 (`tab:rscan`) | Exhaustive scan of scalar orders r=1..32 | `selector/select.py --rmax 32` (see `baselines/README.md` note) |
| Table 11 (`tab:monodromy`) | Monodromy certificate (H1–H4) for the composed pencil | `experiments/05_monodromy_certificate.cpp` |
| Theorem "Obstruction for the odd filter" | `gcd(Q,Γ)` computation | `experiments/04_obstruction_check.cpp` |
| Reproduction of Zhao et al.'s own artifact (Discussion, §8) | Their own configuration, thick bootstrapping | `results/raw_logs/build_and_run.log`, `zhao_thin24.log` |

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
artifact/
├── README.md                  (this file)
├── VERIFICATION.md            (measurement discipline, with a worked example)
├── selector/
│   └── select.py              (standalone (r,d) selector; --self-test replays paper tables)
├── baselines/
│   └── README.md              (pinned commits + build recipes for Ma'24, Zhao'26, Geelen'23)
├── ours/
│   ├── README.md              (how to build the patched HElib and the fatboot driver)
│   ├── patches/
│   │   ├── order4_order6_composed.patch      (unified diff, vanilla HElib -> ours)
│   │   └── extractDigits.vanilla-3e337a6.cpp (the base file the patch is against)
│   ├── src/extractDigits.cpp  (the patched file in full, for readability)
│   ├── fatboot-driver/        (thin-bootstrapping test driver + its own patch)
│   └── dev_history/           (the incremental patches applied during development, for
│                                transparency; the single unified patch above is what a
│                                fresh build should apply)
├── experiments/
│   ├── 01-02_full_census_*.cpp        (Table 9, two independent implementations)
│   ├── 03_census_predict.py            (exact cycle-type prediction, no sampling)
│   ├── 04_obstruction_check.cpp        (gcd(Q,Gamma) obstruction theorem check)
│   ├── 05_monodromy_certificate.cpp    (Table 10, hypotheses H1-H4)
│   ├── 06_density_validation.cpp       (3-level density: IRR/NORM/ZHAO, with padding)
│   ├── 07_make_census_table.py         (renders Table 9 from the .cpp output)
│   └── 10-14_table_*.sh                (Tables 4/7/8, real ciphertext runs)
└── results/raw_logs/           (unedited stdout of every run cited above)
```
