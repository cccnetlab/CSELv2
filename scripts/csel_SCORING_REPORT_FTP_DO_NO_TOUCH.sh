#!/bin/sh
if [ ! -f "/usr/local/bin/name" ]; then
	exit
fi
HOST='#SERVER#'
USER='#USER#'
PASSWD='#PASSWORD#'
FILE='#FILENAME#'
cd /usr/local/bin/
echo 'Starting ftp'
ftp -n $HOST << END_SCRIPT
quote USER $USER
quote PASS $PASSWD
binary
put $FILE
quit
END_SCRIPT
echo 'Closing ftp'
exit 0
