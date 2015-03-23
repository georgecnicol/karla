#!/bin/bash
# George Nicol
# Often Karla forwards an email from a student who is requesting tutoring.
# This script will send a formletter to that student requesting that they
# provide contact info.
#
# You have to provide the ODIN id and the class number.
# an exterior email is option


OPTIND=1

class=""
odinID=""
email=""
formletter="/u/$USER/karla/data/karla_response_form_letter.txt"
theDate=`date`
myEmail=$USER@pdx.edu


usage(){
  echo "$0 -c 162 -i odinID"
  echo "$0 -c 163 -e student@foo.org"
  exit -1
}


if [[ ! -e $formletter ]]; then
  echo "$formletter not found."
  exit
fi



# do we have the right amount of args?
if [[ ($# > 4) || ($# < 4) ]]; then
  echo "not the right amount of args"
  usage
fi

while [[ $1 ]]; do
  case "$1" in
    -c)
      class=$2
      shift 2
      ;;
    -e)
      email=$2
      shift 2
      ;;
    -i)
      odinID=$2
      shift 2
      ;;
    --) # @ the end
      shift
      break
      ;;
    *) #no options
      break
      ;;
  esac
done

# we don't allow email and student id. we need one or the other
# and a class
if [[ ( ${#odinID} > 0 ) && ( ${#email} > 0 ) ]]; then
  usage
fi

# ensure class is valid
if [[ ( $class != "162" ) && ( $class != "163" ) && ( $class != "202" ) ]]; then
  echo "Classes are 162, 163 or 202"
  usage
fi

# ensure relatively valid email
if [[ ${#email} > 0 ]]; then
  if [[ $email != *@[A-Z0-9a-z]*\.[A-Za-z]* ]]; then
    echo "Valid email is name@thing.com"
    usage
  fi
fi


# user input is now sanitized from normal error
# main
# you can remove -b with email if you don't want to bcc yourself

cat $formletter | sed s/CLASS/$class/ > karlatempfile

if [[ ${odinID} > 0 ]]; then
  mailx -s "Tutoring for CS $class" -b $myEmail -r $myEmail $odinID@pdx.edu < karlatempfile
  echo "$odinID $theDate" >> /u/$USER/karla/data/SentEmails.log
else
  mailx -s "Tutoring for CS $class" -b $myEmail -r $myEmail $email <  karlatempfile
  echo "$email $theDate" >> /u/$USER/karla/data/SentEmails.log
fi

rm karlatempfile


