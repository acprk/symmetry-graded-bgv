#!/usr/bin/env bash
# The Case IV row (p=8191) of Tables 4 and 11: BASELINE / ORDER6 / ORDER6_COMPOSED,
# back to back, two passes  ->  results/raw_logs/ORDER6_case4.log
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGDIR=${LOGDIR:-$HERE/logs}; mkdir -p "$LOGDIR"
O4=$(cd "${OURS_ROOT:-$HERE/../ours}" && pwd)
FATBOOT=${FATBOOT:-$O4/fatboot-driver/build/fatboot}
[ -x "$FATBOOT" ] || { echo "fatboot not built at $FATBOOT -- see ../ours/README.md, or set OURS_ROOT / FATBOOT" >&2; exit 1; }

OUT=$LOGDIR/ORDER6_case4.log; : > "$OUT"
for PASS in 1 2; do
for MODE in BASELINE ORDER6 ORDER6_COMPOSED; do
  cd "$O4"; export HELIB_ZZX_CACHE_DIR=$PWD/cache/x6; mkdir -p "$HELIB_ZZX_CACHE_DIR"
  unset HELIB_AUX_ORDER4_EVAL HELIB_COMPOSED_EVAL HELIB_FILTER_ORDER
  if [ "$MODE" != "BASELINE" ]; then export HELIB_AUX_ORDER4_EVAL=1 HELIB_FILTER_ORDER=6; fi
  [ "$MODE" = "ORDER6_COMPOSED" ] && export HELIB_COMPOSED_EVAL=1
  echo "########## ORDER6 pass$PASS :: $MODE ##########" >>"$OUT"
  timeout 5400 "$FATBOOT" \
    i=3 h=12 t=-1 newbts=1 newks=1 thick=0 repeat=1 >>"$OUT" 2>&1
  echo "exit=$? ($MODE pass$PASS)" >>"$OUT"
done; done
echo ORDER6_DONE >>"$OUT"
