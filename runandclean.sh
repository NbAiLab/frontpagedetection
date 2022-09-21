#!/bin/bash
if test $# -gt 1
then
echo "Usage:$0 <path to newspapers from production>"
exit
fi

if test $# -eq 1
then
PRODUCTIONDATADIR=$1
else
PRODUCTIONDATADIR="/nfsmounts/avisforsider/data"
fi

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
