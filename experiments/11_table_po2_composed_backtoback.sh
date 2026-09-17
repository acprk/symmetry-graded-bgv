#!/usr/bin/env bash
# Case IV (p=8191) back-to-back end-to-end arms: BASELINE / ORDER6 / ORDER6_COMPOSED,
# two passes, one context per arm  ->  results/raw_logs/O6_backtoback.log
#
# This is an END-TO-END thin-bootstrapping run of ../ours/, not the stage-level harness.
# It does NOT produce Tables 12 and 13; those are `bench/run_po2.sh`, `bench/run_po2_deep.sh`,
# `bench/run_composed.sh` and `bench/run_composed_4003.sh`. See bench/README.md.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGDIR=${LOGDIR:-$HERE/logs}; mkdir -p "$LOGDIR"
O4=$(cd "${OURS_ROOT:-$HERE/../ours}" && pwd)
FATBOOT=${FATBOOT:-$O4/fatboot-driver/build/fatboot}
[ -x "$FATBOOT" ] || { echo "fatboot not built at $FATBOOT -- see ../ours/README.md, or set OURS_ROOT / FATBOOT" >&2; exit 1; }

OUT=$LOGDIR/O6_backtoback.log; : > "$OUT"
for PASS in 1 2; do
for MODE in BASELINE ORDER6 ORDER6_COMPOSED; do
  cd "$O4"; export HELIB_ZZX_CACHE_DIR=$PWD/cache/x6b; mkdir -p "$HELIB_ZZX_CACHE_DIR"
  unset HELIB_AUX_ORDER4_EVAL HELIB_COMPOSED_EVAL HELIB_FILTER_ORDER
  export HELIB_EXPLICIT_AUX=90
  if [ "$MODE" != "BASELINE" ]; then export HELIB_AUX_ORDER4_EVAL=1 HELIB_FILTER_ORDER=6; fi
  [ "$MODE" = "ORDER6_COMPOSED" ] && export HELIB_COMPOSED_EVAL=1
  echo "########## O6BT pass$PASS :: $MODE ##########" >>"$OUT"
  timeout 5400 "$FATBOOT" i=3 h=12 t=-1 newbts=1 newks=1 thick=0 repeat=1 >>"$OUT" 2>&1
  echo "exit=$? ($MODE pass$PASS)" >>"$OUT"
done; done
echo O6BT_DONE >>"$OUT"
