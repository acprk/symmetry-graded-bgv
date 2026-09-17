# Baselines: pinned upstream sources

We compare against the authors' own code wherever it exists, not our reimplementation of
their method. This directory documents exactly which commit of which repository each
baseline in the paper is, and how to build it. None of the three repositories below is
vendored into this artifact (to keep it small and to avoid re-distributing other authors'
code); `setup.sh` clones each at the pinned commit.

## The three baselines

| Paper citation | Method | Repository | Pinned commit |
|---|---|---|---|
| Ma et al., EUROCRYPT'24 | Bounded-support digit extraction (the odd filter) | `github.com/msh086/BGV-Boot-for-Large-p` | `83b54d534ef36776c912ca49247d1e3157509299` |
| Zhao et al., CRYPTO'26 | Galois norm-map evaluation | `github.com/Nobody673/artifact-helib` | `e8b9cab0908e994a8f2d7b9b2c3dda02bf135c32` |
| Geelen et al., EUROCRYPT'23 | Null-polynomial lattice sparsification | `github.com/KULeuven-COSIC/Bootstrapping_Polyfunctions` | `fc27e5461815499c1d6366a1d73ec7e39087b2cd` |
| Xiong et al. (this line of work's prior paper) | The order-four character filter | *same codebase as `ours/`* | see `ours/README.md` |

The fourth row is not a separate download: the order-four filter is one configuration
(`HELIB_AUX_ORDER4_EVAL=1`, `HELIB_COMPOSED_EVAL` unset) of the exact same patched HElib
tree in `ours/`, since our composed evaluator is built as a strict extension of it. Running
it with both flags unset instead reproduces the Ma et al. baseline *on the same code path*,
which is what makes the ratios in Tables 4, 5, 11 and 14 head-to-head: only the environment
variable changes, not the ring, modulus chain, key, or support.

## Zhao et al.'s artifact: how the patches select a prime

`artifact-helib` is a fork of vanilla HElib (`homenc/HElib` at commit `3e337a6`) with five
patches, one per plaintext prime:

```
patches/GN17.patch      patches/GN127.patch     patches/GN257.patch
patches/GN8191.patch    patches/GN65537.patch
```

Each patch hard-codes the generalized-Fermat/generalized-Mersenne parameters for its prime
into `src/extractDigits.cpp` and the context-construction utilities. To reproduce a
particular row, check out vanilla HElib at `3e337a6`, apply the matching `GN*.patch`, and build
with the artifact's own `CMakeLists.txt`. That is what the shipped logs record: all five presets
were rebuilt and run this way, `p=8191` and `p=65537` in `results/raw_logs/build_and_run.log` and
`p=17`, `127`, `257` in `zhao_repro_p17_p127_p257.log`, against Ma et al. at the same five
presets in `ma_baseline_five_presets.log`. The `1.15x`-`2.37x` range quoted in Section 6, and the
`1.63x` at set V in Table 5, are the five extraction-time ratios between those files; the
top-level `README.md` gives the greps. We did **not** modify Zhao et al.'s code to run the aux-radix path
their artifact does not support: the abort recorded in `zhao_thin24.log`
(`helib::LogicError: thin results not match`) is their own code refusing an input outside its
scope, which is exactly the obstruction the paper's `thm:obstruction` predicts.

## Building each baseline

```bash
./setup.sh                 # clones all three repos at the pinned commits above into ./_upstream/
cd _upstream/BGV-Boot-for-Large-p   && cat README.md   # their own build instructions
cd _upstream/artifact-helib          && cat README.md   # their own build instructions; apply patches/GN*.patch
cd _upstream/Bootstrapping_Polyfunctions && cat README.md
```

We do not re-document their build systems here beyond what `setup.sh` automates (cloning at
the pinned commit); each is a complete, independently buildable HElib-based project with its
own README. If a build fails, it is a statement about that snapshot of their repository, not
about this artifact — pin exactly the commit above, since all three projects have moved on
since these measurements were taken.

## The r = 1..32 exhaustive scan

Not a baseline comparison but a self-check, that the selector's claim — only `r` in
`{2,3,4,6}` ever closes — is not an artifact of having looked only at small `r`. Appendix E
reports it in prose ("we tested every `r <= 32` at `p = 65521`"); the table it was drawn from is
commented out in the current manuscript. Reproduce the scan with:

```bash
cd ../selector
python3 select.py --p 65521 --m 0 --B 20 --support hex --rmax 32 --json | python3 -c \
  "import json,sys; d=json.load(sys.stdin); print([r['r'] for r in d['rows']])"
```

which enumerates every divisor of `p-1` up to 32 and reports which ones survive the
full-orbit consistency check of `Procedure SELECT` step 2(c) — the same check, at the same
prime, that produced the paper's table.
