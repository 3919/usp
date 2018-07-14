#!/bin/sh

ret=`python -c 'import sys; print("%i" % (sys.hexversion<0x03000000))'`
if [ $ret -eq 0 ]; then
    echo "we require python version <3"
    exit 1
else 
    echo "python version is <3"
fi

apt-get update
apt-get install python-netifaces
mkdir ./client/download

mkdir ./server/logs
mkdir ./server/settings
