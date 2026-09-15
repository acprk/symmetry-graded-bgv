# Building the composed `(r,d)` evaluator

## Two layers, and why they are kept separate

This artifact reaches its measured configuration in two patches against vanilla HElib
(`homenc/HElib` at commit `3e337a6`), applied in order, because they come from two
different places and we want that distinction to be checkable, not asserted:

**Layer 1** (`patches/layer1_infrastructure.patch`) is the *aux-radix thin-bootstrapping
infrastructure* this paper's constructions are built on top of: the parameterisation of
the recryption pipeline by an auxiliary radix (`Context::aux_param`, `t_param`, the
`newBtsFlag` code path), which realises the bounded-support construction of Ma et
al., EUROCRYPT'24 natively inside HElib rather than as an external wrapper. **This layer
is not a contribution of this paper.** It is the common substrate every arm in Tables 4,
5, 7 and 8 runs on, including the `MA_BASELINE` arm (Section "Building each baseline" in
`../baselines/README.md`), and we ship it as its own patch precisely so that it is visible
as a separate, clearly-attributed layer rather than folded invisibly into "our code".

**Layer 2** (`patches/layer2_order456_composed_extractDigits.patch` and
`patches/layer2_explicit_aux_recryption.patch`) is what this paper actually contributes:
the generalisation of the order-four split to an arbitrary order `r`, the order-six
construction on the orbit closure, the composed `(r,d)` evaluator (`ComposedEval`), and
the small `recryption.cpp` hook that lets the radix be pinned explicitly
(`HELIB_EXPLICIT_AUX`) so that every arm of a comparison uses the identical radix. Layer 2
is what changes between the `MA_BASELINE` / `ORDER4` / `COMPOSED` arms of every table.

`ours/src/` ships the complete, final source of both touched files for readability;
`apply_all.sh` reconstructs them from vanilla HElib through both layers and verifies the
result is byte-identical to what is shipped — run it yourself:

```bash
./apply_all.sh ./HElib-patched      # clones vanilla HElib, applies both layers, diffs
```

## Build

```bash
./apply_all.sh HElib-patched
cd HElib-patched
mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=$PWD/../../_install -DCMAKE_BUILD_TYPE=Release ..
make -j"$(nproc)" && make install

cd ../../fatboot-driver
mkdir build && cd build
cmake -Dhelib_DIR=$PWD/../../_install/share/cmake/helib ..
make -j"$(nproc)"
```

## Running an arm

Every arm below runs the *same binary*; only the environment variables change, which is
what makes the comparisons in the paper head-to-head (identical ring, modulus chain, key,
and support in every arm of a case).

```bash
export HELIB_EXPLICIT_AUX=256        # the auxiliary radix, box form
export HELIB_ZZX_CACHE_DIR=$PWD/cache
unset HELIB_AUX_ORDER4_EVAL HELIB_COMPOSED_EVAL HELIB_FILTER_ORDER

# Ma et al. baseline (odd bounded-support filter):
./fatboot i=4 h=12 t=-1 newbts=1 newks=1 thick=0 repeat=1

# order-4 filter (Xiong et al., this line of work's prior paper):
HELIB_AUX_ORDER4_EVAL=1 ./fatboot i=4 h=12 t=-1 newbts=1 newks=1 thick=0 repeat=1

# our composed evaluator (order-4 + Galois norm map):
HELIB_AUX_ORDER4_EVAL=1 HELIB_COMPOSED_EVAL=1 \
  ./fatboot i=4 h=12 t=-1 newbts=1 newks=1 thick=0 repeat=1

# order-6 (Eisenstein), at a Mersenne prime where order-4 does not exist:
HELIB_EXPLICIT_AUX=90 HELIB_AUX_ORDER4_EVAL=1 HELIB_FILTER_ORDER=6 \
  ./fatboot i=3 h=12 t=-1 newbts=1 newks=1 thick=0 repeat=1
```

`i=4` is Case V (`p=65537`, `m=50731`); `i=3` is Case IV (`p=8191`, `m=45193`, a Mersenne
prime, where `HELIB_AUX_ORDER4_EVAL` alone has no effect since no order-4 radix exists —
`rem:mersenne` — and `HELIB_FILTER_ORDER=6` is needed to reach anything past the
baseline).

## What layer 2 actually changes, file by file

`extractDigits.cpp`:
1. `compute_prime_aux_poly_order6` — builds the order-six polynomial on the orbit
   closure of the caller's own box, basis-free (it propagates the low-digit map along
   the order-six orbit via the covariance relation and declines if the orbit does not
   close consistently, rather than guessing).
2. `splitFilterCleaner` / the evaluator — generalised from the hard-coded order-4 split
   to an arbitrary order `r`.
3. `buildComposedPlan` — offline half of `ComposedEval` (Algorithm 1): folds by `X^r`,
   pads `Γ` until `d | deg Γ`, searches `Q + (Γ)` for a norm form, factors it, encodes `C`.
4. `composedBsgsEnc` / `composedOrbitProduct` — online half: baby-step/giant-step on `C`
   (not a Horner chain — see `../VERIFICATION.md` rule 4) composed with the Frobenius
   doubling schedule.
5. An activation announcement printed once, the first time the composed branch is
   *evaluated*, not when its plan is built — see `../VERIFICATION.md` rule 1.

`recryption.cpp`: one addition, reading `HELIB_EXPLICIT_AUX` to pin the radix explicitly
(so all arms of a comparison share it) instead of always deriving it from the noise
bound. Everything else in this file's diff against layer 1 is layer 1 itself; the layer-2
patch for this file is 271 lines, almost all of it this one hook.

## Scope

The two layers above are the final, complete state; there is no intermediate development
history shipped in this artifact (the paper's `VERIFICATION.md` documents the one
regression this development process caught and fixed, as a worked example, without
requiring the intermediate patches themselves).
