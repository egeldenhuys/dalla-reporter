import argparse
import requests
import base64
import time
import os
from os import listdir
from os.path import isfile, join
import csv
import datetime
import logging
import sys
import calendar


version = 'v0.0.1'

def main():

	print('[INFO] Starting Dalla Reporter ' + version)

	parser = argparse.ArgumentParser()

	parser.add_argument("-d", "--log-directory", default='', help="Directory containing all device csv")
	parser.add_argument("-o", "--output-file", default='', help="File to save summary")
	parser.add_argument("-u", "--user-map", default='', help="user-map.csv")
	parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + version)

	args = parser.parse_args()

	deviceList = loadDeviceData(args.log_directory, 1490997600, 10000000000000)
	userDict, deviceToUserDict = loadUsers(args.user_map)

	associateDevicesToUser(deviceList, userDict, deviceToUserDict)
	userList = sortUsers(userDict)

	saveReport(userList, args.output_file)

class Device:
	def __init__(self, mac):
		self.mac = mac
		self.onPeak = 0
		self.offPeak = 0

class User:
	def __init__(self, name):
		self.name = name
		self.macList = []
		self.onPeak = 0
		self.offPeak = 0

def sortUsers(userDict):

	users = []

	for key, value in userDict.items():
		users.append(value)

	# take a user from the array
	for j in range(0, len(users)):
		for i in range(0, len(users) - 1):
			if (users[i].onPeak + users[i].offPeak < users[i + 1].onPeak + users[i + 1].offPeak):
			#if (users[i].onPeak < users[i + 1].onPeak):
				# swap
				tmp = users[i]
				users[i] = users[i + 1]
				users[i + 1] = tmp

	return users

def saveReport(userList, reportFile):

	title = 'Total'
	scale = 0.000000954
	scaleStr = 'MiB'
	points = 2

	timeKey = int(time.time()) # UTC TIME!
	localTime = time.localtime(timeKey)
	year = localTime.tm_year
	month = localTime.tm_mon

	totalDays = calendar.monthrange(year, month)[1]

	maxOn = -1
	maxOff = -1

	userCount = 10

	# Bytes
	if (title == "Total"):
		maxOn = float(400 * 1073741824) / userCount
		maxOff = float(1000 * 1073741824) / userCount
	elif (title == "Today"):

		maxOn = ((float(400) / totalDays) / userCount) * 1073741824
		maxOff = float(1000 * 1073741824) / totalDays / userCount

	if not os.path.exists(os.path.dirname(reportFile)):
		os.makedirs(os.path.dirname(reportFile))

	overviewFile = open(reportFile, 'w')


	overviewFile.write('<!DOCTYPE html>\n<html>\n<head><style>body{font-family:courier, monospace;}</style><title>Dalla Stats</title></head>\n<body>\n')

	overviewFile.write('<h1>' + title + '</h1>\n')
	# overviewFile.write('<p>Sorted according to highest On-Peak usage</p>\n')
	# overviewFile.write("<a href=/index.html>Today</a><br>\n<br>\n")
	# overviewFile.write("<a href=/total.html>Total</a><br>\n")
	overviewFile.write('<p>\n')

	overviewFile.write('dalla-reporter ' + version + '<br>\n\n')

	overviewFile.write(time.strftime('%c', localTime))

	overviewFile.write('<br>\n<br>\n')

	for user in userList:
		name = user.name
		total = user.onPeak + user.offPeak
		onPeak = user.onPeak
		offPeak = user.offPeak

		if (name == 'TOTAL'):
			onPerc = round((float(onPeak) / (maxOn * userCount)) * 100, 2)
			offPerc = round((float(offPeak) / (maxOff * userCount)) * 100, 2)
		else:
			onPerc = round(float(onPeak) / maxOn)
			onPerc = round((float(onPeak) / maxOn) * 100, 2)
			offPerc = round((float(offPeak) / maxOff) * 100, 2)

		overviewFile.write('=======<br>\n' + name + "<br>\n=======<br>\n")
		overviewFile.write('Total : ' + str(round(total * scale, points)) + ' ' + scaleStr + '<br>\n')
		overviewFile.write('On-Peak : ' + str(round(onPeak * scale, points)) + ' ' + scaleStr)
		overviewFile.write(' (' + str(onPerc) + '%)<br>\n')
		overviewFile.write('Off-Peak : ' + str(round(offPeak * scale, points)) + ' ' + scaleStr)
		overviewFile.write(' (' + str(offPerc) + '%)<br>\n<br>\n')

	overviewFile.write('</p>\n</body>\n</html>')

	overviewFile.close()

'''
Associate Devices To Users:
	- For each device
	- If the MAC exists in the dict, add the counters
	- Else add to the unknown user
'''

def associateDevicesToUser(deviceList, userDict, deviceToUserDict):
	print('Associating devices to users...')
	for device in deviceList:
		userDict['TOTAL'].offPeak += device.offPeak
		userDict['TOTAL'].onPeak += device.onPeak

		if device.mac in deviceToUserDict:
			userDict[deviceToUserDict[device.mac]].offPeak += device.offPeak
			userDict[deviceToUserDict[device.mac]].onPeak += device.onPeak
		else:
			userDict['UNKNOWN'].offPeak += device.offPeak
			userDict['UNKNOWN'].onPeak += device.onPeak

	# for key, value in userDict.items():
	# 	print(value.onPeak)

'''
Load Users:
	- Open the user map csv
	- For each user, create a struct with the given name and MACs
	- Initialise counters
	- Create MAC -> User entry in dict and return the dict
	- Create "Unknown" -> Unknown user struct
'''

def loadUsers(userMapFile):
	print('Loading users...')
	userDict = {}
	macToUserMap = {}

	if (os.path.isfile(userMapFile) == False):
		print('User map file not found!')
		exit(-1)
		return userDict, macToUserMap

	inputFile = open(userMapFile)
	reader = csv.reader(inputFile, delimiter=',', skipinitialspace=True)
	initial = True

	userDict['UNKNOWN'] = User("UNKNOWN")
	userDict['TOTAL'] = User('TOTAL')

	for row in reader:
		if initial:
			initial = False
			continue

		if str(row[0]) in userDict:
			userDict[str(row[0])].macList.append(str(row[1]))
		else:
			userDict[str(row[0])] = User(str(row[0]))
			userDict[str(row[0])].macList.append(str(row[1]))

		macToUserMap[str(row[1])] = str(row[0])

		# print(row[0])
		# print(row[1])

	# for key, value in macToUserMap.items():
	# 	print(key)
	# 	print(value)

	return userDict, macToUserMap

def getMacFromFileName(name):
	result = name.split('_')
	result = result[0].replace('-', ':')

	return result

def loadDeviceData(deviceLogDir, start, end):
	print('Loading devices...')

	deviceList = []

	if (not os.path.exists(deviceLogDir)):
		print('Log directory not found!')
		exit(-1)
		return deviceList

	fileList = [f for f in listdir(deviceLogDir) if isfile(join(deviceLogDir, f))]

	for deviceLog in fileList:
		mac = getMacFromFileName(deviceLog)
		device = Device(mac)

		initial = True
		prevTotalBytes = 0

		with open(deviceLogDir + '/' + deviceLog, 'r') as csvfile:
			inputFile = csv.reader(csvfile, delimiter=',', skipinitialspace=True)

			# Skip header
			for row in inputFile:
				if initial:
					initial = False
					continue
				# 0 = time stamp
				# 1 = total Bytes



				local = time.localtime(int(row[0]))
				delta = int(row[1]) - prevTotalBytes

				if delta < 0:
					# print('Negative Delta')
					# print(delta)
					# print('Correcting to')
					# print(int(row[1]))

					delta = int(row[1])
					prevTotalBytes = int(row[1])

				else:
					prevTotalBytes = int(row[1])

				if int(row[0]) > start and int(row[0]) < end:
					if (local.tm_hour < 6):
						device.offPeak += delta
					else:
						device.onPeak += delta

		deviceList.append(device)

	return deviceList

main()

'''
Device Struct:
	- MAC
	- On Peak Total
	- Off Peak Total

User Struct:
	- Name
	- MAC[]
	- On Peak Total
	- Off Peak Total

User Map Dict:
	- MAC = User Struct

Load Device Data:
	- Specify the start and end times
	- If the data in in range, process it, else move on
	- Open each CSV file in the given Directory
	- Create a new device struct with the MAC from the file
	- Go through each csv row and calculate delta
		- If delta < 0, delta = 0
	- If on peak, add to on peak counter, else off peak
	- Return array of device structs


Save Report:
	- For each user
	- Write their totals to a file
'''


# DEVICE:
# PROCESS DEVICE DATA
# Open each device csv file
# Start at first row, read until end
# Calculate the delta.
# 	If delta is negative, set delta = 0 for that row
# Add the delta to a running counter for that file

# Use a Dict:
# 	MAC = Cumulative delta

# LOAD USER MAP
# USER:
#	- Name
# 	- Devices[]

# SAVE SUMMARY
# user -> [Mac...]
