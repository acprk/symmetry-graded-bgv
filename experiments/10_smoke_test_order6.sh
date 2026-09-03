#!/usr/bin/env bash
mkdir -p "${LOGDIR:-./logs}"
cd ${OURS_ROOT:-../ours}
export HELIB_ZZX_CACHE_DIR=$PWD/cache/x6b; mkdir -p $HELIB_ZZX_CACHE_DIR
export HELIB_EXPLICIT_AUX=90 HELIB_AUX_ORDER4_EVAL=1 HELIB_FILTER_ORDER=6
timeout 3000 src/BGV-Boot-auxradix-opt/build_o4/fatboot i=3 h=12 t=-1 newbts=1 newks=1 thick=0 repeat=1 \
  > ${LOGDIR:-./logs}/O6_smoke.log 2>&1
echo "exit=$?" >> ${LOGDIR:-./logs}/O6_smoke.log
