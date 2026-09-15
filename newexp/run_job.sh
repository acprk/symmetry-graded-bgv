#!/usr/bin/env bash
# one job = one set, all its remaining passes, sequential; args: <setsfile> <idx> <H> <pass:ARMS>...
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SETS=$1; IDX=$2; HW=$3; shift 3
for spec in "$@"; do PASS=${spec%%:*}; ARMS=${spec#*:}; SETS=$SETS nice -n 5 newexp/run_batch2.sh $PASS $IDX ARMS=$ARMS H=$HW; done
echo "JOB_DONE set $IDX $(date)" >> newexp/logs/jobs.status
