#!/usr/bin/env bash
# Table 5 (Case V) end-to-end queue: (1) three aux-path arms of our patched HElib,
# back-to-back, with the BSGS-not-Horner fix applied (capacity numbers are only
# meaningful with this fix -- see ../VERIFICATION.md rule 4 and
# ../ours/dev_history/patch_bsgs_fix.py for what it changed and why); (2) the Zhao
# et al. artifact run at its OWN native configuration (h=24, t=1), as a same-session
# sanity probe, not as a head-to-head arm (their native path is thick bootstrapping,
# ours is thin -- see ../baselines/README.md); (3) an offline norm-form density check
# via the standalone tool of 06_density_validation.cpp, unrelated to the timed arms.
#
# Environment: OURS_ROOT (default ../ours) must be the built fatboot driver's parent
# directory; ZHAO_ROOT (default ../baselines/_upstream/artifact-helib) must contain a
# `build/` with the Zhao artifact already built per ../baselines/README.md.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGDIR=${LOGDIR:-$HERE/logs}; mkdir -p "$LOGDIR"
ZH=${ZHAO_ROOT:-../baselines/_upstream/artifact-helib}
O4=${OURS_ROOT:-../ours}
wait_idle(){ while pgrep -f "fatboot" >/dev/null; do sleep 45; done; sleep 15; }

OUT=$LOGDIR/v_rerun_bsgs.log; : > "$OUT"
for MODE in MA_BASELINE ORDER4 COMPOSED; do
  wait_idle; cd "$O4"
  export HELIB_ZZX_CACHE_DIR=$PWD/cache/x; mkdir -p "$HELIB_ZZX_CACHE_DIR"
  unset HELIB_AUX_ORDER4_EVAL HELIB_COMPOSED_EVAL
  [ "$MODE" != "MA_BASELINE" ] && export HELIB_AUX_ORDER4_EVAL=1
  [ "$MODE" = "COMPOSED" ] && export HELIB_COMPOSED_EVAL=1
  echo "########## V :: $MODE :: bsgs-fixed thin t=-1 ##########" >>"$OUT"
  HELIB_EXPLICIT_AUX=256 timeout 7200 src/BGV-Boot-auxradix-opt/build_o4/fatboot \
    i=4 h=12 t=-1 newbts=1 newks=1 thick=0 repeat=1 >>"$OUT" 2>&1
  echo "exit=$? ($MODE)" >>"$OUT"
done

OUT2=$LOGDIR/zhao_thin24.log; : > "$OUT2"
for C in "IV 3" "V 4"; do set -- $C
  wait_idle; cd "$ZH/build"
  echo "########## $1 :: ZHAO thin h=24 t=1 (native path; sanity probe, not a head-to-head arm) ##########" >>"$OUT2"
  timeout 7200 ./fatboot i=$2 h=24 t=1 newbts=1 newks=1 thick=0 repeat=1 >>"$OUT2" 2>&1
  echo "exit=$? ($1)" >>"$OUT2"
done

# Offline norm-form density check (not timed; independent of the arms above).
# Build first: g++ -O2 -std=c++17 06_density_validation.cpp -o normdens -lntl -lgmp -pthread
cd "$HERE"
if [ -x ./normdens ]; then
  ./normdens 8191   91    17 1 8190   8 > "$LOGDIR/census_8191.log"   2>&1
  ./normdens 131071 21906 17 1 131070 2 > "$LOGDIR/census_131071.log" 2>&1
else
  echo "normdens not built; run: g++ -O2 -std=c++17 06_density_validation.cpp -o normdens -lntl -lgmp -pthread" >&2
fi
echo ALL DONE >> "$OUT"
