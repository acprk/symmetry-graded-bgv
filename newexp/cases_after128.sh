#!/usr/bin/env bash
ARTIFACT="${ARTIFACT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd $ARTIFACT/ours
while ! grep -q "tier128 pass done" newexp/logs/after_batch.status 2>/dev/null; do sleep 300; done
SETS=newexp/cases.tsv newexp/run_batch2.sh 1 3 4 H=12
echo "cases pass done $(date)" >> newexp/logs/after_batch.status
