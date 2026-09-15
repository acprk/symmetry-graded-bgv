# Extended parameter sweep: thin bootstrapping with order-6 / composed digit extraction

This directory contains everything needed to reproduce the extended comparison of
thin-bootstrapping digit extraction in HElib:

* `BASELINE`         – bounded-support odd filter of Ma et al. (generic Paterson–Stockmeyer on P_A)
* `ORDER4`           – order-four character filter (Xiong et al.), available for p ≡ 1 (mod 4)
* `ORDER4_COMPOSED`  – order-four filter + Galois norm-map evaluation of the folded Q
* `ORDER6`           – order-six (Eisenstein) filter on the box's orbit closure, p ≡ 1 (mod 3)
* `ORDER6_COMPOSED`  – order-six filter + Galois norm-map evaluation

All arms run the same binary (`fatboot-driver/build/fatboot`, HElib with the patches in `../patches`)
on the same ring, modulus chain, key weight (`h=12`) and auxiliary radix; only environment
variables differ. Every run is decrypted and checked slot by slot by the driver.

## Parameter sets (`sets.tsv`)

| idx | p | p mod 12 | m = q1·q2 | φ(m) | d | slots | chain bits (requested) | radix (order 4 / order 6) | arms |
|---|---|---|---|---|---|---|---|---|---|
| 14 | 2971  | 7 | 17·2917  = 49589 | 46656 | 4  | 11664 | 1320 | – / 55   | baseline, order-6, composed |
| 15 | 4423  | 7 | 11·4603  = 50633 | 46020 | 3  | 15340 | 1320 | – / 67   | baseline, order-6, composed |
| 16 | 13807 | 7 | 59·743   = 43837 | 43036 | 7  | 6148  | 1320 | – / 118  | baseline, order-6, composed |
| 17 | 19183 | 7 | 727·61   = 44347 | 43560 | 12 | 3630  | 1320 | – / 139  | baseline, order-6, composed |
| 18 | 37831 | 7 | 617·61   = 37637 | 36960 | 4  | 9240  | 1320 | – / 195  | baseline, order-6, composed |
| 19 | 60271 | 7 | 73·829   = 60517 | 59616 | 4  | 14904 | 1500 | – / 246  | baseline, order-6, composed |
| 20 | 3307  | 7 | 827·73   = 60371 | 59472 | 8  | 7434  | 1500 | – / 58   | baseline, order-6, composed |
| 21 | 6163  | 7 | 79·523   = 41317 | 40716 | 9  | 4524  | 1320 | – / 79   | baseline, order-6, composed |
| 22 | 14401 | 1 | 23·1871  = 43033 | 41140 | 11 | 3740  | 1320 | 120 / 318 | all five |
| 23 | 2521  | 1 | 97·523   = 50731 | 50112 | 18 | 2784  | 1500 | 71 / 676  | all five |
| 24 | 2917  | 1 | 1459·37  = 53983 | 52488 | 4  | 13122 | 1500 | 54 / 248  | all five |
| 25 | 4513  | 1 | 61·617   = 37637 | 36960 | 4  | 9240  | 1320 | 95 / 815  | all five |
| 26 | 8101  | 1 | 17·3049  = 51833 | 48768 | 8  | 6096  | 1320 | 90 / –    | baseline, order-4, composed |
| 27 | 13457 | 5 | 43·1051  = 45193 | 44100 | 7  | 6300  | 1320 | 116 / –   | baseline, order-4, composed |
| 28 | 15377 | 5 | 31·1789  = 55459 | 53640 | 4  | 13410 | 1500 | 124 / –   | baseline, order-4, composed |

Cases IV (p = 8191, m = 45193) and V (p = 65537, m = 50731) of the paper are presets `i=3` and `i=4`.

The radix is the small integer representative `A` of a root of Φ₄ (A² ≡ −1) or Φ₆ (A² ≡ A − 1)
modulo p with `A > 2B`; it is passed to HElib through `HELIB_EXPLICIT_AUX`. Hypercube generators
and orders (`gens`/`ords` in `fatboot.cpp`, presets 14–28) are CRT-aligned with `mvec = (q1, q2)`,
the second factor carrying the full Frobenius order, as HElib's `ThinEvalMap` requires.

## Running

```bash
newexp/run_batch.sh 1            # pass 1 over all sets, all arms, sequential
newexp/run_batch.sh 2 14 16 22   # pass 2 on a subset
python3 newexp/parse_logs.py     # one line per (set, arm, pass): times, capacity, security, degrees
```

Per-arm environment (set by the script):

| arm | HELIB_EXPLICIT_AUX | HELIB_AUX_ORDER4_EVAL | HELIB_FILTER_ORDER | HELIB_COMPOSED_EVAL |
|---|---|---|---|---|
| BASELINE        | A (order-4 radix if it exists, else order-6) | – | – | – |
| ORDER4          | A₄ | 1 | – | – |
| ORDER4_COMPOSED | A₄ | 1 | – | 1 |
| ORDER6          | A₆ | 1 | 6 | – |
| ORDER6_COMPOSED | A₆ | 1 | 6 | 1 |

Driver command for every arm: `fatboot i=<idx> h=12 t=-1 newbts=1 newks=1 thick=0 repeat=1`.

## Output

`logs/set<idx>_p<p>_pass<k>.log` holds the raw HElib output of every arm; the lines
`time for linear1 = ..., linear2 = ..., extract = ..., total = ...` and
`bits for ... after cap = ...` are the measurements, `security level = ...` and
`number of bits = ...` the chain HElib built and the level it reports for it.
