#!/bin/bash

echo "      date     time $(free -m | grep total | sed -E 's/^    (.*)/\1/g')" |& tee meminfo.log
while true; do
    echo "$(date '+%Y-%m-%d %H:%M:%S') $(free -m | grep Mem: | sed 's/Mem://g')" |& tee -a meminfo.log
    sleep 60
done

