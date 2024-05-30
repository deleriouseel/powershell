#!/bin/bash
# Checks for open ports on external IP

# Requires dig and nmap
if ! [ -x "$(command -v nmap)" ]; then
  echo '{"success": 0, "message": "nmap command not found"}'
  exit 1
fi
if ! [ -x "$(command -v dig)" ]; then
  echo '{"success": 0, "message": "dig command not found"}'
  exit 1
fi

#get external ip, write it to iplist file
currentIP=$(dig +short myip.opendns.com @resolver1.opendns.com)

#run nmap, save output to file
nmap -Pn "$currentIP" -oN ./nmapoutput.txt

# print results
# TODO: > file
cat nmapoutput.txt
