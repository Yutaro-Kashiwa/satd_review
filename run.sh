#! /bin/bash
project=$1
start=$2
stop=$3
worker=$4
echo "project: " $project
echo "start: "$start
echo "stop: "$stop
echo "worker: "$worker

cp /app/conf/for_deploy/$1.ini /app/conf/setting.ini
cd src
python -m exe._1_detect.run $project $start $stop $worker