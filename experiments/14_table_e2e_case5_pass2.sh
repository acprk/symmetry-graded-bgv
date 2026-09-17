#!/usr/bin/env bash
# Independent second pass of Table 5, Case V (see ../VERIFICATION.md rule 3: ratios
# are only trusted once they reproduce across independent, back-to-back sessions).
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGDIR=${LOGDIR:-$HERE/logs}; mkdir -p "$LOGDIR"
O4=$(cd "${OURS_ROOT:-$HERE/../ours}" && pwd)
FATBOOT=${FATBOOT:-$O4/fatboot-driver/build/fatboot}
[ -x "$FATBOOT" ] || { echo "fatboot not built at $FATBOOT -- see ../ours/README.md, or set OURS_ROOT / FATBOOT" >&2; exit 1; }

OUT=$LOGDIR/VERIFY_pass2.log; : > "$OUT"
for MODE in MA_BASELINE ORDER4 COMPOSED; do
  cd "$O4"; export HELIB_ZZX_CACHE_DIR=$PWD/cache/x; mkdir -p "$HELIB_ZZX_CACHE_DIR"
  unset HELIB_AUX_ORDER4_EVAL HELIB_COMPOSED_EVAL
  [ "$MODE" != "MA_BASELINE" ] && export HELIB_AUX_ORDER4_EVAL=1
  [ "$MODE" = "COMPOSED" ] && export HELIB_COMPOSED_EVAL=1
  echo "########## PASS2 V :: $MODE ##########" >>"$OUT"
  HELIB_EXPLICIT_AUX=256 timeout 3600 "$FATBOOT" \
    i=4 h=12 t=-1 newbts=1 newks=1 thick=0 repeat=1 >>"$OUT" 2>&1
  echo "exit=$? ($MODE)" >>"$OUT"
done
echo PASS2_DONE >>"$OUT"
