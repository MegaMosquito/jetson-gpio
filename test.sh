#!/bin/bash

curl -X POST -sS localhost:6667/gpio/v1/mode/board

curl -X POST -sS localhost:6667/gpio/v1/configure/40/out
curl -X POST -sS localhost:6667/gpio/v1/configure/38/in/down

while [ true ]
do
  x=`curl -sS localhost:6667/gpio/v1/38 | jq .state`
  if [[ "${x}" == "true" ]]
  then
    curl -X POST -sS localhost:6667/gpio/v1/40/1 >/dev/null 2>&1
  else
    curl -X POST -sS localhost:6667/gpio/v1/40/0 >/dev/null 2>&1
  fi
  # sleep 1
done
