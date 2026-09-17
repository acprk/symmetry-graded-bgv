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
# Environment: OURS_ROOT (default ../ours) is the root of the patched HElib tree, so
# that OURS_ROOT/fatboot-driver/build/fatboot is the driver built per ../ours/README.md;
# set FATBOOT directly to override that path. ZHAO_ROOT (default
# ../baselines/_upstream/artifact-helib) must contain a `build/` with the Zhao artifact
# already built per ../baselines/README.md.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOGDIR=${LOGDIR:-$HERE/logs}; mkdir -p "$LOGDIR"
ZH=${ZHAO_ROOT:-$HERE/../baselines/_upstream/artifact-helib}
O4=$(cd "${OURS_ROOT:-$HERE/../ours}" && pwd)
FATBOOT=${FATBOOT:-$O4/fatboot-driver/build/fatboot}
[ -x "$FATBOOT" ] || { echo "fatboot not built at $FATBOOT -- see ../ours/README.md, or set OURS_ROOT / FATBOOT" >&2; exit 1; }
# Serialise against any other driver run on this machine: capacity and wall-clock numbers
# are only comparable if nothing else is competing for cores. `pgrep -x` matches the process
# NAME exactly, not the command line, so this does not match the shell running this script
# (which `pgrep -f fatboot` did, and then waited on itself forever).
wait_idle(){ local n; n=$(basename "$FATBOOT"); while pgrep -x "$n" >/dev/null; do sleep 45; done; sleep 15; }

OUT=$LOGDIR/v_rerun_bsgs.log; : > "$OUT"
for MODE in MA_BASELINE ORDER4 COMPOSED; do
  wait_idle; cd "$O4"
  export HELIB_ZZX_CACHE_DIR=$PWD/cache/x; mkdir -p "$HELIB_ZZX_CACHE_DIR"
  unset HELIB_AUX_ORDER4_EVAL HELIB_COMPOSED_EVAL
  [ "$MODE" != "MA_BASELINE" ] && export HELIB_AUX_ORDER4_EVAL=1
  [ "$MODE" = "COMPOSED" ] && export HELIB_COMPOSED_EVAL=1
  echo "########## V :: $MODE :: bsgs-fixed thin t=-1 ##########" >>"$OUT"
  HELIB_EXPLICIT_AUX=256 timeout 7200 "$FATBOOT" \
    i=4 h=12 t=-1 newbts=1 newks=1 thick=0 repeat=1 >>"$OUT" 2>&1
  echo "exit=$? ($MODE)" >>"$OUT"
done

OUT2=$LOGDIR/zhao_thin24.log; : > "$OUT2"
if [ -x "$ZH/build/fatboot" ]; then
  for C in "IV 3" "V 4"; do set -- $C
    wait_idle; cd "$ZH/build"
    echo "########## $1 :: ZHAO thin h=24 t=1 (native path; sanity probe, not a head-to-head arm) ##########" >>"$OUT2"
    timeout 7200 ./fatboot i=$2 h=24 t=1 newbts=1 newks=1 thick=0 repeat=1 >>"$OUT2" 2>&1
    echo "exit=$? ($1)" >>"$OUT2"
  done
else
  echo "SKIPPED: Zhao et al.'s fatboot not found at $ZH/build/fatboot." >>"$OUT2"
  echo "         Run ../baselines/setup.sh and build it per ../baselines/README.md," >>"$OUT2"
  echo "         or set ZHAO_ROOT. This probe is independent of the three arms above." >>"$OUT2"
  cat "$OUT2" >&2
fi

# Offline norm-form density check (not timed; independent of the arms above).
# `normdens` is 06_density_validation.cpp in this directory; built here if missing.
# Set CXX if your default compiler's ABI does not match the NTL you have installed.
cd "$HERE"
CXX=${CXX:-g++}
if [ ! -x ./normdens ]; then
  echo "building normdens from 06_density_validation.cpp with $CXX ..." >&2
  "$CXX" -O2 -std=c++17 06_density_validation.cpp -o normdens -lntl -lgmp -pthread >&2 2>&1 || true
fi
if [ -x ./normdens ]; then
  ./normdens 8191   91    17 1 8190   8 > "$LOGDIR/census_8191.log"   2>&1
  ./normdens 131071 21906 17 1 131070 2 > "$LOGDIR/census_131071.log" 2>&1
else
  echo "SKIPPED density check: could not build ./normdens. It needs NTL and GMP; build it by hand with" >&2
  echo "  \$CXX -O2 -std=c++17 06_density_validation.cpp -o normdens -lntl -lgmp -pthread" >&2
  echo "This check is offline and independent of every timed arm above, so the log is still usable." >&2
fi
echo ALL DONE >> "$OUT"
