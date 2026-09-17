#!/usr/bin/env bash
# Table 12 (`tab:po2`), the four daggered rows  ->  results/raw_logs/sweep_po2_deep.log
#
# Deep baselines: r=2 and r=1 exhausted the noise budget at bits=2000 on m=2^16, which is
# itself the depth observation (they abort with `Decrypting with too much noise`). Rerun
# them at a longer chain so the ratio is measurable. This is a SEPARATE context, so the
# cross-context comparison is the MULTIPLICATION COUNT, not the wall clock -- which is why
# the daggered entries of Table 12 are counts read from here and times are not mixed
# across the two chains. `orbit=0` suppresses bench_m14's composed arm: these are
# scalar-axis reruns only.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCH_BUILD=${BENCH_BUILD:-$HERE/build}
LOGDIR=${LOGDIR:-$HERE/logs}; mkdir -p "$LOGDIR"
TH=${THREADS:-32}

BD=$BENCH_BUILD/bench_m14
[ -x "$BD" ] || { echo "bench_m14 not built at $BD -- see README.md, or set BENCH_BUILD" >&2; exit 1; }

OUT=$LOGDIR/sweep_po2_deep.log; : > "$OUT"
run(){ echo "" >>"$OUT"; echo "########## p=$1 sup=$3 ordr=$4 bits=$5" >>"$OUT"
       timeout 7200 "$BD" m=65536 p=$1 A=$2 B=17 bits=$5 ordr=$4 sup=$3 \
         kaps="20,26,34,44" threads=$TH orbit=0 >>"$OUT" 2>&1; echo "exit=$? (p=$1 r=$4)" >>"$OUT"; }
run 131071 21906 hex 2 3600
run 131071 21906 hex 1 3600
run   8191    91 hex 1 3600
run  65537   256 box 2 3600
run  65537   256 box 1 3600
echo ALL DONE >>"$OUT"
