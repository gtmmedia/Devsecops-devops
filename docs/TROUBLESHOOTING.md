# Troubleshooting cheat sheet

Golden path: `kubectl get pods -n quickdesk` > `kubectl describe pod <name> -n quickdesk` (read **Events**) > `kubectl logs <name> -n quickdesk` (add `-c migrate` for the init container, `--previous` after a crash).

| Symptom | Likely cause | Check | Fix |
|---|---|---|---|
| `ImagePullBackOff` / `ErrImagePull` | Wrong tag, typo, or the GHCR package is private | `describe pod` > Events | Use a SHA that exists on the package page; make the package public or add an `imagePullSecret` |
| `Init:0/1` for a long time, then `Init:CrashLoopBackOff` | Backend can't reach/login to PostgreSQL | `logs <pod> -c migrate` | Postgres pod Running? Password in `quickdesk-db` consistent? (see `scripts/break.sh`) |
| `Running` but `0/1` Ready | Readiness probe failing | `describe pod` > "Readiness probe failed" | Fix the path/port; `curl` `/ready` via port-forward; DB down also causes this |
| `CrashLoopBackOff` on backend | App crashes at start | `logs <pod> --previous` | Read the traceback (bad env var, missing migration) |
| `Pending` | No node has room (CPU/memory/pod limit) or the PVC can't bind | `describe pod` > "Insufficient cpu" / "unbound PersistentVolumeClaim" | Add nodes; for PVC check the `aws-ebs-csi-driver` add-on and a default StorageClass |
| HPA shows `<unknown>/60%` | No metrics-server, or no CPU *request* set | `kubectl top pods -n quickdesk`; `describe hpa` | Install metrics-server (Terraform add-on); keep `resources.requests.cpu` |
| Ingress has no ADDRESS | Ingress controller not installed or still creating the load balancer | `kubectl get svc -n ingress-nginx` | Run the bootstrap script; wait 2-3 minutes |
| 404 from the load balancer | No matching Ingress rule/host | `kubectl describe ingress -n quickdesk` | Leave `ingress.host` empty or send the right Host header |
| `/api` works, page is blank | Frontend image/pods unhealthy | `kubectl logs deploy/quickdesk-frontend -n quickdesk` | Check `/healthz`, check the image tag |
| Prometheus Targets has no QuickDesk | ServiceMonitor missing (CRD absent when the app was installed) | `kubectl get servicemonitor -n quickdesk` | Install monitoring first, then `helm upgrade` the app again |
| Grafana dashboard missing | ConfigMap label or sidecar | `kubectl get cm -n quickdesk -l grafana_dashboard=1` | Re-run `helm upgrade`; restart the Grafana pod |
| Pipeline red at Trivy | A fixable HIGH/CRITICAL CVE | Step log | Upgrade the package or base image tag, push again |
| Pipeline red at GHCR push | Workflow permissions read-only | Step log: "denied" | Settings > Actions > General > Read and write |
| `terraform destroy` hangs on the VPC | Load balancer or EBS volume left behind | EC2 > Load Balancers / Volumes | Run `scripts/teardown.sh`, wait, retry |

Useful extras: `kubectl get events -n quickdesk --sort-by=.lastTimestamp`, `kubectl rollout history deploy/quickdesk-backend -n quickdesk`, `kubectl exec -it quickdesk-postgres-0 -n quickdesk -- psql -U quickdesk`.
