#!/usr/bin/env bash
# Break the deployment on purpose for the troubleshooting part of the demo.
#
# Usage:  ./scripts/break.sh bad-image | bad-probe | bad-db-password
# Each scenario prints how to diagnose and fix it afterwards.
set -euo pipefail
NS="${NAMESPACE:-quickdesk}"
DEPLOY="${DEPLOY:-quickdesk-backend}"

case "${1:-}" in
  bad-image)
    echo "Pointing the backend at an image tag that does not exist ..."
    img="$(kubectl get deploy "$DEPLOY" -n "$NS" -o jsonpath='{.spec.template.spec.containers[0].image}')"
    kubectl set image deploy/"$DEPLOY" backend="${img%:*}:this-tag-does-not-exist" -n "$NS"
    cat <<MSG

Expected symptom : new pods show ErrImagePull -> ImagePullBackOff (old pods keep serving)
Diagnose         : kubectl get pods -n $NS
                   kubectl describe pod <new-pod> -n $NS      # read the Events at the bottom
Fix              : kubectl rollout undo deploy/$DEPLOY -n $NS
MSG
    ;;
  bad-probe)
    echo "Making the readiness probe check a path that does not exist ..."
    kubectl patch deploy "$DEPLOY" -n "$NS" --type=json \
      -p='[{"op":"replace","path":"/spec/template/spec/containers/0/readinessProbe/httpGet/path","value":"/does-not-exist"}]'
    cat <<MSG

Expected symptom : pods are Running but READY stays 0/1, rollout never finishes
Diagnose         : kubectl get pods -n $NS
                   kubectl describe pod <new-pod> -n $NS      # "Readiness probe failed: HTTP probe failed with statuscode: 404"
                   kubectl get endpoints $DEPLOY -n $NS       # new pods are missing from the list
Fix              : kubectl rollout undo deploy/$DEPLOY -n $NS
MSG
    ;;
  bad-db-password)
    echo "Corrupting the password inside DATABASE_URL, then restarting the backend ..."
    secret="${DEPLOY%-backend}-db"
    bad="$(printf 'postgresql+psycopg2://quickdesk:WRONG-PASSWORD@%s-postgres:5432/quickdesk' "${DEPLOY%-backend}" | base64 -w0)"
    kubectl patch secret "$secret" -n "$NS" --type=json \
      -p="[{\"op\":\"replace\",\"path\":\"/data/DATABASE_URL\",\"value\":\"$bad\"}]"
    kubectl rollout restart deploy/"$DEPLOY" -n "$NS"
    cat <<MSG

Expected symptom : new pods stuck in Init:0/1, later Init:CrashLoopBackOff (the migrate init container can't log in)
Diagnose         : kubectl get pods -n $NS
                   kubectl logs <new-pod> -n $NS -c migrate    # "password authentication failed"
MSG
    cat <<'MSG' | sed -e "s/__SECRET__/$secret/g" -e "s/__NS__/$NS/g" -e "s/__DEPLOY__/$DEPLOY/g"
Fix              : rebuild DATABASE_URL from the real password stored next to it:
                   PW=$(kubectl get secret __SECRET__ -n __NS__ -o jsonpath='{.data.POSTGRES_PASSWORD}' | base64 -d)
                   kubectl patch secret __SECRET__ -n __NS__ --type=merge \
                     -p "{\"stringData\":{\"DATABASE_URL\":\"postgresql+psycopg2://quickdesk:${PW}@quickdesk-postgres:5432/quickdesk\"}}"
                   kubectl rollout restart deploy/__DEPLOY__ -n __NS__
MSG
    ;;
  *)
    echo "Usage: $0 bad-image | bad-probe | bad-db-password" >&2
    exit 1
    ;;
esac
