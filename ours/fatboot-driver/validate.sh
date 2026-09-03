#!/bin/bash
# args: idx A p
cd /home/luck/xzy/0424project/order4bgv/src/BGV-Boot-auxradix-opt
idx=$1; A=$2; p=$3
mkdir -p /home/luck/xzy/0424project/order4bgv/results/multi_p_new/val
LOG=/home/luck/xzy/0424project/order4bgv/results/multi_p_new/val/val_i${idx}_p${p}.log
HELIB_EXPLICIT_AUX=$A ./build_j/fatboot i=$idx h=12 t=-1 newbts=1 newks=1 thick=0 repeat=1 > $LOG 2>&1
echo "VAL_DONE i=$idx p=$p rc=$?" >> $LOG
