#!/usr/bin/env bash
ARTIFACT="${ARTIFACT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
# Usage: newexp/run_batch.sh <pass-number> [idx ...]   (default: all sets in sets.tsv)
cd $ARTIFACT/ours
PASS=${1:-1}; shift || true
ARMFILTER=""; HW=12; for a in "$@"; do case $a in ARMS=*) ARMFILTER=${a#ARMS=};; H=*) HW=${a#H=};; esac; done
SEL="${*//ARMS=*/}"; SEL="${SEL//H=*/}"
mkdir -p newexp/logs
while IFS=$'\t' read -r idx p pm m q1 q2 d ns bits aux4 aux6 arms; do
  [[ "$idx" =~ ^# ]] && continue
  if [ -n "$SEL" ] && ! grep -qw "$idx" <<< "$SEL"; then continue; fi
  OUT=newexp/logs/set${idx}_p${p}_h${HW}_pass${PASS}.log; [ "$HW" = 12 ] && OUT=newexp/logs/set${idx}_p${p}_pass${PASS}.log; touch $OUT
  export HELIB_ZZX_CACHE_DIR=$PWD/newexp/cache/i${idx}; mkdir -p $HELIB_ZZX_CACHE_DIR
  IFS=',' read -ra ARMS <<< "$arms"
  for MODE in "${ARMS[@]}"; do
    if [ -n "$ARMFILTER" ] && ! grep -qw "$MODE" <<< "$ARMFILTER"; then continue; fi
    unset HELIB_AUX_ORDER4_EVAL HELIB_COMPOSED_EVAL HELIB_FILTER_ORDER HELIB_EXPLICIT_AUX
    case $MODE in
      BASELINE)         AUX=${aux4/-/$aux6} ;;
      ORDER4)           AUX=$aux4; export HELIB_AUX_ORDER4_EVAL=1 ;;
      ORDER4_COMPOSED)  AUX=$aux4; export HELIB_AUX_ORDER4_EVAL=1 HELIB_COMPOSED_EVAL=1 ;;
      ORDER6)           AUX=$aux6; export HELIB_AUX_ORDER4_EVAL=1 HELIB_FILTER_ORDER=6 ;;
      ORDER6_COMPOSED)  AUX=$aux6; export HELIB_AUX_ORDER4_EVAL=1 HELIB_FILTER_ORDER=6 HELIB_COMPOSED_EVAL=1 ;;
      NORMONLY)         AUX=${aux4/-/$aux6}; export HELIB_AUX_ORDER4_EVAL=1 HELIB_FILTER_ORDER=1 HELIB_COMPOSED_EVAL=1 ;;
    esac
    export HELIB_EXPLICIT_AUX=$AUX
    echo "########## SET $idx p=$p m=$m d=$d :: $MODE :: aux=$AUX :: pass$PASS :: h=$HW :: $(date '+%F %T') ##########" >> $OUT
    /usr/bin/time -f "WALL=%e s MAXRSS=%M kB" timeout ${TIMEOUT:-5400} fatboot-driver/build/fatboot i=$idx h=$HW t=-1 newbts=1 newks=1 thick=0 repeat=1 >> $OUT 2>&1
    echo "exit=$? ($MODE pass$PASS)" >> $OUT
  done
  echo "SET_DONE $idx" >> $OUT
done < ${SETS:-newexp/sets.tsv}
echo BATCH_DONE > newexp/logs/batch_pass${PASS}.done
