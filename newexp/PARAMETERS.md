# How every parameter set was derived

This file reconstructs the 22 parameter sets of Appendix D from scratch: the ring, the digit
bound, the radix, the modulus chain and the two security estimates. Everything below is checked
against the shipped data (`sets.tsv`, `sets128.tsv`, `cases.tsv`,
`../ours/fatboot-driver/fatboot.cpp`, `final/final_rows.json`, `final/tab_offline.tex`,
`final/tab_sec_full.tex`, `security/*.json`); where the manuscript and the data disagree, the
data is quoted and the disagreement is stated.

A set is fully described by seven numbers: the plaintext prime `p`, the two factors `q1, q2` of
the cyclotomic index `m`, the encapsulated key weight `h`, the requested chain length in bits,
and the two radices `aux4`/`aux6`. Those seven are exactly the columns of `sets.tsv`; the driver
preset in `fatboot.cpp` adds the hypercube generators, which are derived from them.

## 1. The ring

### What the ring has to satisfy

`m = q1 * q2` with `q1, q2` distinct odd primes, and `d = ord_m(p)` the slot degree, so that
`phi(m) = (q1-1)(q2-1)` and the number of slots is `phi(m)/d`. HElib's thin evaluation map
(`ThinEvalMap`, `src/EvalMap.cpp`) decomposes along the two CRT factors, and the recryption
code needs the decomposition to be a prefix of the inert tower. Three conditions come out of
that, and all 22 rings were screened against them before anything was built:

1. `ord_{q1}(p)` divides `ord_{q2}(p) = d`. This holds on all 22 rings; the quotients range from
   1 (e.g. `p=13807`, `ord_59(13807)=1`) to `d` itself (e.g. `p=14401`, both orders 11).
2. The first hypercube dimension is the whole of `(Z/q1)^*`, of order `q1 - 1`.
3. The second dimension has order `(q2-1)/d`, so `d` must divide `q2 - 1`.

Appendix D also states `gcd((q2-1)/d, d) = 1`. That is the condition for the second dimension to
be *good* in HElib's sense (rotation is a bare automorphism, no masking), and it holds on 19 of
the 22 rings. It fails on three — `p=4513` (`154 = 2*7*11`, `d=4`), `p=8101` at `h=26`
(`74 = 2*37`, `d=8`) and `p=14401` at `h=26` (`286 = 2*11*13`, `d=10`) — and those three
nevertheless build, bootstrap and decrypt correctly. In `fatboot.cpp` they are exactly the
presets whose second `ords` entry is negative (`{60,-154}`, `{96,-74}`, `{18,-286}`): HElib's
convention is that a negative order marks a bad dimension. So the condition is a preference, not
a requirement.

### The hypercube generators

`mvec = (q1, q2)` is handed to HElib, and `gens`/`ords` are supplied explicitly rather than
letting `findGenerators` search, because the search is slow on these `m` and does not always
return a decomposition the recryption path accepts. The two generators are CRT lifts:

    g1 = CRT( a generator of (Z/q1)^* ,  1 mod q2 )      ords[0] = q1 - 1
    g2 = CRT( 1 mod q1 ,  an element of order (q2-1)/d in (Z/q2)^* / <p> )
                                                         ords[1] = ±(q2-1)/d

with the sign negative when `g2` has larger order in `(Z/q2)^*` than in the quotient by `<p>`,
i.e. on the three bad-dimension rings above. Every preset in `fatboot.cpp` in the ranges
`i=3,4` and `i=14..33` satisfies this exactly; it can be rechecked in a few lines of sympy
against the `gens`/`ords` literals in the file.

The comments on presets `i=5..13` in `fatboot.cpp` record the failures this screening is meant
to avoid, in the authors' own words: `m=42311=29*1459` "rejected (ThinEvalMap bad
inertPrefix)", `m=29941` "cyclic single-gen, unfit for mvec recryption", `m=42541` "q2=379 not
carrier". `../ours/fatboot-driver/readme.md` lists the same failure modes for the `custom=1`
mode, where `gens`/`ords` are left empty and HElib derives them itself.

### The 22 rings

`sets.tsv` holds the 15 new rings at `h=12`, `sets128.tsv` the 5 at `h=26`, `cases.tsv` Ma et
al.'s sets IV (`i=3`) and V (`i=4`). The columns are

    idx  p  p mod 12  m  q1  q2  d  slots  chain-bits-requested  aux4  aux6  arms

and `idx` is the `i=` argument of the driver. Coverage: seven rings with `p = 7 (mod 12)`
(order six only), six with `p = 1` (both orders exist), two with `p = 5` (order four only) at
`h=12`, plus the two Ma et al. sets; slot degrees run from `d=3` (`p=4423`) to `d=18`
(`p=2521`, `p=65537`) at `h=12` and down to `d=2` at `h=26` (`p=13457`, `m=65047`); slot counts
run from 2784 to 15340 at `h=12`, and up to 31388 on that `d=2` ring.

## 2. The digit bound B and the degree of P_A

`B` is not chosen. HElib computes it from the ring and the encapsulated key weight `h` through
Ma et al.'s overflow estimate, and prints it as `bound on I = <x>`; the pipeline uses
`B = ceil(x)`. The measured values are `B = 17` at `h = 12` on every ring except `p = 4423`,
where `x = 15.75` and `B = 16`, and `B = 24` at `h = 26`. (`collect.py` reads that line; the
per-run values are the `B` column of `results.csv`.)

`B` then fixes the support region and hence the degree of the interpolated polynomial. The
region is the set of lattice points the low digit has to be correct on, and

    deg P_A = |region| - 2

in both cases:

| region | `|region|` | `deg P_A` | at `B=16` | at `B=17` | at `B=24` |
|---|---|---|---|---|---|
| order-four box | `(2B+1)^2` | `(2B+1)^2 - 2` | 1087 | 1223 | 2399 |
| order-six closure of that box | `6B^2+6B+1` | `6B^2+6B-1` | 1631 | 1835 | 3601 |

Both columns are confirmed in the logs: `HELIB_ORDER6: ... |closure|=1837 ... deg(P)=1835` at
`B=17`, and `deg of poly for non-power-of-p aux is 1223` on the box arms. Section 6 of the
manuscript writes the order-six degree as `6B^2+6B+1 = 1835`; `6*17^2+6*17+1` is 1837, so the
formula there should read `6B^2+6B-1`. The value 1835 is the one the code uses and the one in
`tab:offline`.

The folded polynomial is shorter by the fold factor: `deg Q = floor(deg P_A / r*)`, giving 305
at `B=17` for both `r*=4` (`1223/4`) and `r*=6` (`1835/6`), 271 at `B=16`, and 599 at `B=24`.
`deg Q` is padded up to `n'` so that `d | deg Gamma`; `n'` is 306–312 at `B=17` and 600 at
`B=24`. All of these are columns of `final/tab_offline.tex` and are regenerated by
`make_appendix_tables.py`.

At `h=26` only order four is used. The order-six closure would need 3601 points, and the
smallest `h=26` ring is `p=2917`, so the region does not inject: the `ORDER6` arm of set 30
prints `HELIB_ORDER6: box not injective at aux=248`. See section 6 below for what actually
happens next, which is not what the manuscript says.

## 3. The radix A

The overflow part of the bootstrapping pipeline is reduced modulo `|A|`, and the short modulus
`q` grows linearly in `|A|`, so the radix has to be large enough to separate the digits and
small enough not to inflate the chain:

    2B < |A| << p

`A` is a root of the cyclotomic polynomial `Phi_{r*}` modulo `p`: `A^2 = -1` for `r* = 4`,
`A^2 = A - 1` for `r* = 6`. It is passed to the driver as `HELIB_EXPLICIT_AUX`, which pins it
so that all arms of a comparison share the identical radix instead of each deriving its own
from the noise bound.

For `r* = 4` the shipped `aux4` is, on every ring where it exists, the smallest absolute
representative of a root of `x^2+1`: 71 (`p=2521`), 54 (2917), 90 (8101), 95 (4513), 116
(13457), 120 (14401), 124 (15377), 256 (65537). Every one is well above `2B = 34`
(48 at `h=26`) and far below `p`; the tightest is `A=54` against `p=2917`.

For `r* = 6` the four candidates `{A, A-1, -(A-1), -A}` are the primitive sixth and third roots
of unity; `A` and `A-1` are the two positive ones and differ by 1. The shipped `aux6` is the
positive root of `x^2-x+1` on twelve rings (55, 67, 118, 139, 195, 246, 58, 79, 318, 676, 248,
815) and, at `p = 8191` only, the order-three root `90` rather than the order-six root `91`.
Appendix D describes the rule as "the representative of smallest absolute value among the roots
of `Phi_{r*}` and their negatives", which matches `p=8191` but not the other twelve, where it
would give `A-1`. Both choices generate the same orbit closure and satisfy `2B < |A|`, so this
is an inconsistency in how the table was filled in, not a difference in what was measured.

Injectivity is checked against `p` before any interpolation, and the implementation refuses the
radix if it fails — that check is what fires at set 30 (3601 points, `p = 2917`).

## 4. The modulus chain

`sets.tsv` column 9 is the chain length *requested* from HElib: 1320 or 1500 bits at `h=12`,
and 839–1055 bits at `h=26`. HElib then adds its own special primes, so the chain it actually
builds is 467–527 bits longer at `h=12` and 294–352 bits longer at `h=26`. It reports the
result twice, once as a float and once rounded:

* `INFO: total bits = 1794.4` — the float, used as `log2Q` for the security estimate;
* `number of bits = 1795` — the integer, used as the "built" figure in `tab:offline` and as the
  `chain` column of `tab:e2e`.

Every security figure in the paper refers to the built chain, never the requested one. The
requested/built pairs are the `chain req./built` column of `final/tab_offline.tex`: 1320/1787,
1320/1795, 1500/2018, 1500/2027 at `h=12`, and 839/1133 up to 1055/1407 at `h=26`. The 1 bit of
slack between `tab:offline` (1795) and `tab:sec_full` (1794) on the same ring is this
integer-versus-float difference, not two different chains.

## 5. Security

### The two instances

A bootstrappable HElib instance carries two LWE problems, and the security of the set is the
smaller of the two.

| | dimension | modulus | secret |
|---|---|---|---|
| main key | `n = phi(m)` | `Q` = the built chain | `SparseTernary(h'=120)` |
| encapsulated key | `n = phi(m)` | `q_boot = q_ks * R` | `SparseTernary(h)`, `h` = 12 or 26 |

Error is `DiscreteGaussian(sigma = 3.2)`, HElib's default, and the number of samples is `m = n`.
`log2 q_boot` is read straight out of the run: it is the sum of the two lines

    final log2(qks) = 34.502003
    final log2(R)   = 26.886599

which for `p = 2971` gives 61.388602, the `log2qboot` field of `security/sets_all_h12.json`.
Across the `h=12` tier `log2 q_boot` runs from 61.39 (`p=2971`) to 70.59 (`p=60271`); at `h=26`
from 61.55 to 66.42.

### The six attacks

`security/estimate_security.py` runs six Lattice Estimator attacks on each instance and keeps
the minimum: `primal_usvp`, `primal_bdd`, `primal_hybrid`, `primal_hybrid` with `babai=False`
(`primal_hybrid_nb` below), `dual`, `dual_hybrid`. The reason both hybrid variants are run is in
the script's own comment: `LWE.primal_hybrid` does not optimise over the `babai` switch, and on
very sparse instances `babai=False` is several bits cheaper. Each attack's optimised `zeta`,
`eta` and `beta` are recorded alongside its cost in `security/est_*.json`.

Three things hold across all 44 instances, and can be read off `security/est_*.json`:

* The binding attack is `primal_hybrid_nb` on every instance, main and encapsulated, at both key
  weights. Nothing else ever wins.
* On the encapsulated instance the estimator returns no finite cost for `primal_usvp`,
  `primal_bdd`, `dual` or `dual_hybrid` at all — those entries are `null`, which is why the
  corresponding columns of `tab:sec_full` are dashes. The sparse secret is what makes them
  degenerate.
* Against `primal_usvp` on the *main* key, `primal_hybrid_nb` is 0.90–5.39 bits cheaper at
  `h=12` (smallest at `p=4513`, largest at `p=60271`) and 23.57–25.22 bits cheaper at `h=26`
  (smallest at `p=13457`, largest at `p=2917`). Appendix D attributes the 23.6–25.2 range to
  "the sparse encapsulated key at `h=26`"; in the data it is the main key on the `h=26` rings,
  and no uSVP figure for the encapsulated key exists to compare against.

`lambda* = min(main, encapsulated)`. The main key binds on 20 of the 22 rings. The two
exceptions are `p = 60271` and `p = 3307`, whose 2017–2026-bit chains push the main key to
95.1 and 94.6 bits while the encapsulated key sits at 93.1 and 93.9; there the `binding` field
of the JSON reads `encap`.

The rotated primal hybrid of eprint 2026/279 does not apply here. It exploits the coefficient
isometries of `Z_q[X]/(X^N+1)`, which is a power-of-two cyclotomic; every ring in this artifact
is `m = q1*q2` with two odd prime factors. The power-of-two contexts that do appear
(`results/raw_logs/sweep_po2_*.log`, `m = 2^16`) are stage-level harnesses that report
`security level = 5.4695` and carry no security claim.

### Re-running the estimate

The script needs a checkout of `github.com/malb/lattice-estimator` on `sys.path`, pointed to by
an environment variable; the manuscript pins commit `3e48ef4`.

```bash
git clone https://github.com/malb/lattice-estimator ~/lattice-estimator
git -C ~/lattice-estimator checkout 3e48ef4
export LATTICE_ESTIMATOR=~/lattice-estimator

cd newexp/security
# sanity check first: reproduces Ma et al.'s own Table 4, set V-A (82.3 / 136.8 / 82.3 bits)
python3 estimate_security.py --validate

# the h=12 tier, in slices, because a single instance takes 5-20 CPU-minutes
python3 estimate_security.py --sets sets_all_h12.json --slice 0:4  --out est_h12_slice0.json
python3 estimate_security.py --sets sets_all_h12.json --slice 4:8  --out est_h12_slice1.json
python3 estimate_security.py --sets sets_all_h12.json --slice 8:12 --out est_h12_slice2.json
python3 estimate_security.py --sets sets_all_h12.json --slice 12:  --out est_h12_slice3.json

# the h=26 tier; the file also carries the seventeenth h=12 ring (p=15377), which is why
# the first slice below mixes the two weights and the file is named the way it is
python3 estimate_security.py --sets sets_h26_and_28.json --slice 0:2 --out est_h26_slice0.json
python3 estimate_security.py --sets sets_h26_and_28.json --slice 2:4 --out est_h26_slice1.json
python3 estimate_security.py --sets sets_h26_and_28.json --slice 4:  --out est_h26_slice2.json
```

The `secs` field of each result records how long that instance took here: 708–1326 s for the
main key, 237–395 s for the encapsulated one. `--quick` drops to uSVP and dual only, which is
useful for a smoke test but does not reproduce the table, since the attack that binds is not in
that pair. The `.log` files next to each `.json` are the stdout of the runs that produced them.

To add a ring, append an entry to the JSON with `phim`, `log2Q` (the `total bits` float), `h`,
`hmain` (120) and `log2qboot` (`qks + R`), all read out of one completed run of that ring.

### Which rings reach 80 bits

At `h=12`, thirteen of the seventeen rings clear 80 bits at the chain that was built
(`lambda*` from `final/final_rows.json`):

    60271: 93.1   3307: 93.9   8101: 88.5   15377: 87.2   2971: 85.6   2917: 85.4
     4423: 84.5   65537: 82.6  2521: 82.4   8191: 81.9    13457: 81.9  19183: 81.1
    13807: 80.3

Four do not:

    14401: 77.4   6163: 76.2   37831: 70.8   4513: 70.7

The mechanism is visible in `tab:sec_full`: at a fixed chain the main key's security is governed
by `phi(m)`. The two rings at `phi(m) = 36960` (`p=37831` and `p=4513`) sit at 70.7–70.8 bits on
1786–1795-bit chains, while every ring with `phi(m) >= 44100` reaches 80–95 bits on chains of
1787–2027 bits. `p=14401` (`phi(m)=41140`) and `p=6163` (`phi(m)=40716`) fall in between.

The fix is to shorten the chain rather than to change the ring. Dropping roughly 250 bits off
the built chain restores 80 bits on all four, and shortens every evaluator's running time in
proportion, because the security of the main key at fixed `n` is monotone in `log2 Q`. The four
rings are reported in `tab:e2e` for completeness and marked there; they are not among the nine
sets of Table 3.

At `h=26` all five rings land at 129.8–131.0 bits on chains of 1133–1407 bits, with the main
key binding in every case.

## 6. Where the pipeline says no

Two failure modes are exercised by the shipped runs rather than argued about.

`p = 2917` at `h = 26`, set 30, order six. The closure needs 3601 points and `p` is 2917, so
the region cannot inject. The implementation detects this and says so:

    HELIB_ORDER6: box not injective at aux=248
    HELIB_ORDER6: unavailable at p=2917; falling back to the order-four path

Appendix D describes this as falling back to order four. In the shipped log
(`logs/set30_p2917_h26_pass1.log`, lines 366–372) the fallback does not survive: the next lines
are `ZZ_p: division by non-invertible element`, `Command terminated by signal 6`, `exit=134`,
and the same happens on the `ORDER6_COMPOSED` arm. The detection is correct and no reported
number depends on the fallback — set 30's row in `tab:e2e128` comes from the `ORDER4` and
`ORDER4_COMPOSED` arms of the same log, which complete and verify — but the fallback path
itself is broken, and a reviewer running set 30 with `HELIB_FILTER_ORDER=6` will get a core
dump, not a graceful degradation.

`p = 7 (mod 12)`, any `B`: no order-four radix exists, and the order-four evaluator reports
itself inapplicable rather than silently running the baseline. `../VERIFICATION.md` documents
the one occasion where that was not checked and a wrong speedup was nearly reported.
