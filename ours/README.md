# Building the composed `(r,d)` evaluator

## Two layers, and why they are kept separate

The measured configuration is vanilla HElib (`homenc/HElib` at commit
`3e337a66a91a92d49de6a9505340826b0eb71081`) plus two patches applied in order. They come from
two different places, and the split is there so that the boundary is checkable rather than
asserted.

Layer 1, `patches/layer1_infrastructure.patch`, is the aux-radix thin-bootstrapping
infrastructure this paper's constructions sit on: the parameterisation of the recryption
pipeline by an auxiliary radix (`Context::aux_param`, `t_param`, the `newBtsFlag` path), which
realises Ma et al.'s bounded-support construction natively inside HElib instead of wrapping it.
It touches sixteen files across `include/helib/`, `src/`, `misc/` and `tests/`. **This layer is
not a contribution of this paper.** It is the substrate every arm runs on, including the
`BASELINE` arm that all the ratios are taken against, and it ships as its own patch so that it
is visible as a separate, attributed layer.

Layer 2 is what this paper contributes, in two files:
`patches/layer2_order456_composed_extractDigits.patch` (485 lines) generalises the order-four
split to arbitrary order `r`, adds the order-six construction on the orbit closure and the
composed `(r,d)` evaluator; `patches/layer2_explicit_aux_recryption.patch` (271 lines) adds the
one hook that lets the radix be pinned from the environment (`HELIB_EXPLICIT_AUX`) so that every
arm of a comparison uses the identical radix. Layer 2 is what changes between the
`BASELINE` / `ORDER4` / `ORDER6` / `*_COMPOSED` arms of every table.

`src/` ships the complete post-patch source of both touched files, for reading.
`apply_all.sh` reconstructs them from vanilla HElib through both layers and checks the result is
byte-identical to what is shipped.

```bash
./apply_all.sh ./HElib-patched      # clones vanilla HElib at the pinned commit, applies both
                                    # layers, diffs both files against src/
```

If you would rather check the patch chain than trust it, and would rather not clone HElib to do
so, `dev_history/legacy/extractDigits.vanilla-3e337a6.cpp` is that file at the pinned commit, so
the larger of the two layer-2 patches can be replayed offline in about ten seconds:

```bash
mkdir -p /tmp/chk/src && cd /tmp/chk && git init -q .
cp <artifact>/ours/dev_history/legacy/extractDigits.vanilla-3e337a6.cpp src/extractDigits.cpp
# layer 1 is a git diff over the whole tree; take only its extractDigits.cpp section
awk '/^diff --git a\/src\/extractDigits.cpp/{f=1} f&&/^diff --git/&&!/extractDigits/{f=0} f' \
    <artifact>/ours/patches/layer1_infrastructure.patch > l1.patch
git apply l1.patch
patch -p0 src/extractDigits.cpp < <artifact>/ours/patches/layer2_order456_composed_extractDigits.patch
diff src/extractDigits.cpp <artifact>/ours/src/extractDigits.cpp && echo "chain reproduces"
```

## Build

HElib's own prerequisites apply (GMP and NTL, or HElib's `PACKAGE_BUILD` mode); see its
`INSTALL.md`. The measurements were taken with GCC 9.5.0 `-O3` and NTL 11.5.1, single-threaded.

```bash
./apply_all.sh HElib-patched
cd HElib-patched && mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=$PWD/../../_install -DCMAKE_BUILD_TYPE=Release ..
make -j"$(nproc)" && make install

cd ../../fatboot-driver && mkdir build && cd build
cmake -Dhelib_DIR=$PWD/../../_install/share/cmake/helib ..
make -j"$(nproc)"
```

That produces `ours/fatboot-driver/build/fatboot`, which is the path `newexp/run_batch.sh`
expects; override it with `FATBOOT=<path>` if you build elsewhere.

## Running an arm

Every arm is the same binary. Only the environment changes, which is what makes the comparisons
head to head: identical ring, modulus chain, key and support in every arm of a case.

```bash
cd ours/fatboot-driver/build
export HELIB_ZZX_CACHE_DIR=$PWD/cache          # replaces the upstream driver's hard-coded path
unset HELIB_AUX_ORDER4_EVAL HELIB_COMPOSED_EVAL HELIB_FILTER_ORDER

# Ma et al.'s baseline, set V (p=65537, m=50731):
HELIB_EXPLICIT_AUX=256 ./fatboot i=4 h=12 t=-1 newbts=1 newks=1 thick=0 repeat=1

# order-four filter (Xiong-Wang):
HELIB_EXPLICIT_AUX=256 HELIB_AUX_ORDER4_EVAL=1 \
  ./fatboot i=4 h=12 t=-1 newbts=1 newks=1 thick=0 repeat=1

# composed (r,d) evaluator:
HELIB_EXPLICIT_AUX=256 HELIB_AUX_ORDER4_EVAL=1 HELIB_COMPOSED_EVAL=1 \
  ./fatboot i=4 h=12 t=-1 newbts=1 newks=1 thick=0 repeat=1

# order six, set IV (p=8191, a Mersenne prime, where no order-four radix exists):
HELIB_EXPLICIT_AUX=90 HELIB_AUX_ORDER4_EVAL=1 HELIB_FILTER_ORDER=6 \
  ./fatboot i=3 h=12 t=-1 newbts=1 newks=1 thick=0 repeat=1
```

At `i=3`, `HELIB_AUX_ORDER4_EVAL` on its own has no effect: `8191 = 7 (mod 12)`, so there is no
order-four radix and the evaluator declares itself inapplicable rather than quietly running the
baseline. `HELIB_FILTER_ORDER=6` is what gets past the baseline there. `newexp/README.md` has the
full arm-to-environment table, and `newexp/arms.sh` is the same mapping in shell.

`fatboot-driver/readme.md` documents the command-line arguments and the `custom=1` mode, in
which `gens`/`ords` are left empty and HElib derives the hypercube itself. The preset table
`real_params[]` in `fatboot.cpp` has 34 entries, `i=0..33`: `i=0..2` are Ma et al.'s sets at
`p=17,127,257`, `i=3` and `i=4` are their sets IV and V, `i=5..13` are earlier order-four
candidates kept for their rejection notes, and `i=14..33` are the 20 rings of the sweep, in the
order of `newexp/sets.tsv` and `newexp/sets128.tsv`. How the generators in each preset were
derived is in `newexp/PARAMETERS.md`.

## What layer 2 changes, file by file

`extractDigits.cpp`:

1. `compute_prime_aux_poly_order6` builds the order-six polynomial on the orbit closure of the
   caller's own box, basis-free: it propagates the low-digit map along the order-six orbit via
   the covariance relation and declines if the orbit does not close consistently, rather than
   guessing.
2. `splitFilterCleaner` and the evaluator are generalised from the hard-coded order-four split
   to arbitrary order `r`.
3. `buildComposedPlan` is the offline half of `ComposedEval`: fold by `X^r`, pad `Gamma` until
   `d | deg Gamma`, search `Q + (Gamma)` for a norm form, factor it, encode `C`.
4. `composedBsgsEnc` and `composedOrbitProduct` are the online half: baby-step/giant-step on `C`
   composed with the Frobenius doubling schedule.
5. The activation line is printed once, the first time the composed branch is *evaluated*, not
   when its plan is built. `../VERIFICATION.md` explains why that distinction is load-bearing.

`recryption.cpp`: one addition, reading `HELIB_EXPLICIT_AUX` to pin the radix instead of always
deriving it from the noise bound. The rest of this file's content is layer 1.

## Two debug markers you will see, and what they gate

`src/extractDigits.cpp:396` and `:407` are a `// XXX: debug` pair around a null-polynomial
assertion. They are dead: the block is guarded by `#ifdef HELIB_DEBG`, with the `U` missing, and
nothing in HElib or in either patch defines `HELIB_DEBG`. The typo comes from layer 1 — it is at
`patches/layer1_infrastructure.patch:1262` — so it is upstream of this paper's contribution. It
is left alone rather than fixed because `apply_all.sh` verifies `src/extractDigits.cpp` byte for
byte against the patch chain, and correcting the typo here would mean editing layer 1.

The other `// XXX: debug` pairs in the same file (`:985`/`:1008` and `:1021`/`:1075`) are inside
correctly spelled `#ifdef HELIB_DEBUG` blocks and do compile in a debug build. None of them runs
in the Release builds the measurements were taken with.

## `dev_history/`

The incremental patches and helper scripts from the development of layer 2, plus the vanilla
`extractDigits.cpp` at the pinned commit and the single-file version of the layer-2 patch before
it was split. None of it is needed to build or reproduce anything; `patches/` is the final state.
It is shipped because the one regression this process caught is described in `../VERIFICATION.md`
and it should be possible to look at the code rather than take the description on trust.
