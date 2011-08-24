#!/bin/bash
# A little script to use backtrace.gdb to extract a backtrace

if [[ $# -lt 2 ]]; then
    echo "Usage: $0 <jsbin> [jsopts] <testcase>" >&2
    exit 1
fi

jsbin="$1"
shift 1
testjsopts="--ion $@"

# Please forgive me
exec 2>/dev/null
gdb -batch -x backtrace.gdb --args "$jsbin" $testjsopts 2>/dev/null |\
 sed -r '/^[^#]/d;/^$/d;/syscall/d;/raise/d;s/"[^"]+"//;s/\s+/ /g;s/\([^)]*\) //;s/:([0-9]+)$/ \1/;s,/([^/]+/)+,,g;' |\
 awk '{ print $4 " " $6 " " $7 }' |\
 sed -r '/0x/d'
