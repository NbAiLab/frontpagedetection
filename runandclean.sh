#!/bin/bash
if test $# -ne 0
then
echo "Usage:$0 "
exit
fi

PRODUCTIONDATADIR="/nfsmounts/avisforsider/data"


antall=`find ${PRODUCTIONDATADIR} -mindepth 1 -maxdepth 1 -type d -printf '1'  | wc -c`

if test ${antall} -gt 0
then
subdir=`echo $(date '+%d%m%Y')`

#cd full
python bundlesimulation.py --masterpath ${PRODUCTIONDATADIR}
#cd ../top
python bundletopsimulation.py --masterpath ${PRODUCTIONDATADIR}
#cd ..
fi

if test -f  ${PRODUCTIONDATADIR}/finished_top.status
then
if test -f  ${PRODUCTIONDATADIR}/finished_full.status
then
echo "rm -rf ${PRODUCTIONDATADIR}/*"
rm -rf ${PRODUCTIONDATADIR}/*
fi
fi
