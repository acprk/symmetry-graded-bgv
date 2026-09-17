#!/usr/bin/env bash
# Run one pass of the sweep: every arm of every selected parameter set, sequentially.
#
#   newexp/run_batch.sh <pass> [idx ...] [ARMS=A,B,...] [H=<weight>]
#
#   SETS=<tsv>      parameter file to read      (default newexp/sets.tsv)
#   TIMEOUT=<secs>  per-run wall-clock limit    (default 5400, i.e. 90 minutes)
#   FATBOOT=<path>  driver binary               (default ours/fatboot-driver/build/fatboot)
#
# Examples:
#   newexp/run_batch.sh 1                                    # pass 1, all 15 rings of sets.tsv, all arms
#   newexp/run_batch.sh 2 14 16 22 27                        # pass 2 on the four repeated rings
#   SETS=newexp/sets128.tsv newexp/run_batch.sh 1 29 30 31 32 33 H=26
#   SETS=newexp/cases.tsv   newexp/run_batch.sh 1 3 4        # Ma et al.'s sets IV and V
#   newexp/run_batch.sh 1 17 ARMS=NORMONLY TIMEOUT=21600
#
# Output goes to newexp/logs/set<idx>_p<p>[_h<H>]_pass<pass>.log, appended, one
# "########## SET ..." banner per arm; collect.py parses exactly those banners.
set -u
ARTIFACT="${ARTIFACT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd "$ARTIFACT"
FATBOOT="${FATBOOT:-$ARTIFACT/ours/fatboot-driver/build/fatboot}"
[ -x "$FATBOOT" ] || { echo "driver not found: $FATBOOT (build it: see ours/README.md)" >&2; exit 1; }

PASS=${1:-1}; shift || true
ARMFILTER=""; HW=12
for a in "$@"; do case $a in ARMS=*) ARMFILTER=${a#ARMS=};; H=*) HW=${a#H=};; esac; done
SEL="${*//ARMS=*/}"; SEL="${SEL//H=*/}"
mkdir -p newexp/logs

while IFS=$'\t' read -r idx p pm m q1 q2 d ns bits aux4 aux6 arms; do
  [[ "$idx" =~ ^# ]] && continue
  [ -n "$SEL" ] && ! grep -qw "$idx" <<< "$SEL" && continue
  OUT=newexp/logs/set${idx}_p${p}_h${HW}_pass${PASS}.log
  [ "$HW" = 12 ] && OUT=newexp/logs/set${idx}_p${p}_pass${PASS}.log
  touch "$OUT"
  export HELIB_ZZX_CACHE_DIR=$ARTIFACT/newexp/cache/i${idx}; mkdir -p "$HELIB_ZZX_CACHE_DIR"
  IFS=',' read -ra ARMS <<< "$arms"
  for MODE in "${ARMS[@]}"; do
    [ -n "$ARMFILTER" ] && ! grep -qw "$MODE" <<< "$ARMFILTER" && continue
    . newexp/arms.sh                      # $MODE + aux4/aux6 -> $AUX and the HELIB_* flags
    echo "########## SET $idx p=$p m=$m d=$d :: $MODE :: aux=$AUX :: pass$PASS :: h=$HW :: $(date '+%F %T') ##########" >> "$OUT"
    /usr/bin/time -f "WALL=%e s MAXRSS=%M kB" timeout "${TIMEOUT:-5400}" \
      "$FATBOOT" i=$idx h=$HW t=-1 newbts=1 newks=1 thick=0 repeat=1 >> "$OUT" 2>&1
    echo "exit=$? ($MODE pass$PASS)" >> "$OUT"
  done
  echo "SET_DONE $idx" >> "$OUT"
done < "${SETS:-newexp/sets.tsv}"
