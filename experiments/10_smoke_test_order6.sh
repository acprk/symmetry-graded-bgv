#!/usr/bin/env bash
# Correctness smoke test of the order-six construction at a Mersenne prime (set IV,
# p=8191), before trusting any timing from it. Run this first.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGDIR=${LOGDIR:-$HERE/logs}; mkdir -p "$LOGDIR"
O4=$(cd "${OURS_ROOT:-$HERE/../ours}" && pwd)
FATBOOT=${FATBOOT:-$O4/fatboot-driver/build/fatboot}
[ -x "$FATBOOT" ] || { echo "fatboot not built at $FATBOOT -- see ../ours/README.md, or set OURS_ROOT / FATBOOT" >&2; exit 1; }

cd "$O4"
export HELIB_ZZX_CACHE_DIR=$PWD/cache/x6b; mkdir -p "$HELIB_ZZX_CACHE_DIR"
export HELIB_EXPLICIT_AUX=90 HELIB_AUX_ORDER4_EVAL=1 HELIB_FILTER_ORDER=6
timeout 3000 "$FATBOOT" i=3 h=12 t=-1 newbts=1 newks=1 thick=0 repeat=1 \
  > "$LOGDIR/O6_smoke.log" 2>&1
echo "exit=$?" >> "$LOGDIR/O6_smoke.log"
