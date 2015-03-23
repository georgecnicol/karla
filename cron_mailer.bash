#!/bin/bash
# George Nicol
# searchs file for date, and then sends reminder email.
# date is 'tomorrow'

currentDate=`date`
fileToLookIn="/u/$USER/karla/data/scheduled_appointments.txt"
emailLog="/u/$USER/karla/data/SentEmails.log"
tempFile="/u/$USER/karla/data/tempfile.txt"
dateToFind=`date +%m/%d --date="+1 day"`
emailAddr="$USER@pdx.edu"

if [[ ! -e $fileToLookIn ]]; then
  echo "Can't find scheduled_appointments.txt in /u/$USER/karla/data"
  exit
fi


if [[ ! -e $emailLog ]]; then
  echo "Can't find SentEmails.log in /u/$USER/karla/data"
  exit
fi

# match the date? if so send mail. Note, you can't run shell commands directly from inside awk (like mailx)
awk -v date2find="$dateToFind" 'BEGIN { FS = "," } ; ( $3 ~ date2find ) ' $fileToLookIn >> $tempFile
awk -v theDate="$currentDate"  'BEGIN { FS = "," } ; { print $2 " " theDate } ' $tempFile >> $emailLog

while read line; do
  studentName=`echo $line | awk -F, '{ print $1 }'`
  studentEmail=`echo $line | awk -F, '{ print $2 }'`
  TCSSname=`echo $line | awk -F, '{ print $8  }'`
  TCSSemail=`echo $line | awk -F, '{ print $9 }'`
  APdate=`echo $line | awk -F, '{ print $3 }'`
  APtime=`echo $line | awk -F, '{ print $5 }'`
  APdow=`echo $line | awk -F, '{ print $4 }'`
  APloc=`echo $line | awk -F, '{ print $6 }'`
  APclass=`echo $line | awk -F, '{ print $7 }'`

  echo "As a reminder, $studentName has a tutoring appointment at $APtime on $APdow, $APdate in $APloc with $TCSSname" |\
    mailx -s "Reminder for tutoring - CS $APclass" -b $TCSSemail -r $emailAddr $studentEmail

done < $tempFile
rm $tempFile




