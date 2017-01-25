#!/bin/sh
echo 'Stopping...'
PID=$(cat ./app.pid)
kill -9 $PID
echo 'Stopped!'
exit 0
