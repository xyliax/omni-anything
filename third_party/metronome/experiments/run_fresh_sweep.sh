#!/bin/bash
# FRESH-PER-POINT capacity sweep: one worker LOAD+teardown per N (no sequential-sweep contamination).
# Each iteration calls run_stream_gateway.sh with a SINGLE N -> fresh worker -> clean capacity point.
# Pass MODEL / PERIOD_MS / DUR / WINDOW / INENGINE_SWA / MAXSEQS / TAG via env (inherited downstream).
#   GRID="64 96 128 160" TAG=freshv MODEL=... bash experiments/run_fresh_sweep.sh
set -u
cd "$(dirname "$0")/.."
GRID="${GRID:-64 96 128 160}"
for N in $GRID; do
  echo "######## FRESH point: ${TAG:-fresh} N=$N ($(date +%H:%M:%S)) ########"
  bash experiments/run_stream_gateway.sh "$N"
  sleep 6
done
echo "######## FRESH SWEEP DONE (${TAG:-fresh}) ########"
