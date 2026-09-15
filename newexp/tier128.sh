#!/usr/bin/env bash
ARTIFACT="${ARTIFACT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd $ARTIFACT/ours
while ! grep -q "normonly pass done" newexp/logs/after_batch.status 2>/dev/null; do sleep 180; done
( cd fatboot-driver/build && make 2>&1 | tail -1 ) >> newexp/logs/after_batch.status 2>&1
SETS=newexp/sets128.tsv newexp/run_batch2.sh 1 29 30 31 32 33 H=26
echo "tier128 pass done $(date)" >> newexp/logs/after_batch.status
