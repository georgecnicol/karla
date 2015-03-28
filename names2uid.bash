#!/bin/bash
# George Nicol
# March 28, 2015
# reads list of common names from a file
# output is those same names plus their corresponding uid(s) to stdout


usage()
{
  echo "$0 /path/to/file"
  echo "performs ldapsearch on list of names provided in file"
  echo "output to stdout"
  exit
}


if [[ $# != 1 ]] ; then
  usage
fi

if [[ ! -e $1 ]] ; then
  usage
fi

while read line; do
  echo $line
  ldapsearch -xLLL "cn=$line" | grep uid:
done < $1
