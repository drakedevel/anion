#!/bin/bash
# This is a small driver to drive "driver.sh" on multiple processes
# while killing all of them with C-c or C-\.
if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <config> <nthreads>"
fi

# Parameters
declare -r pConfig="$1"
declare -i -r pNumThreads="$2"

# Global variables
declare -a gThreads

function bail() {
    for pid in "${gThreads[@]}"; do
	kill -TERM "$pid"
    done
    exit 0
}

trap bail SIGINT
trap bail SIGTERM

for i in `seq 1 $pNumThreads`; do
    ./driver.sh "$pConfig" &
    gThreads[i]=$!
done
wait
