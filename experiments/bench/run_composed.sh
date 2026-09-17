#!/usr/bin/env bash
# Table 13 (`tab:composed`), rows 1-3  ->  results/raw_logs/sweep_composed.log
#
# Composed (r,d) measurements: the interior of the grading, for the FIRST time at r=6.
#   p=131071, m=2^16  : power-of-two ring, d=2,  16384 slots, p=7 mod 12 (no order-4 exists)
#   p=8191,   m=2^16  : power-of-two ring, d=8,   4096 slots, p=7 mod 12 (no order-4 exists)
#   p=4003,   m=209833: general ring,      d=6,  32280 slots, p=7 mod 12
# Each run reports RESULT (scalar axis only) and ORBIT (composed) in ONE context, so the
# two arms of a row are head to head by construction.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCH_BUILD=${BENCH_BUILD:-$HERE/build}
LOGDIR=${LOGDIR:-$HERE/logs}; mkdir -p "$LOGDIR"
TH=${THREADS:-32}

BD=$BENCH_BUILD/bench_m14
[ -x "$BD" ] || { echo "bench_m14 not built at $BD -- see README.md, or set BENCH_BUILD" >&2; exit 1; }

OUT=$LOGDIR/sweep_composed.log; : > "$OUT"
run(){ echo "" >>"$OUT"
       echo "########## m=$1 p=$2 A=$3 sup=$4 ordr=$5 bits=$6" >>"$OUT"
       timeout 7200 "$BD" m=$1 p=$2 A=$3 B=17 bits=$6 ordr=$5 sup=$4 \
         kaps="$7" threads=$TH >>"$OUT" 2>&1; echo "exit=$? (m=$1 p=$2 r=$5)" >>"$OUT"; }

# --- power-of-two rings, r=6 composed (the headline construction) ---
run 65536 131071 21906 hex   6 2000 "10,14,20"
run 65536 131071 21906 boxcl 6 2000 "10,14,20"
run 65536 131071 21906 hex   2 2000 "14,20,26"    # prior art on this class
run 65536   8191    91 hex   6 2000 "10,14,20"
run 65536   8191    91 hex   2 2000 "14,20,26"
# --- general ring, r=6 composed ---
run 209833  4003   823 hex   6 3000 "10,14,20"
run 209833  4003   823 hex   2 3000 "14,20,26"
echo "ALL DONE" >>"$OUT"
