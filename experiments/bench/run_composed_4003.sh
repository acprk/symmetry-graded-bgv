#!/usr/bin/env bash
# Table 13 (`tab:composed`), row 4  ->  results/raw_logs/sweep_composed_4003.log
#
# The p=4003, m=209833 arm of run_composed.sh rerun on its own, at 24 threads, because it
# was the last arm of a long queue and shared the machine with another job the first time.
# Same binary, same parameters; the difference is only that it ran alone.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCH_BUILD=${BENCH_BUILD:-$HERE/build}
LOGDIR=${LOGDIR:-$HERE/logs}; mkdir -p "$LOGDIR"
TH=${THREADS:-24}

BD=$BENCH_BUILD/bench_m14
[ -x "$BD" ] || { echo "bench_m14 not built at $BD -- see README.md, or set BENCH_BUILD" >&2; exit 1; }

OUT=$LOGDIR/sweep_composed_4003.log; : > "$OUT"
echo "########## m=209833 p=4003 A=823 sup=hex ordr=6 bits=3000" >>"$OUT"
timeout 7200 "$BD" m=209833 p=4003 A=823 B=17 bits=3000 ordr=6 sup=hex \
   kaps="10,14,20" threads=$TH >>"$OUT" 2>&1; echo "exit=$?" >>"$OUT"
echo "########## m=209833 p=4003 A=823 sup=boxcl ordr=6 bits=3000" >>"$OUT"
timeout 7200 "$BD" m=209833 p=4003 A=823 B=17 bits=3000 ordr=6 sup=boxcl \
   kaps="10,14,20" threads=$TH >>"$OUT" 2>&1; echo "exit=$?" >>"$OUT"
echo ALL DONE >>"$OUT"
