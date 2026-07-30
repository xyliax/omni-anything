#!/usr/bin/env bash
# Block until GPU $1 has been idle for $2 consecutive seconds.
#
# The card is shared and the co-tenant is bursty. Contention inflates eager
# prefill steps by ~30% and decode steps by up to 2x, which is larger than the
# validation bar itself -- so a validation run started at the wrong moment
# measures the neighbour, not the model.
gpu=${1:-3}
need=${2:-60}
quiet=0
while :; do
  read -r util pwr < <(nvidia-smi --id="$gpu" \
      --query-gpu=utilization.gpu,power.draw --format=csv,noheader,nounits \
      | tr -d ',')
  if [ "${util%.*}" -le 3 ] && [ "${pwr%.*}" -le 150 ]; then
    quiet=$((quiet + 3))
  else
    [ "$quiet" -gt 0 ] && echo "  [wait] busy again (${util}% ${pwr}W), resetting"
    quiet=0
  fi
  if [ "$quiet" -ge "$need" ]; then
    echo "  [wait] GPU $gpu quiet for ${quiet}s (${util}% ${pwr}W) -- go"
    exit 0
  fi
  sleep 3
done
