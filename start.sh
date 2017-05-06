#!/bin/sh
echo "Starting..."
num=`ps -ef | grep 'app.py' | grep -v grep | wc -l`
numOfLog=`cat ./log/log_number`
if [ $num == 0 ]
then
    while [ -e "./log/log_$numOfLog" ]
    do
        numOfLog=$(($numOfLog+1))
    done
    echo "$numOfLog" > ./log/log_number
    nohup python -u app.py 1>"./log/log_$numOfLog" 2>error &
    echo $! > ./app.pid
    echo 'Started!'
else
    echo 'Already running!'
fi
exit 0
