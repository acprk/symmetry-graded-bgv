#!/usr/bin/env bash
ARTIFACT="${ARTIFACT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd $ARTIFACT/ours
while ! grep -q "POOL DONE" newexp/logs/jobs.status 2>/dev/null; do sleep 120; done
echo "FOLLOWUP2 START $(date)" >> newexp/logs/jobs.status
SETS=newexp/sets128.tsv newexp/run_batch3.sh 1 29 ARMS=BASELINE,ORDER4,ORDER4_COMPOSED H=26
SETS=newexp/sets128.tsv newexp/run_batch3.sh 1 30 ARMS=ORDER4 H=26
echo "FOLLOWUP2 DONE $(date)" >> newexp/logs/jobs.status
