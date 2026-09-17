#!/usr/bin/env bash
# Table 12 (`tab:po2`), the 2000-bit rows  ->  results/raw_logs/sweep_po2_ma_sets.log
#
# Family A: POWER-OF-TWO rings, on the state of the art's OWN sets. Ma et al.
# (ASIACRYPT'24) Table 2 uses m=2^16 with p in {65537, 8191, 131071}.
#   p=65537  = 5 mod 12 : order-4 exists, order-6 does not      -> r*=4   (control)
#   p=8191   = 7 mod 12 : NO order-4 exists, order-6 does       -> r*=6
#   p=131071 = 7 mod 12 : NO order-4 exists, order-6 does       -> r*=6
# All arms of one prime share one context (ring, modulus, key) and one support, so only
# the folding group varies: the ratios are controlled head-to-head measurements.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCH_BUILD=${BENCH_BUILD:-$HERE/build}
LOGDIR=${LOGDIR:-$HERE/logs}; mkdir -p "$LOGDIR"
# 32 was the core count of the measurement machine; override for yours.
TH=${THREADS:-32}

BD=$BENCH_BUILD/bench_m13
[ -x "$BD" ] || { echo "bench_m13 not built at $BD -- see README.md, or set BENCH_BUILD" >&2; exit 1; }

M=65536; BITS=2000; B=17; KAPS=${KAPS:-"8,10,12,16,20,26"}
OUT=$LOGDIR/sweep_po2_ma_sets.log; : > "$OUT"
run(){ echo "" >>"$OUT"; echo "########## p=$1 sup=$3 ordr=$4" >>"$OUT"
       timeout 5400 "$BD" m=$M p=$1 A=$2 B=$B bits=$BITS ordr=$4 sup=$3 \
         kaps="$KAPS" threads=$TH >>"$OUT" 2>&1; echo "exit=$? (p=$1 $3 r=$4)" >>"$OUT"; }

# --- p=131071 (= 7 mod 12, d=2, 16384 slots): order-6 is the ONLY high-order filter ---
for R in 6 3 2 1; do run 131071 21906 hex $R; done
run 131071 21906 boxcl 6          # same claim on the honest infinity-norm box

# --- p=8191 (= 7 mod 12, d=8, 4096 slots) ---
for R in 6 3 2 1; do run 8191 91 hex $R; done
run 8191 91 boxcl 6

# --- p=65537 (= 5 mod 12, d=1): control, order-4 does exist here ---
for R in 4 2 1; do run 65537 256 box $R; done
echo "ALL DONE" >>"$OUT"
