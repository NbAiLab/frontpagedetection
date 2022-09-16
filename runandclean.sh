#!/bin/bash
if test $# -ne 0
then
echo "Usage:$0 "
exit
fi

antall=`find /nfsmounts/avisforsider/data -mindepth 1 -maxdepth 1 -type d -printf '1'  | wc -c`

if test ${antall} -gt 0
then
subdir=`echo $(date '+%d%m%Y')`

cd full
python bundlesimulation.py --masterpath /nfsmounts/avisforsider/data
cd ../top
python bundletopsimulation.py --masterpath /nfsmounts/avisforsider/data
cd ..
fi

if test -f  /nfsmounts/avisforsider/data/finished_top.status
then
if test -f  /nfsmounts/avisforsider/data/finished_full.status
then
echo "rm -rf /nfsmounts/avisforsider/data/*"
rm -rf /nfsmounts/avisforsider/data/*
fi
fi
