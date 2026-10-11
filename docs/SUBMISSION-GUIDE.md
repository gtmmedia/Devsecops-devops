# Submission guide: rubric to evidence

For each module: where the work lives, the exact command that produces the screenshot, and the traps that cost points. Work through it in order. **Add each layer to Git only after you have run it yourself** (that is also how you get 10+ honest, meaningful commits, for example `Add Terraform VPC and EKS`, `Add Helm chart with HPA`, `Fix readiness probe path`).

Before you start, make it yours: change something visible (a ticket field, a colour, the wording) and be ready to explain every file. The rubric gives zero for unmodified reference clones and the live demo asks you to explain what you built.

## One-time GitHub setup

1. Create a **public** repository and push this folder to `main`.
2. Settings > Actions > General > Workflow permissions: **Read and write** (the pipeline pushes packages with the built-in token).
3. After the first green run, open your profile > Packages > `quickdesk-backend` / `quickdesk-frontend` > Package settings > **Change visibility to Public** (otherwise the cluster can't pull them without an image pull secret).
4. Optional continuous deployment: Settings > Secrets and variables > Actions:
   - Secrets: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` (never in the repo)
   - Variables: `AWS_REGION`, `EKS_CLUSTER_NAME` (`quickdesk-demo-eks`), `DEPLOY_ENABLED=true`
   - If the key belongs to a different IAM user than the one that ran `terraform apply`, add its ARN to `admin_principal_arns` in `terraform.tfvars` and apply again.

## M1 Application (10)

| Evidence | How |
|---|---|
| `/health` responds | `curl localhost:8000/health` |
| 4+ endpoints incl. GET/POST/PUT/DELETE | `backend/app/routers/tickets.py` (8 endpoints) |
| Alembic migration | `backend/alembic/versions/0001_create_tickets_and_comments.py` |
| Frontend renders and calls the API | screenshot of `http://localhost:3000` with tickets listed |
| Responsive | screenshot at phone width (browser dev tools, 390px wide) |

## M2 Testing (10)

`cd backend && pytest -v` then screenshot the terminal showing all passing. Tests use SQLite in memory (`tests/conftest.py`), never the real database. `pytest.ini` is present.

## M3 Git and GitHub (5)

Repo URL, a screenshot of `git log --oneline` (10+ commits), `.gitignore` already excludes `.env`, `__pycache__`, `node_modules`, `.venv`. Avoid commit messages like "update" or "fix".

**Check for secrets before every push:** `git status` must never show `.env`, `terraform.tfvars` or `*.tfstate`.

## M4 Docker (10)

```bash
docker compose up --build        # screenshot the running output
```
Screenshot `http://localhost:3000`. Show non-root: `docker compose exec backend id` (uid=10001) and `docker compose exec frontend id` (uid=101). The frontend Dockerfile is multi-stage (Node build, nginx runtime).

## M5 CI/CD (15)

Push to `main`, open the Actions tab, copy the URL of the green run. Screenshot the GHCR package page showing tags that are 40-character commit SHAs. The workflow file is `.github/workflows/ci.yml`.

## M6 Trivy (5)

Screenshot the "Trivy scan" step log (a clean result prints a table with `0` vulnerabilities, which is fine). Write 2-3 sentences, for example:

> Trivy scanned the OS packages and Python/Node libraries inside the backend and frontend images against its CVE database. The pipeline fails on HIGH or CRITICAL findings that have a fix available. Both images came back clean, so they were pushed to GHCR.

If Trivy fails: read the CVE, bump the package in `requirements.txt` (or change the base image tag), push again. Do not silence it in `.trivyignore` without a reason.

## M7 Terraform (15)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform validate
terraform plan                    # screenshot (non-empty plan, no errors)
terraform apply                   # 12-15 minutes
```
AWS console screenshots (same region as `aws_region`): VPC > Your VPCs, VPC > Subnets (two public subnets), EKS > Clusters (Active, node group). Finish with `terraform destroy` and screenshot the "Destroy complete!" line. **Run `./scripts/teardown.sh` before `terraform destroy`.**

Never commit AWS keys. `terraform.tfvars.example` is the committed file; `terraform.tfvars` is ignored.

## M8 Kubernetes and Helm (15)

```bash
kubectl apply -f k8s/namespace.yaml
helm lint helm/quickdesk
helm upgrade --install quickdesk helm/quickdesk -n quickdesk \
  --set backend.image.repository=ghcr.io/<owner>/quickdesk-backend --set backend.image.tag=<sha> \
  --set frontend.image.repository=ghcr.io/<owner>/quickdesk-frontend --set frontend.image.tag=<sha>
```
(`scripts/bootstrap-cluster.sh` does this and the cluster add-ons.) Screenshots: `kubectl get pods -n quickdesk` (all Running, 2+ backend and 2+ frontend), `kubectl get svc -n quickdesk` (ClusterIP), `helm list -n quickdesk`, and the browser at the load balancer address. Ingress routes `/api` to the backend and `/` to the frontend (`helm/quickdesk/templates/ingress.yaml`).

## M9 Observability (10)

Screenshots: `curl localhost:8000/metrics` (via port-forward), Prometheus **Status > Targets** showing the backend `UP` (look for `serviceMonitor/quickdesk/quickdesk-backend`), and Grafana > Dashboards > **QuickDesk overview** with live panels (create some traffic first by clicking around the UI or running `./scripts/loadtest.sh`).

## M10 Documentation and demo (5)

`README.md` is in the root. Practise `docs/DEMO-SCRIPT.md` at least twice.

## Final checklist (from the course document)

```
Application      [ ] repo URL  [ ] docker compose up --build  [ ] 4+ endpoints  [ ] Alembic file
Testing          [ ] pytest screenshot  [ ] 5+ tests (there are 25)
Docker           [ ] backend builds  [ ] frontend multi-stage  [ ] non-root in both
CI/CD            [ ] workflow  [ ] runs on push to main  [ ] pytest in pipeline  [ ] GHCR + SHA tags
Security         [ ] Trivy in pipeline  [ ] no secrets in Git (check history: git log -p | grep -i secret)
Terraform        [ ] plan output  [ ] VPC + EKS console screenshot  [ ] destroy output
Kubernetes/Helm  [ ] pods Running  [ ] helm list  [ ] app via Ingress
Observability    [ ] /metrics  [ ] Targets UP  [ ] Grafana dashboard
Documentation    [ ] README  [ ] presentation or recording
```
