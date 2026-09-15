#!/usr/bin/env bash
# Usage: newexp/run_batch.sh <pass> [idx ...] [ARMS=A,B]
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PASS=${1:-1}; shift || true
ARMFILTER=""; for a in "$@"; do case $a in ARMS=*) ARMFILTER=${a#ARMS=};; esac; done
SEL="${*//ARMS=*/}"
mkdir -p newexp/logs
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
while IFS=$'\t' read -r idx p pm m q1 q2 d ns bits aux4 aux6 arms; do
  [[ "$idx" =~ ^# ]] && continue
  if [ -n "$SEL" ] && ! grep -qw "$idx" <<< "$SEL"; then continue; fi
  OUT=newexp/logs/set${idx}_p${p}_pass${PASS}.log; touch $OUT
  export HELIB_ZZX_CACHE_DIR=$PWD/newexp/cache/i${idx}; mkdir -p $HELIB_ZZX_CACHE_DIR
  IFS=',' read -ra ARMS <<< "$arms"
  for MODE in "${ARMS[@]}"; do
    if [ -n "$ARMFILTER" ] && ! grep -qw "$MODE" <<< "$ARMFILTER"; then continue; fi
    . newexp/arms.sh
    echo "########## SET $idx p=$p m=$m d=$d :: $MODE :: aux=$AUX :: pass$PASS :: $(date '+%F %T') ##########" >> $OUT
    /usr/bin/time -f "WALL=%e s MAXRSS=%M kB" timeout 5400 fatboot-driver/build/fatboot i=$idx h=12 t=-1 newbts=1 newks=1 thick=0 repeat=1 >> $OUT 2>&1
    echo "exit=$? ($MODE pass$PASS)" >> $OUT
  done
  echo "SET_DONE $idx" >> $OUT
done < newexp/sets.tsv
echo BATCH_DONE > newexp/logs/batch_pass${PASS}.done
