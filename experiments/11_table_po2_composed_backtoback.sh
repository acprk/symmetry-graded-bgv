#!/usr/bin/env bash
mkdir -p "${LOGDIR:-./logs}"
set -u
O4=${OURS_ROOT:-../ours}
OUT=${LOGDIR:-./logs}/O6_backtoback.log; : > $OUT
for PASS in 1 2; do
for MODE in BASELINE ORDER6 ORDER6_COMPOSED; do
  cd $O4; export HELIB_ZZX_CACHE_DIR=$PWD/cache/x6b; mkdir -p "$HELIB_ZZX_CACHE_DIR"
  unset HELIB_AUX_ORDER4_EVAL HELIB_COMPOSED_EVAL HELIB_FILTER_ORDER
  export HELIB_EXPLICIT_AUX=90
  if [ "$MODE" != "BASELINE" ]; then export HELIB_AUX_ORDER4_EVAL=1 HELIB_FILTER_ORDER=6; fi
  [ "$MODE" = "ORDER6_COMPOSED" ] && export HELIB_COMPOSED_EVAL=1
  echo "########## O6BT pass$PASS :: $MODE ##########" >>$OUT
  timeout 5400 src/BGV-Boot-auxradix-opt/build_o4/fatboot i=3 h=12 t=-1 newbts=1 newks=1 thick=0 repeat=1 >>$OUT 2>&1
  echo "exit=$? ($MODE pass$PASS)" >>$OUT
done; done
echo O6BT_DONE >>$OUT
