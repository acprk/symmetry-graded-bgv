#!/usr/bin/env bash
cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "POOL START $(date)" >> newexp/logs/jobs.status
xargs -P 4 -L 1 newexp/run_job.sh < newexp/jobs.txt
echo "POOL DONE $(date)" >> newexp/logs/jobs.status
echo "normonly pass done (pool) $(date)" >> newexp/logs/after_batch.status
echo "tier128 pass done (pool) $(date)" >> newexp/logs/after_batch.status
echo "cases pass done (pool) $(date)" >> newexp/logs/after_batch.status
