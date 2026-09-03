# Building the composed `(r,d)` evaluator

This is a single-file patch to vanilla HElib's digit-extraction implementation
(`src/extractDigits.cpp`), plus a thin-bootstrapping test driver (`fatboot-driver/`) built
on top of it. It implements, in one code path selected by environment variables, every
arm compared in the paper:

| Environment variables | Evaluator | Corresponds to |
|---|---|---|
| (none set) | generic / odd bounded-support | Ma et al., EUROCRYPT'24 |
| `HELIB_AUX_ORDER4_EVAL=1` | order-4 character filter | Xiong et al. (this line of work's prior paper) |
| `HELIB_AUX_ORDER4_EVAL=1 HELIB_FILTER_ORDER=6` | order-6 Eisenstein filter | this paper, §5 (new) |
| `HELIB_AUX_ORDER4_EVAL=1 HELIB_COMPOSED_EVAL=1` | order-4 + Galois norm map, composed | this paper, §6–7 |
| `HELIB_AUX_ORDER4_EVAL=1 HELIB_FILTER_ORDER=6 HELIB_COMPOSED_EVAL=1` | order-6 + Galois norm map, composed | this paper, the headline configuration |

Running all arms through **one code path** with only an environment variable changed is
what makes the ratios in Tables 4, 5, 7 and 8 head-to-head: the ring, modulus chain, key,
and support are byte-identical across arms, and only the digit-extraction polynomial
evaluator differs.

## Build

```bash
# 1. Vanilla HElib at the pinned base commit
git clone https://github.com/homenc/HElib.git HElib-patched
cd HElib-patched
git checkout 3e337a66a91a92d49de6a9505340826b0eb71081

# 2. Apply our patch
patch -p1 < ../patches/order4_order6_composed.patch
# (equivalently: cp ../src/extractDigits.cpp src/extractDigits.cpp -- the patch and the
#  full file in src/ are the same change, offered in both forms for convenience)

# 3. Build HElib as usual (see HElib's own INSTALL.md), e.g.
mkdir build && cd build
cmake -DCMAKE_INSTALL_PREFIX=$PWD/../_install -DCMAKE_BUILD_TYPE=Release ..
make -j"$(nproc)" && make install

# 4. Build the thin-bootstrapping driver against the installed library
cd ../../fatboot-driver
mkdir build && cd build
cmake -Dhelib_DIR=$PWD/../../HElib-patched/_install/share/cmake/helib ..
make -j"$(nproc)"
```

## Running an arm

```bash
export HELIB_EXPLICIT_AUX=256       # the auxiliary radix's box-form representative
export HELIB_ZZX_CACHE_DIR=$PWD/cache   # see VERIFICATION.md: this cache affects timing
unset HELIB_AUX_ORDER4_EVAL HELIB_COMPOSED_EVAL HELIB_FILTER_ORDER

# Ma et al. baseline:
./fatboot i=4 h=12 t=-1 newbts=1 newks=1 thick=0 repeat=1

# order-4 filter (Xiong et al.):
HELIB_AUX_ORDER4_EVAL=1 ./fatboot i=4 h=12 t=-1 newbts=1 newks=1 thick=0 repeat=1

# our composed evaluator:
HELIB_AUX_ORDER4_EVAL=1 HELIB_COMPOSED_EVAL=1 \
  ./fatboot i=4 h=12 t=-1 newbts=1 newks=1 thick=0 repeat=1
```

`i=4` selects the parameter set index built into the driver (Case V, `p=65537`,
`m=50731`); `i=3` selects Case IV (`p=8191`, `m=45193`, a Mersenne prime, where
`HELIB_AUX_ORDER4_EVAL` alone has no effect since no order-4 radix exists — see
`rem:mersenne` — and `HELIB_FILTER_ORDER=6` must be added to reach anything beyond the
baseline).

## What `extractDigits.cpp` actually changes

The patch (`patches/order4_order6_composed.patch`, 1074 lines against the 310-line
vanilla file) adds, without touching any code path the baseline arm executes:

1. `compute_prime_aux_poly_order6` — builds the order-six digit-extraction polynomial on
   the *orbit closure* of the caller's own box (basis-free: it propagates the low-digit
   map along the order-six orbit using the covariance relation, and declines rather than
   guessing if the orbit does not close consistently).
2. `splitFilterCleaner` / the evaluator loop — generalised from the hard-coded order-4
   split (`X, X^2, X^3, X^4`) to an arbitrary order `r` (`X, ..., X^{r-1}, X^r`).
3. `buildComposedPlan` — the offline half of `ComposedEval` (Algorithm 1 of the paper):
   folds the interpolant by `X^r`, pads the vanishing ideal `Γ` until `d | deg Γ`,
   searches the coset `Q + (Γ)` for a norm form, factors it over the slot ring, and
   encodes the resulting constant `C` into plaintext slots.
4. `composedBsgsEnc` / `composedOrbitProduct` — the online half: a baby-step/giant-step
   evaluation of `C` (not a Horner chain — see `VERIFICATION.md` for why this distinction
   is load-bearing for the capacity numbers in Table 6) composed with the Frobenius
   doubling schedule that closes the norm-map orbit.
5. An activation announcement (`std::cout << "HELIB_COMPOSED_EVAL active: ..."`) printed
   exactly once, the first time the composed branch is actually *evaluated* on a
   ciphertext — not when the plan is merely built. Every script in `../experiments/`
   `grep`s for this line before trusting a log's numbers; see `VERIFICATION.md`.

## `dev_history/`

The patch above is the *final* state. `dev_history/` additionally ships the sequence of
smaller patches applied during development (the BSGS-vs-Horner fix, the order-6
generalisation, the monodromy-label fix, etc.), each with the commit message explaining
what it corrected and why, for readers who want the paper trail rather than only the
end state. They are not needed to reproduce any table; the single patch above is.
