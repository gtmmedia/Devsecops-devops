# QuickDesk

A small helpdesk. Customers file tickets, support agents triage them (status, priority, owner), talk to the customer in a comment thread, and close them.

QuickDesk is the *cargo*. The point of the project is the delivery pipeline around it: tests, containers, a security scan, a registry, Terraform-built AWS infrastructure, Kubernetes, Helm, autoscaling and monitoring.

```
 git push ──► GitHub Actions ──► tests ──► Docker build ──► Trivy scan ──► GHCR (tag = commit SHA)
                                                                              │
 terraform apply ──► AWS VPC + EKS ──► helm upgrade --install ◄───────────────┘
                                          │
              Internet ─► NLB ─► Ingress ─┼─ /api ─► backend (FastAPI, HPA 2-6 pods) ─► PostgreSQL
                                          └─ /    ─► frontend (nginx + React, 2 pods)
                          Prometheus scrapes backend /metrics ─► Grafana dashboard
```

## What's inside

| Part | Tech | Where |
|---|---|---|
| Frontend | React 18 + Vite, responsive (phone and desktop) | `frontend/` |
| Backend | FastAPI, SQLAlchemy 2, Alembic migrations | `backend/` |
| Database | PostgreSQL 16 | `docker-compose.yml`, `helm/quickdesk/templates/postgres.yaml` |
| Tests | pytest (25 tests, SQLite test DB), ruff | `backend/tests/` |
| Containers | Multi-stage frontend, non-root images | `*/Dockerfile` |
| CI/CD | GitHub Actions, Trivy, GHCR | `.github/workflows/ci.yml` |
| Infrastructure | Terraform: VPC (2 public subnets) + EKS | `terraform/` |
| Kubernetes | Namespace, Helm chart, Ingress, HPA | `k8s/`, `helm/quickdesk/` |
| Observability | Prometheus + Grafana (kube-prometheus-stack) | `monitoring/`, `helm/quickdesk/dashboards/` |
| Docs and helpers | Guides, demo script, scripts | `docs/`, `scripts/` |

## REST API

Interactive docs at `http://localhost:8000/docs` when running locally.

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/tickets` | Create a ticket (201) |
| GET | `/api/tickets?status=&priority=&q=` | List, filter and search |
| GET | `/api/tickets/stats` | Counts by status |
| GET | `/api/tickets/{id}` | One ticket with its comments |
| PUT | `/api/tickets/{id}` | Replace editable fields (a closed ticket is frozen until reopened: 409) |
| DELETE | `/api/tickets/{id}` | Delete a ticket and its comments (204) |
| GET | `/api/tickets/{id}/comments` | List comments |
| POST | `/api/tickets/{id}/comments` | Add a comment (201) |
| GET | `/health` | Liveness probe |
| GET | `/ready` | Readiness probe (checks the database) |
| GET | `/metrics` | Prometheus metrics |

## 1. Run it locally (Docker Compose)

```bash
cp .env.example .env            # optional: change the DB password
docker compose up --build
```

Open <http://localhost:3000>. Load demo tickets (optional):

```bash
docker compose exec backend python -m app.seed
```

Stop with `Ctrl+C`; `docker compose down -v` also deletes the database volume.

## 2. Develop without Docker

```bash
# backend (needs a PostgreSQL; the quickest is: docker compose up db -d  after adding ports: ["5432:5432"] to db)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL=postgresql+psycopg2://quickdesk:quickdesk-dev-only@localhost:5432/quickdesk
alembic upgrade head
uvicorn app.main:app --reload            # http://localhost:8000/docs

# frontend, in a second terminal
cd frontend
npm install
npm run dev                              # http://localhost:5173 (proxies /api to :8000)
```

## 3. Tests and lint

```bash
cd backend
pytest -v                                # tests use an in-memory SQLite DB, never PostgreSQL
pytest --cov=app --cov-report=term-missing
ruff check . && ruff format --check .
```

## 4. CI/CD pipeline

`.github/workflows/ci.yml` runs on every push to `main` (and on pull requests):

1. **backend-test**: ruff, then pytest. A failing test stops everything below.
2. **frontend-build**: `npm ci && npm run build`.
3. **docker** (one job each for backend and frontend): build the image, **Trivy scan** (fails on HIGH/CRITICAL that have a fix), and only if the scan is clean push `ghcr.io/<you>/quickdesk-<service>:<commit-sha>`. There is no `latest` tag.
4. **deploy** (optional): `helm upgrade` on EKS. Disabled until you set the repository variable `DEPLOY_ENABLED=true`.

One-time GitHub setup: see `docs/SUBMISSION-GUIDE.md` (package visibility and the optional deploy secrets).

## 5. Deploy to AWS

You need: an AWS account and credentials in your shell (`aws configure`), Terraform >= 1.6, kubectl, Helm 3. **This costs money while it runs (roughly $0.25 an hour: EKS control plane plus 3 small nodes plus a load balancer). Always finish with step 7.**

```bash
# 1. infrastructure
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply

# 2. connect kubectl (the command is also printed as the `configure_kubectl` output)
aws eks update-kubeconfig --region ap-south-1 --name quickdesk-demo-eks
kubectl get nodes

# 3. everything on top (ingress controller, Prometheus + Grafana, QuickDesk)
cd ..
GITHUB_OWNER=<your-github-username-lowercase> IMAGE_TAG=<full-commit-sha> ./scripts/bootstrap-cluster.sh
```

The script prints the load balancer address. Open `http://<that-address>/`. To deploy by hand instead, read `scripts/bootstrap-cluster.sh`: it is just three `helm upgrade --install` commands.

## 6. See it working

```bash
kubectl get pods,svc,ingress,hpa -n quickdesk
helm list -n quickdesk
kubectl port-forward -n quickdesk svc/quickdesk-backend 8000:8000   # then: curl localhost:8000/metrics
kubectl port-forward -n monitoring svc/monitoring-grafana 3001:80    # Grafana: http://localhost:3001 (user: admin)
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090  # Targets: http://localhost:9090/targets
./scripts/loadtest.sh                                                # watch: kubectl get hpa -n quickdesk -w
```

Grafana dashboard: **Dashboards > QuickDesk overview**.

## 7. Tear down (do not skip)

```bash
./scripts/teardown.sh        # removes the load balancer and disks Kubernetes created
cd terraform && terraform destroy
```

Then confirm in the AWS console that EC2 (load balancers, volumes) and VPC are empty.

## Security notes

- No secrets in Git. `.env`, `terraform.tfvars` and state files are git-ignored. AWS keys come from your environment or GitHub secrets. The database password in Kubernetes is generated by Helm.
- Containers run as non-root (backend uid 10001, nginx uid 101) with all Linux capabilities dropped.
- Images are scanned with Trivy before they are pushed. The Trivy action is pinned to a commit SHA because its version tags were hijacked in March 2026.
- Known simplifications (fine for a course project, not for production): no user login, worker nodes in public subnets without a NAT gateway, local Terraform state, Prometheus without persistent storage.

## Repository layout

```
backend/        FastAPI app, Alembic migrations, tests, Dockerfile
frontend/       React app, nginx template, Dockerfile
helm/quickdesk/ Helm chart (deployments, services, ingress, HPA, ServiceMonitor, dashboard)
k8s/            Namespace and ingress controller values
terraform/      VPC + EKS
monitoring/     Prometheus and Grafana Helm values
scripts/        bootstrap, loadtest, break (troubleshooting demo), teardown
docs/           submission guide, demo script, troubleshooting
.github/        CI/CD workflow
```
