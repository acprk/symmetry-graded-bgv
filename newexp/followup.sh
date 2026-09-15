#!/usr/bin/env bash
ARTIFACT="${ARTIFACT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd $ARTIFACT/ours
while ! grep -q "POOL DONE" newexp/logs/jobs.status 2>/dev/null; do sleep 300; done
echo "FOLLOWUP START $(date)" >> newexp/logs/jobs.status
# NORMONLY at h=26, 6 h budget each, all in parallel (~20 GB each); skip sets that already succeeded
for i in 31 32 30 33; do
  if ! grep -q "exit=0 (NORMONLY pass1)" newexp/logs/set${i}_p*_h26_pass1.log 2>/dev/null; then
    ( TIMEOUT=21600 SETS=newexp/sets128.tsv newexp/run_batch3.sh 1 $i ARMS=NORMONLY H=26; echo "FOLLOWUP normonly $i done $(date)" >> newexp/logs/jobs.status ) &
  fi
done
# set 29 (64 GB) and set 30 ORDER4, sequential in one worker
( SETS=newexp/sets128.tsv newexp/run_batch3.sh 1 29 ARMS=BASELINE,ORDER4,ORDER4_COMPOSED H=26;
  SETS=newexp/sets128.tsv newexp/run_batch3.sh 1 30 ARMS=ORDER4 H=26;
  TIMEOUT=21600 SETS=newexp/sets128.tsv newexp/run_batch3.sh 1 29 ARMS=NORMONLY H=26;
  echo "FOLLOWUP A done $(date)" >> newexp/logs/jobs.status ) &
wait
echo "FOLLOWUP DONE $(date)" >> newexp/logs/jobs.status
