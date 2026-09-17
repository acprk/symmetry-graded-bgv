#!/usr/bin/env bash
# results/raw_logs/sweep_aligned65537.log  (quoted in the text; not a table row of its own)
#
# Aligned-ring comparison with fatboot (Ma et al.): OUR stage-level harness run at THEIR
# exact ring and prime: p=65537, m=50731 (d=18, nslots=2784), Gaussian box B=17 (|S|=1225,
# the support cardinality of their published p=65537 config), HElib bits=1500 (their
# fatboot run: total Q 2036 bits). A=256, since 256^2 = -1 mod 65537.
# Arms: r=4 (the selector's choice at p = 5 mod 12), r=2 (Ma's odd filter in our harness),
# r=1 (generic Paterson-Stockmeyer). Same machine as the fatboot reproduction.
#
# Note this log has NO composed arm: bench_m12 predates it. The composed number for this
# ring is the full recryption in results/raw_logs/v_rerun_bsgs.log -- see ../../README.md.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCH_BUILD=${BENCH_BUILD:-$HERE/build}
LOGDIR=${LOGDIR:-$HERE/logs}; mkdir -p "$LOGDIR"
TH=${THREADS:-16}

BD=$BENCH_BUILD/bench_m12
[ -x "$BD" ] || { echo "bench_m12 not built at $BD -- see README.md, or set BENCH_BUILD" >&2; exit 1; }

LOG=$LOGDIR/sweep_aligned65537.log; : > "$LOG"
M=50731; P=65537; A=256; B=17; BITS=1500
echo "=== aligned-ring run: p=65537 m=50731 (fatboot ring) box B=17 ===" | tee -a "$LOG"
date -Is | tee -a "$LOG"
run() {
  local tag=$1; shift
  echo "" | tee -a "$LOG"
  echo "########## $tag ##########" | tee -a "$LOG"
  timeout 7200 "$BD" "$@" threads=$TH m=$M p=$P A=$A B=$B bits=$BITS sup=box 2>&1 | tee -a "$LOG"
  echo "exit=$? for $tag" | tee -a "$LOG"
}
run "r4_box_aligned" ordr=4 kaps=18,14,22
run "r2_box_aligned" ordr=2 kaps=26,30,36
run "r1_box_aligned" ordr=1 kaps=40,44,48
date -Is | tee -a "$LOG"
