#!/bin/bash

outputFile=/mnt/dalla-hdd/http/index.html
deviceLogDir=/mnt/dalla-stats/logs
userMapFile=/mnt/dalla-stats/user-map.csv

python3 dalla-reporter.py -d $deviceLogDir -u $userMapFile -o $outputFile
