#!/usr/bin/env bash
ARTIFACT="${ARTIFACT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd $ARTIFACT/ours
OUT=newexp/logs/smoke_i14_p3307.log; : > $OUT
export HELIB_ZZX_CACHE_DIR=$PWD/newexp/cache/i14; mkdir -p $HELIB_ZZX_CACHE_DIR
for MODE in BASELINE ORDER6 ORDER6_COMPOSED; do
  unset HELIB_AUX_ORDER4_EVAL HELIB_COMPOSED_EVAL HELIB_FILTER_ORDER
  export HELIB_EXPLICIT_AUX=58
  [ "$MODE" != "BASELINE" ] && export HELIB_AUX_ORDER4_EVAL=1 HELIB_FILTER_ORDER=6
  [ "$MODE" = "ORDER6_COMPOSED" ] && export HELIB_COMPOSED_EVAL=1
  echo "########## SMOKE i=14 :: $MODE :: $(date +%T) ##########" >> $OUT
  /usr/bin/time -f "WALL=%e s MAXRSS=%M kB" timeout 3600 fatboot-driver/build/fatboot i=14 h=12 t=-1 newbts=1 newks=1 thick=0 repeat=1 >> $OUT 2>&1
  echo "exit=$? ($MODE)" >> $OUT
done
echo SMOKE_DONE >> $OUT
