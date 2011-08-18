#!/bin/bash
# Drive the fuzzer with the given config file on a single process.
if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <config>" >&2
    exit 1
fi

# Settings
function setConfigName() { declare -g -r cConfigName="$1"; }
function setGenerator() { declare -g -r cGenerator="$1"; }
function setGeneratorParams() { declare -g -r cGeneratorParams="$@"; }
function setIonBinary() { declare -g -r cIonBinary="$1"; }
function setIonOpts() { declare -g -r cIonOpts="$@"; }
function setSampleFactor() { declare -g -r cSampleFactor="$1"; }
. "$1"

jsbin="../js-$btype$arch/js"
resultdir="results_${btype}${arch}_$(tr ' ' '_' <<< "$opts")"

# Parameters
declare -r pTempDir="/tmp"
declare -r pResultDir="results-${cConfigName:?}"
declare -r pHash="md5sum"
declare -i -r pHashLength=32
declare -r pJSReferenceBinary="${cIonBinary:?}"
declare -r pJSReferenceParams
declare -r pSkipCount="${cSampleFactor:-30}"
declare -r pTriageScript="$(dirname "$0")/triage.sh"

# Global variables
declare gGeneratorBinary="${cGenerator:?}"
declare gGeneratorParams="${cGeneratorParams:-}"
declare gJSTestBinary="${cIonBinary:?}"
declare gJSTestParams="--ion ${cIonOpts:-}"
declare gSkipIndex=0
declare gTestSourceHash
declare gTestSource
declare gTestOutput
declare gTestReturn
declare gTestReference
declare gTestSignature
declare gTestSignatureHash

# logInteresting <status>
function logInteresting() {
    echo "!"
    echo "$1"
}

# logUninteresting <statuschar>
function logUninteresting() {
    gSkipIndex=$(((gSkipIndex+1) % pSkipCount))
    [[ $gSkipIndex -eq 0 ]] && echo -n "$1"
}

# die <message>
function die() {
    echo "!!!"
    echo "$1" >&2
    exit 1
}

# tempExt <ext>
function tempExt() {
    mktemp "${pTempDir}/XXXXXXXXXX.${1}"
}

function generateTest() {
    gTestSource="$(tempExt js)"
    "$gGeneratorBinary" $gGeneratorParams >"$gTestSource"
    local ret=$?
    [[ $ret -eq 0 ]] || return $ret

    local hashline="$("$pHash" "$gTestSource")"
    gTestSourceHash="${hashline:0:pHashLength}"
    return 0
}

function runTest() {
    gTestOutput="$(tempExt out)"
    (ulimit -t 2; exec 2>/dev/null; "$gJSTestBinary" $gJSTestParams "$gTestSource" &>"$gTestOutput")
    gTestReturn=$?
    return $gTestReturn
}

function runTestReference() {
    gTestReference="$(tempExt ref)"
    (ulimit -t 2; exec 2>/dev/null; "$pJSReferenceBinary" $pJSReferenceParams "$gTestSource" &>"$gTestReference")
    return $?
}

function calculateSignature() {
    gTestSignature="$(tempExt sig)"
    head -n1 "$gTestOutput" >"$gTestSignature"
    "$pTriageScript" "$gJSTestBinary" $gJSTestParams "$gTestSource" >>"$gTestSignature"
    local ret=$?
    [[ $ret -eq 0 ]] || return $ret

    local hashline="$("$pHash" "$gTestSignature")"
    gTestSignatureHash="${hashline:0:pHashLength}"
    return 0
}

# interestingOutput <category> <message>
function interestingOutput() {
    local dir="${pResultDir}/${1}"
    mkdir -p "$dir"
    mv "$gTestSource" "${dir}/${gTestSourceHash}.js"
    mv "$gTestOutput" "${dir}/${gTestSourceHash}.out"
    mv "$gTestReference" "${dir}/${gTestSourceHash}.ref"
    logInteresting "$2"
}

# interestingSignature <category> [message]
function interestingSignature() {
    calculateSignature
    local dir="${pResultDir}/${1}/${gTestSignatureHash}"
    if [[ -d "$dir" ]]; then
	logUninteresting "+"
    else
	mkdir -p "$dir"
	if [[ $2 ]]; then
	    logInteresting "$2"
	else
	    logInteresting "$(head -n1 "$gTestSignature")"
	fi
	mv "$gTestSignature" "${dir}/signature"
    fi
    mv "$gTestSource" "${dir}/${gTestSourceHash}.js"
}

# interestingTestcase <category> <message>
function interestingTestcase() {
    local dir="${pResultDir}/${1}"
    mkdir -p "$dir"
    mv "$gTestSource" "${dir}/${gTestSourceHash}.js"
    logInteresting "$2"
}

function cleanup() {
    [[ -f $gTestSource ]] && rm -f "$gTestSource"
    [[ -f $gTestOutput ]] && rm -f "$gTestOutput"
    [[ -f $gTestReference ]] && rm -f "$gTestReference"
    [[ -f $gTestSignature ]] && rm -f "$gTestSignature"
}

function bail() {
    cleanup
    exit 0
}

trap bail SIGINT
trap bail SIGTERM

while true; do
    generateTest || die "Failed to generate test"
    runTest
    case $gTestReturn in
        # If we had a successful run (ret=0), or the script ran forever and was
        # timed out (ret=137), run it with IM disabled and compare the outputs
	0|137)
	    runTestReference
	    cmp -s "$gTestOutput" "$gTestReference"
	    if [[ $? -ne 0 ]]; then
		interestingOutput "divergences" "Output diverged"
	    else
		if [[ $gTestReturn -eq 0 ]]; then
		    logUninteresting "."
		else
		    logUninteresting "z"
		fi
	    fi
	;;

        # If this is an assertion (ret=134), capture the output
	134)
	    # Filter out known (ignored) asserts
	    egrep -q "(implement|NYI)" "$gTestOutput"
	    if [[ $? -eq 0 ]]; then
		logUninteresting "-"
	    else
		interestingSignature "assertions"
	    fi
	;;

	# Segfaults are ret=139
	139)
	    interestingSignature "segfaults" "Segmentation fault"
	    ;;

	# Unexpected error code. Weird.
	*)
	    interestingTestcase "return-${gTestReturn}" "Unexpected return code ${gTestReturn}"
	    ;;
    esac

    cleanup
done
