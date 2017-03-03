#!/bin/sh
echo "Starting..."
num=`ps -ef | grep 'app.py' | grep -v grep | wc -l`
if [ -e "log" ]
then
    rm log
fi
if [ $num == 0 ]
then
    nohup python -u app.py 1>log 2>error &
    echo $! > ./app.pid
    echo 'Started!'
else
    echo 'Already running!'
fi
exit 0
