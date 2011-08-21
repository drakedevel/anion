#!/bin/bash
if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <config>" >&2
    exit 1
fi

# Settings
function setConfigName() { cConfigName="$1"; }
function setGenerator() { cGenerator="$1"; }
function setGeneratorParams() { cGeneratorParams="$@"; }
function setIonBinary() { cIonBinary="$1"; }
function setIonParamsA() { cIonParamsA="$@"; }
function setIonParamsB() { cIonParamsB="$@"; }
function setTracer() { cTracer="$1"; }
. "$1"

# Parameters
declare -r pTempDir="/tmp"
declare -r pResultDir="results${cConfigName:+-}${cConfigName:-}"
declare -r pHash="md5sum"
declare -i -r pHashLength=32

declare -r pGenerator="${cGenerator:?}"
declare -r pGeneratorParams="${cGeneratorParams:-}"

declare -r pIonBinary="${cIonBinary:?}"
declare -r pIonParamsA="${cIonParamsA:-}"
declare -r pIonParamsB="${cIonParamsB:-}"
declare -r pTimeout="1"
declare -r pTracer="${cTracer:?}"

# Global state
declare gTestSource
declare gTestSourceHash

# Functions
function die() {
    echo "$1" >&2
    exit 1
}

function spam() {
    echo -n "$1"
}

function tempExt() {
    mktemp "${pTempDir}/XXXXXXXX.${1}"
}

function generateTest() {
    gTestSource="$(tempExt js)"
    "$pGenerator" $pGeneratorParams > "$gTestSource" || return $?

    local hashLine="$("$pHash" "$gTestSource")"
    gTestSourceHash="${hashLine:0:pHashLength}"
    return 0
}

function runTest() {
    local params="$1"
    (ulimit -t "$pTimeout"; exec 2>/dev/null; "${pIonBinary}" $params "${gTestSource}" | egrep "^CATION:${pTracer}\$" | wc -l)
}

function cleanup() {
    [[ -f "$gTestSource" ]] && rm -f "$gTestSource"
    return 0
}

function bail() {
    cleanup
    exit 0
}

# Make sure we actually die on Ctrl-C/Ctrl-\
trap bail INT TERM

mkdir -p "${pResultDir}" || die "Failed to create output directory"
while true; do
    generateTest || die "Failed to generate test"

    resultsA="$(runTest "$pIonParamsA")"
    [[ $? -ne 0 ]] && continue
    resultsB="$(runTest "$pIonParamsB")"
    [[ $? -ne 0 ]] && continue

    if [[ "$resultsA" -lt "$resultsB" ]]; then
	# Regression found!
	if [[ "$resultsA" -eq 0 ]]; then
	    echo -e "Infty\t${gTestSourceHash}" >> "${pResultDir}/scorecard"
	else
	    regressPercent="$(dc -e "4k ${resultsB} ${resultsA} - ${resultsA} / 100 * 2k 1 / p")"
	    echo -e "${regressPercent}\t${gTestSourceHash}" >> "${pResultDir}/scorecard"
	fi
	mv "${gTestSource}" "${pResultDir}/${gTestSourceHash}.js"
	spam "-"
    elif [[ "$resultsA" -gt "$resultsB" ]]; then
	spam "+"
    fi

    cleanup
done
