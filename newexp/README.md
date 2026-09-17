# The extended sweep: Section 6 and Appendix D

Twenty-two general cyclotomic rings `m = q1*q2`, seventeen at encapsulated key weight `h=12` and
five at `h=26`, each measured with every digit-extraction evaluator that applies to it. All arms
of a ring run the same binary on the same ring, modulus chain, key and support; only environment
variables differ, and every run ends with HElib's own all-slot decryption check.

`PARAMETERS.md` is the companion to this file: it derives every parameter set and every security
figure from first principles. This file is about running the thing.

## Building the driver

Everything here invokes `../ours/fatboot-driver/build/fatboot`, which does not exist until you
build it. The full path, from a clean checkout, is in `../ours/README.md`; the short version is

```bash
cd ours
./apply_all.sh HElib-patched                   # clones HElib at 3e337a6, applies both layers
cd HElib-patched && mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=$PWD/../../_install -DCMAKE_BUILD_TYPE=Release ..
make -j"$(nproc)" && make install
cd ../../fatboot-driver && mkdir build && cd build
cmake -Dhelib_DIR=$PWD/../../_install/share/cmake/helib .. && make -j"$(nproc)"
```

`run_batch.sh` checks for the binary and stops with the path it expected if it is missing. Set
`FATBOOT=<path>` to point it somewhere else.

## The arms

Six evaluators. `HELIB_EXPLICIT_AUX` pins the radix so that every arm of a ring uses the same
one; the rest select the evaluator. `arms.sh` maps an arm name onto these variables, reading
`aux4`/`aux6` from the parameter file.

| arm | `HELIB_EXPLICIT_AUX` | `HELIB_AUX_ORDER4_EVAL` | `HELIB_FILTER_ORDER` | `HELIB_COMPOSED_EVAL` | what it is |
|---|---|---|---|---|---|
| `BASELINE` | `aux4`, or `aux6` if no order-four radix | – | – | – | Ma et al.'s odd bounded-support filter with Paterson–Stockmeyer |
| `ORDER4` | `aux4` | 1 | – | – | order-four character filter (Xiong–Wang), `p = 1 (mod 4)` |
| `ORDER4_COMPOSED` | `aux4` | 1 | – | 1 | order four followed by the Galois norm map |
| `ORDER6` | `aux6` | 1 | 6 | – | order-six filter on the box's orbit closure, `p = 1 (mod 3)` |
| `ORDER6_COMPOSED` | `aux6` | 1 | 6 | 1 | order six followed by the Galois norm map |
| `NORMONLY` | same as `BASELINE` | 1 | 1 | 1 | control: norm map on the *unfiltered* `P_A`, i.e. Zhao et al.'s axis without the scalar fold |

Every arm runs `fatboot i=<idx> h=<12|26> t=-1 newbts=1 newks=1 thick=0 repeat=1`.

The `arms` column of the parameter files says which arms apply to which ring. On `p = 7 (mod 12)`
there is no order-four radix, so only the order-six arms run; on `p = 5 (mod 12)` there is no
cube root of unity, so only the order-four arms run; on `p = 1 (mod 12)` both exist and all five
evaluators run.

## Parameter sets

`sets.tsv` (15 rings at `h=12`), `sets128.tsv` (5 rings at `h=26`), `cases.tsv` (Ma et al.'s sets
IV and V, presets `i=3` and `i=4`). One tab-separated line per ring:

    idx  p  p%12  m  q1  q2  d  slots  chain-bits-requested  aux4  aux6  arms

`idx` is the `i=` argument of the driver and indexes `real_params[]` in
`../ours/fatboot-driver/fatboot.cpp`, where the same ring also carries its hypercube generators.
How each column was arrived at — the ring conditions, the digit bound, the radix, the chain, the
Lattice Estimator run — is in `PARAMETERS.md`.

## Running

```bash
newexp/run_batch.sh 1                                     # pass 1, all of sets.tsv, all arms
newexp/run_batch.sh 2 14 16 22 27                         # pass 2 on the four repeated rings
SETS=newexp/sets128.tsv newexp/run_batch.sh 1 29 30 31 32 33 H=26
SETS=newexp/cases.tsv   newexp/run_batch.sh 1 3 4         # sets IV and V
newexp/run_batch.sh 1 17 ARMS=NORMONLY TIMEOUT=21600      # one arm, longer budget
```

A full pass over `sets.tsv` is a few days of single-threaded wall clock. The runs behind the
shipped logs were scheduled four at a time on a shared 104-core machine by a small wrapper around
`run_batch.sh` that is not part of this artifact; nothing in the measurements depends on it,
but it is the reason absolute times vary between passes and the reason every ratio in the paper
is taken within one pass (see `../VERIFICATION.md`, rule 3).

## From logs to tables

```bash
python3 newexp/collect.py            # logs/ -> results.csv, one row per (ring, arm, pass)
python3 newexp/make_final.py         # results.csv -> final/final_rows.json, tables_final.tex,
                                     #                fig_extract_time.pdf, fig_speedup_vs_d.pdf
python3 newexp/make_appendix_tables.py   # -> final/tab_offline.tex, tab_sec_full.tex, tab_passes.tex
python3 newexp/make_origin_figs.py   # -> final/fig6a_bars.pdf, fig6b_speedup.pdf,
                                     #    tab_results_compact.tex, tab_params_compact.tex
python3 newexp/parse_logs.py         # human-readable dump, one line per run, no files written
```

The three generators take an optional output directory as their first argument; with none they
write into this directory (`final/`, for `make_appendix_tables.py`). Running them into a scratch
directory and diffing against `final/` reproduces every checked-in table byte for byte. The two
figure scripts need matplotlib, which on the machine these were made on lives in
`/usr/bin/python3` and not in every interpreter on `PATH`; they say so and exit rather than
tracebacking.

`collect.py` keeps the last block of a log that passes all three validity checks — HElib's
`everything ok`, `exit=0`, and the arm's own activation string — and falls back to a failing
block only if nothing valid exists for that `(ring, arm, pass)`. `make_final.py` then picks, per
ring, the pass whose `BASELINE` linear-transform time is smallest, and takes all three arms of
the row from that pass.

The two panels of Fig. 7 (`fig6a_stacked.pdf`, `fig6b_prior.pdf`) come from
`make_fig6_v2.py <outdir>`, which re-parses the per-stage times from `logs/` so the stacked
bars are not taken on trust from `final_rows.json`; `make_origin_figs.py` produces the earlier
grouped-bar and speedup-versus-`d` pair.

## Logs

`logs/set<idx>_p<p>[_h26]_pass<k>.log`, appended arm by arm, one banner per arm:

    ########## SET 22 p=14401 m=43033 d=11 :: ORDER6_COMPOSED :: aux=318 :: pass2 :: h=12 :: ... ##########

The lines that carry the measurements are

    time for linear1 = ..., linear2 = ..., extract = ..., total = ...
    bits for linear1 = ..., linear2 = ..., extract = ..., min cap = ..., after cap = ...
    number of bits = ...                     the chain HElib built
    security level = ...                     HElib's own estimate, not the one in the paper
    HELIB_COMPOSED_EVAL: norm form c=... degC=... (search ...s)
    HELIB_COMPOSED_EVAL active: order=... degC=... d=...     printed only when the plan is evaluated

`logs/smoke/` holds three short pre-sweep context builds. Two are on rings that made it into
`sets.tsv`; the third, `smoke_i20_baseline.log`, is `p=3307` on `m=41*1361=55801`, an earlier
candidate that was replaced by `827*73=60371` before the sweep. `smoke_custom_8191_baseline.log`
is the `custom=1` mode driven at Case IV's own ring with `gens`/`ords` left empty, and it fails
— `Invalid argument: sig and reps have inconsistent dimension` — which is one of the failure
modes `../ours/fatboot-driver/readme.md` warns about, on a ring that works perfectly well once
the generators are supplied by hand.
`logs/set15_p4423_pass1_before_signfix.log` is the first measurement of `p=4423`, taken before a
sign fix in the order-six construction; it is superseded by `set15_p4423_pass1.log` and
`collect.py` skips any file with `before` in its name. It is kept so that the correction is
visible rather than merely asserted.

## What did not work

Three things about the sweep that the tables do not show.

`NORMONLY` completed on 14 of the 22 rings. In every one of those 14 the evaluator reported
`no norm form found; staying on P-S` — the unfiltered `P_A` has no norm form in its coset, which
is the obstruction the scalar fold removes, so the arm is a control that measures the baseline
again rather than an evaluator that runs. The other 8 did not finish: seven hit the 90-minute
budget during the search (`exit=124`: `p=65537`, `19183`, `37831`, `60271` at `h=12`, and
`15377`, `8101`, `14401` at `h=26`), and one, `p=13457` at `h=26`, was killed after 470 s
(`exit=143`) when its worker was terminated. Re-running those eight with `TIMEOUT=21600` is the
obvious thing to do; it was not done.

The order-six arm of set 30 (`p=2917`, `h=26`) reports its radix as not injective — the box
closure needs `6*24^2+6*24+1 = 3601` points and `p` is 2917 — and then dies. The detection line
is correct and is the one Appendix D cites; the fallback to order four that it announces does
not survive, and the arm ends in `ZZ_p: division by non-invertible element` and `exit=134`.
Set 30's published row comes from its `ORDER4` and `ORDER4_COMPOSED` arms, which complete and
verify. Details in `PARAMETERS.md`, section 6.

Four rings — `p = 2971`, `13807`, `14401`, `13457` — were measured twice, on different days and
under different machine load; the remaining eighteen were measured once. `tab:passes` reports
both passes for those four. Note that its `p=14401` rows are the order-four arms, whereas
`tab:e2e` reports the order-six arms for that ring, because those were faster; the two tables
label different evaluators "composed" on that one row.
