# Live demo script (about 12 minutes)

Have ready: the cluster up, the app open in a browser tab, Grafana open on the QuickDesk dashboard, three terminals (`kubectl get pods -n quickdesk -w`, `kubectl get hpa -n quickdesk -w`, a free one), and the GitHub Actions tab.

Walk the chain, one sentence of "why" each:

1. **Application.** Create a ticket in the UI. "Frontend calls `/api`, which the Ingress sends to the backend, which stores it in PostgreSQL."
2. **Git commit.** Make a visible change (for example a wording change in `frontend/src/App.jsx`), then `git commit -am "Reword empty state"` and `git push`.
3. **CI pipeline.** In Actions: tests, build, scan, push. "Tests are the first gate: if they fail nothing gets built."
4. **Docker image + Trivy.** Open the Trivy step. "The image is scanned *before* it is pushed; a HIGH/CRITICAL CVE with a fix turns the pipeline red and nothing reaches the registry."
5. **Registry.** GHCR page. "The tag is the commit SHA, so every running pod maps to exactly one commit."
6. **Terraform.** Show `terraform/main.tf` and the AWS console. "The VPC and the EKS cluster came from code, and `terraform destroy` removes them."
7. **Kubernetes + Helm.** `helm upgrade --install ... --set backend.image.tag=<new sha>` (or let the deploy job do it). Watch the rolling update in the pods terminal. Then `helm list -n quickdesk`. "Helm is the chart plus values; the new SHA is the only thing that changed."
8. **Ingress.** `kubectl get ingress -n quickdesk`; show `/api` vs `/` rules. Refresh the browser and show the change.
9. **Autoscaling.** `./scripts/loadtest.sh`. Watch the HPA go from 2 toward 6 replicas. "HPA targets 60% of the CPU *request*; without a request there is no percentage."
10. **Monitoring.** Grafana: requests per second jump, replicas climb, CPU usage crosses the request line.
11. **Troubleshooting.** Run `./scripts/break.sh bad-image`. Narrate the diagnosis: `kubectl get pods`, `kubectl describe pod`, read Events, fix with `kubectl rollout undo deploy/quickdesk-backend -n quickdesk`. If time allows, repeat with `bad-probe`.

## Questions examiners like

- Why does the backend have both `/health` and `/ready`? (Liveness restarts a stuck process; readiness only stops sending traffic, for example when the database is down.)
- Why do migrations run in an init container and not in each backend pod? (Two replicas would race; an init container runs before the app starts, and a database lock serialises the replicas.)
- What happens to the database if the postgres pod dies? (The StatefulSet recreates it and re-attaches the same EBS volume.)
- Why SHA tags and not `latest`? (Reproducible and traceable; `latest` can't tell you what is running or how to roll back.)
- Why must you run `teardown.sh` before `terraform destroy`? (Kubernetes created a load balancer and a disk that Terraform doesn't know about; they block deleting the VPC.)
