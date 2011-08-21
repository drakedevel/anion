#!/bin/bash
# This is a small driver to drive "driver.sh" on multiple processes
# while killing all of them with C-c or C-\.
if [[ $# -lt 3 ]]; then
    echo "Usage: $0 <driver> <config> <nthreads>"
fi

# Parameters
declare -r pDriver="$1"
declare -r pConfig="$2"
declare -i -r pNumThreads="$3"

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
    "${pDriver}" "$pConfig" &
    gThreads[i]=$!
done
wait
