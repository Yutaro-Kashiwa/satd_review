#!/bin/bash

export LC_ALL=en_US.UTF-8
CWD=$PWD
DIR_SCRIPT=${CWD}/src
export PERL5LIB=${DIR_SCRIPT}
CODE_NAME=self_checker.py

#. ${DIR_SCRIPT}/util.sh


EXE_TIME=`date "+%Y%m%d%H%M%S"`
ERROR_LOGS=${CWD}/data_logs/ERROR_LOGS_${EXE_TIME}.txt


#今は引数は特に指定しない
python ${DIR_SCRIPT}/${CODE_NAME} openstack nova 0
python ${DIR_SCRIPT}/${CODE_NAME} openstack swift 0
python ${DIR_SCRIPT}/${CODE_NAME} openstack glance 0
python ${DIR_SCRIPT}/${CODE_NAME} qt qtquickcontrols 0  #> nohup1.out &
python ${DIR_SCRIPT}/${CODE_NAME} qt qtenginio 0
python ${DIR_SCRIPT}/${CODE_NAME} qt qtrepotools 0
python ${DIR_SCRIPT}/${CODE_NAME} qt qtx11extras 0
python ${DIR_SCRIPT}/${CODE_NAME} qt qtmacextras 0
python ${DIR_SCRIPT}/${CODE_NAME} qt qtsvg 0
python ${DIR_SCRIPT}/${CODE_NAME} qt qtbase 1 30000


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
