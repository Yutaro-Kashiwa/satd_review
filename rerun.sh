#! /bin/bash
project=$1
no=$2
echo "project: " $project
echo "no: "$no


cp /app/conf/for_deploy/$1.ini /app/conf/setting.ini
cd src
python -m exe.rerun.rerun $project $no