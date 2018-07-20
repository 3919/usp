#!/bin/bash
echo "Hello in USP installer "

if [ "$EUID" -ne 0 ]
  then echo "WARNING, program requires package python-netifaces."
 	   echo "Install this package by yourself, or run this script "
 	   echo "with sudo"
fi

read -p "Type instllation folder path : " path
read -p "Type path to folder from which filles will be shared for other users: " sharedPath
read -p "Type path to folder where filles will be download from other users : " downloadPath
read -p "Nick visible for others in network : " NICK

path="$path/USP"
clientpath="$path/client"
serverpath="$path/server"

sharedFolderName="shared"
downloadFolderName="download"

if [ "$EUID" -eq 0 ]
	then apt-get update
		 apt-get install python-netifaces
fi

mkdir $path

mkdir $clientpath
mkdir $serverpath

cp  ./client/client.py $clientpath
cp  ./client/preferences.conf $clientpath

cp  ./server/main.py $serverpath
cp  ./server/FileServer.py $serverpath


mkdir "$serverpath/logs"
mkdir "$serverpath/settings"
mkdir "$clientpath/settings"

cSettingsFile="$clientpath/settings/settings.ini"
sSettingsFile="$serverpath/settings/settings.ini"

mkdir "$downloadPath/$downloadFolderName"
mkdir "$sharedPath/$sharedFolderName"

# createfile client settings.ini
touch $cSettingsFile
printf "[DOWNLOAD]\n" >> $cSettingsFile
printf "folder_path=$downloadPath \n" >> $cSettingsFile
printf "folder_name=$downloadFolderName\n" >> $cSettingsFile

# createfile server settings.ini
touch $sSettingsFile
printf "[main]\n" >> $sSettingsFile 
printf "shared_path=$sharedPath/$sharedFolderName\n" >> $sSettingsFile
printf "shared_name=$NICK\n" >> $sSettingsFile
