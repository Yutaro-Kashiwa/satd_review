#!/bin/bash

export LC_ALL=en_US.UTF-8
CWD=$PWD
DIR_SCRIPT=${CWD}/src
export PERL5LIB=${DIR_SCRIPT}

#. ${DIR_SCRIPT}/util.sh


EXE_TIME=`date "+%Y%m%d%H%M%S"`
ERROR_LOGS=${CWD}/data_logs/ERROR_LOGS_${EXE_TIME}.txt


#今は引数は特に指定しない
python ${DIR_SCRIPT}/self_checker.py $1 $2 $3 $4  #> nohup1.out &
#引数２つ以上が条件
#if [ $# -ge 4 ]; then
#  python ${DIR_SCRIPT}/ExtractComment2.py $3 $4 > nohup2.out &
#fi
#if [ $# -ge 6 ]; then
#  python ${DIR_SCRIPT}/ExtractComment2.py $5 $6 > nohup3.out &
#fi
#if [ $# -ge 8 ]; then
#  python ${DIR_SCRIPT}/ExtractComment2.py $7 $8 > nohup4.out &
#fi
#if [ $# -ge 10 ]; then
#python ${DIR_SCRIPT}/ExtractComment2.py $9 ${10} > nohup5.out &
#fi
#wait

#> ${CWD}/data_logs/repos.txt 2>&1
# &をつけて最後にwaitを入れれば並列実行できるよ
