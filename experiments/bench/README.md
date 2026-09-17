# The stage-level multiplication-count harness (Tables 12 and 13)

Tables 12 (`tab:po2`) and 13 (`tab:composed`) are **stage-level** measurements: they time and
count the digit-extraction polynomial on its own, on a freshly built context, rather than
measuring it inside a full recryption the way `newexp/` does. That is what lets them report a
multiplication count per Paterson–Stockmeyer parameter `kappa`, and what lets a scalar arm and a
composed arm of the same row share one context, one modulus chain and one key.

These binaries link against **vanilla HElib**. They are not the patched evaluator of `../../ours/`
— they build the filter polynomial and evaluate it directly, so they test the same mathematics
through an independent implementation. Every configuration ends with a decryption check against
the true low digit, and a row is only meaningful if it says `CORRECT`.

## What each generation is, and which log it produced

| source | adds | log it produced | paper |
|---|---|---|---|
| `bench_m12.cpp` | box (order-4 radix) and hexagon (order-6) supports, scalar axis | `sweep_aligned65537.log` | quoted in Sec. 6 |
| `bench_m13.cpp` | the orbit-closed box `sup=boxcl` | `sweep_po2_ma_sets.log` | Table 12, 2000-bit rows |
| `bench_m14.cpp` | the composed `(r,d)` arm (`ORBIT` rows) | `sweep_composed.log`, `sweep_composed_4003.log`, `sweep_po2_deep.log` | Table 13 rows 1–4; Table 12 daggered rows |
| `bench_m15.cpp` | the relaxed norm criterion (`relaxed=`, `skipirr=`) | — | no table; appendix discussion only |

The logs all live in `../../results/raw_logs/`.

## Reading a log

```
RESULT r=6 degEval=152 |S|=919
RESULT  kappa    time_s   mults  cap_used verify
RESULT     10    28.134      29       826 CORRECT
ORBIT      10    19.336      22       580 CORRECT  autos=1
```

`RESULT` rows are the scalar axis; `ORBIT` rows are the composed `(r,d)` evaluator, in the same
context and at the same `kappa` as the `RESULT` row above them. `mults` counts non-scalar
ciphertext multiplications (`multiplyBy` and `square`, counted in `mulCt`/`sqCt`), `cap_used` is
the capacity in bits the arm consumed, and `autos` on an `ORBIT` row is the number of Frobenius
automorphisms, which are free on ciphertexts. A table entry is the minimum over the `kappa` values
the run was given; in two rows of Table 12 the minimising `kappa` for `mults` and for `time_s`
differ, which the top-level `README.md` spells out.

## Build

```bash
cd experiments/bench
mkdir build && cd build
cmake -Dhelib_DIR=/path/to/helib/share/cmake/helib ..
make -j"$(nproc)"
```

`helib_DIR` is whatever HElib install you have; if you already built the patched HElib for
`../../ours/`, `<that build>/../_install/share/cmake/helib` works too — the patch does not change
anything these harnesses call. The measurements were taken with GCC 9.5.0 and NTL 11.5.1.

## Run

Each runner reproduces exactly one log. They take no arguments; three environment variables
adjust them to your machine:

| variable | default | meaning |
|---|---|---|
| `BENCH_BUILD` | `./build` | directory holding the compiled `bench_m*` binaries |
| `LOGDIR` | `./logs` | where the log is written |
| `THREADS` | `32` (`24` for `run_composed_4003.sh`, `16` for `run_aligned65537.sh`) | NTL thread pool size; these are the core counts of the machine the paper's runs were made on |

```bash
./run_po2.sh             # Table 12, 2000-bit rows   -> logs/sweep_po2_ma_sets.log
./run_po2_deep.sh        # Table 12, daggered rows   -> logs/sweep_po2_deep.log
./run_composed.sh        # Table 13, rows 1-3        -> logs/sweep_composed.log
./run_composed_4003.sh   # Table 13, row 4           -> logs/sweep_composed_4003.log
./run_aligned65537.sh    # Sec. 6 aligned-ring run   -> logs/sweep_aligned65537.log
```

Budget several hours per runner: each is a queue of 2–13 arms with a 5400–10800 s timeout each.

The fifth row of Table 13 (`p=65537`, `m=50731`) does **not** come from here. It is a full
recryption with the patched driver, `../../results/raw_logs/v_rerun_bsgs.log`, produced by
`../13_table_e2e_case5_bsgsfix.sh`; the top-level `README.md` explains why that row is a
different kind of measurement.

## Arguments

All four binaries share one `ArgMap`:

| argument | default | meaning |
|---|---|---|
| `m`, `p` | `60697`, `4003` | ring and plaintext prime |
| `A` | `823` | the radix: a primitive 6th root of unity for `hex`/`boxcl` (`A^2 = A-1`), a primitive 4th root for `box` (`A^2 = -1`). Checked at startup. |
| `B` | `20` | support radius |
| `bits` | `900` | HElib modulus-chain size |
| `ordr` | `6` | filter order `r`; `1..32` accepted, and an order with no filter terminates at the orbit-consistency check with `FATAL`, which is the measured verdict for that order |
| `sup` | `hex` | `hex` (Eisenstein hexagon), `box` (Gaussian square), `boxcl` (orbit closure of the infinity-norm box under the order-six map) |
| `kaps` | `4,6,...,20` | comma-separated Paterson–Stockmeyer parameters to sweep |
| `kappa` | `0` | run a single `kappa` instead of the sweep |
| `reps` | `1` | repetitions per `kappa` |
| `threads` | `1` | NTL thread pool size |
| `orbit` (m14, m15) | `1` | also run the composed arm when `d >= 2` |
| `relaxed` (m15) | `1` | accept the exact norm criterion, not just irreducibility |
| `skipirr` (m15) | `0` | diagnostic: reject irreducible `F`, exercising only the relaxed path |
