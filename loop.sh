#!/bin/bash

installDir=/mnt/dalla-hdd/dalla-reporter
cd /mnt/dalla-hdd/dalla-stats

python3 -m http.server 80 &

cd $installDir

while true
do
	echo "[$(date)] Parsing logs"
	$installDir/run.sh
	sleep 3000
done
