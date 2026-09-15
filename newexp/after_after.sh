#!/usr/bin/env bash
ARTIFACT="${ARTIFACT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
cd $ARTIFACT/ours
while ! grep -q "pass2 subset done" newexp/logs/after_batch.status 2>/dev/null; do sleep 120; done
newexp/run_batch.sh 1 14 16 17 18 19 20 21 22 23 24 25 26 27 28 ARMS=NORMONLY
echo "normonly pass done $(date)" >> newexp/logs/after_batch.status
