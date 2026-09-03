#!/bin/bash
# Sequential OFF/ON digit-extraction timing driver for new order-4 sets J..N.
# STRICTLY SEQUENTIAL by design (no &): concurrent runs contaminate order-4 ON timings.
set -u
BASE=/home/luck/xzy/0424project/order4bgv
BIN=$BASE/src/BGV-Boot-auxradix-opt/build_j/fatboot
OUT=$BASE/results/multi_p_new
DRV=$OUT/driver.log
mkdir -p "$OUT"
export HELIB_ZZX_CACHE_DIR=$BASE/cache/x
mkdir -p "$HELIB_ZZX_CACHE_DIR"
export LD_LIBRARY_PATH=/usr/local/lib:${LD_LIBRARY_PATH:-}

ts(){ date "+%Y-%m-%d %H:%M:%S"; }
log(){ echo "[$(ts)] $*" | tee -a "$DRV"; }

# idx  A     p
SETS=(
"9  95  4513"
"10 116 13457"
"11 71  2521"
"12 120 14401"
"13 124 15377"
)

log "=== DRIVER START pid=$$ (sequential OFF/ON, repeat=3) ==="
for entry in "${SETS[@]}"; do
  read -r IDX A P <<< "$entry"
  # OFF run
  OFFLOG="$OUT/p${P}_off_r3.log"
  log "BEGIN OFF  p=$P i=$IDX A=$A -> $OFFLOG"
  HELIB_EXPLICIT_AUX=$A "$BIN" i=$IDX h=12 t=-1 newbts=1 newks=1 thick=0 repeat=3 > "$OFFLOG" 2>&1
  log "END   OFF  p=$P i=$IDX rc=$?"
  # ON run
  ONLOG="$OUT/p${P}_on_r3.log"
  log "BEGIN ON   p=$P i=$IDX A=$A -> $ONLOG"
  HELIB_EXPLICIT_AUX=$A HELIB_AUX_ORDER4_EVAL=1 "$BIN" i=$IDX h=12 t=-1 newbts=1 newks=1 thick=0 repeat=3 > "$ONLOG" 2>&1
  log "END   ON   p=$P i=$IDX rc=$?"
done
log "=== DRIVER DONE ==="
