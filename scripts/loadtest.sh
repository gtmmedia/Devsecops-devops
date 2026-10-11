#!/usr/bin/env bash
# Generates CPU load inside the cluster so you can watch the HPA scale the backend.
# Needs the chart default backend.enableDebugEndpoints=true (it calls /api/debug/burn).
#
# Usage:  ./scripts/loadtest.sh            (runs for 4 minutes)
#         DURATION=120 PARALLEL=30 ./scripts/loadtest.sh
#
# In other terminals:
#   kubectl get hpa -n quickdesk -w
#   kubectl get pods -n quickdesk -w
set -euo pipefail
NAMESPACE="${NAMESPACE:-quickdesk}"
DURATION="${DURATION:-240}"
PARALLEL="${PARALLEL:-20}"
SERVICE="${SERVICE:-quickdesk-backend}"
URL="http://${SERVICE}:8000/api/debug/burn?ms=300"

echo "Hitting ${URL} with ${PARALLEL} parallel clients for ${DURATION}s ..."
kubectl run loadgen -n "$NAMESPACE" --rm -i --restart=Never --image=busybox:1.37 -- \
  /bin/sh -c "
    end=\$(( \$(date +%s) + ${DURATION} ))
    for i in \$(seq 1 ${PARALLEL}); do
      ( while [ \$(date +%s) -lt \$end ]; do wget -q -O /dev/null '${URL}' || true; done ) &
    done
    wait
    echo load finished"
echo "Done. Scale-down starts after the HPA stabilisation window (about 90s)."
