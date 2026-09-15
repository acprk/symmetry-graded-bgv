#!/usr/bin/env bash
ARTIFACT="${ARTIFACT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
# waits for pass 1, rebuilds HElib+driver with the sign fix, reruns set 15, then pass 2 on representatives
cd $ARTIFACT/ours
while [ ! -f newexp/logs/batch_pass1.done ]; do sleep 60; done
echo "batch done $(date)" > newexp/logs/after_batch.status
( cd _build_case1/HElib-patched/build && make -j16 2>&1 | tail -2 && make install 2>&1 | tail -1 ) >> newexp/logs/after_batch.status 2>&1
( cd fatboot-driver/build && make 2>&1 | tail -1 ) >> newexp/logs/after_batch.status 2>&1
echo "rebuilt $(date)" >> newexp/logs/after_batch.status
mv newexp/logs/set15_p4423_pass1.log newexp/logs/set15_p4423_pass1_before_signfix.log
newexp/run_batch.sh 1 15
echo "set15 rerun done $(date)" >> newexp/logs/after_batch.status
newexp/run_batch.sh 2 14 16 22 27
echo "pass2 subset done $(date)" >> newexp/logs/after_batch.status
