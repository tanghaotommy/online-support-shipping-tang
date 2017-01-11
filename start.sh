#!/bin/sh
if [ -e "nohup.out" ]
then
    rm nohup.out
fi
nohup python app.py &
echo $! > ./app.pid
exit 0
