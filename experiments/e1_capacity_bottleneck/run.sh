#!/usr/bin/env bash
# Stable shell entry point for the E1 capacity-bottleneck experiment.
set -Eeuo pipefail
cd "$(dirname "$0")/../.."
exec "${EXPERIMENT_PYTHON:-python3}" -m experiments.e1_capacity_bottleneck.cli "$@"
