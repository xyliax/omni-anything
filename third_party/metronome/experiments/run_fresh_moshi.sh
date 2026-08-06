#!/bin/bash
set -u
cd "$(dirname "$0")/.."
for N in ${1:-8 16 24 32}; do
  echo "######## FRESH moshi N=$N ($(date +%H:%M:%S)) ########"
  DUR="${DUR:-60}" bash experiments/run_sustained_moshi.sh "$N"
  sleep 6
done
echo "######## FRESH MOSHI DONE ########"
