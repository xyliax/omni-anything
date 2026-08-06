#!/bin/bash
set -u
cd "$(dirname "$0")/.."
N="${N:-128}"; DUR="${DUR:-300}"
echo "#### LONG vanilla N=$N/${DUR}s ($(date +%H:%M:%S)) ####"
WINDOW=0 INENGINE_SWA=0 DUR=$DUR MAXSEQS=192 MML=8192 TAG=longp_van bash experiments/run_stream_gateway.sh "$N"
sleep 6
echo "#### LONG in-engine SWA N=$N/${DUR}s ($(date +%H:%M:%S)) ####"
WINDOW=0 INENGINE_SWA=1024 DUR=$DUR MAXSEQS=192 MML=8192 TAG=longp_ineng bash experiments/run_stream_gateway.sh "$N"
echo "#### LONG PAIR DONE ####"
