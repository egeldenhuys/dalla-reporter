#!/bin/bash

installDir=/mnt/dalla-hdd/dalla-reporter

while true
do
	echo "[$(date)] Parsing logs"
	$installDir/run.sh
	sleep 600
done
