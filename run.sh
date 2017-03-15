#!/bin/bash

outputFile=/mnt/dalla-hdd/dalla-stats/index.html
deviceLogDir=/mnt/dalla-hdd/dalla-stats/logs
userMapFile=/mnt/dalla-hdd/dalla-stats/user-map.csv

python3 dalla-reporter.py -d $deviceLogDir -u $userMapFile -o $outputFile
