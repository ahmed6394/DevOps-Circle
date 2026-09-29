# DevOps Circle

An 8-service microservices social platform, delivered to a Kubernetes cluster
on AWS EC2 through a CI/CD and GitOps pipeline, with metrics and logs collected
from the application's own instrumentation.

> **Status: deployed.** The full delivery path runs end to end on a k3s cluster
> on AWS EC2, reconciled by ArgoCD from this repository.
>
---

## What this project is

The interesting part is not the social feed. It is the delivery path.

A React frontend, six FastAPI services, an asynchronous worker, PostgreSQL, and
Redis are packaged into container images, scanned, published to a registry,
rendered through Kustomize, and reconciled onto a k3s cluster by ArgoCD. The
services export Prometheus metrics as they serve traffic, so the platform's
observability is driven by the application rather than bolted on afterward.

Post creation is asynchronous by design: `post-service` pushes a job onto a
Redis list and returns immediately, and `worker-service` consumes the queue and
writes to PostgreSQL. That queue is what makes queue depth and worker throughput
observable as first-class metrics.

## Architecture

```
Developer
  │
  ▼
GitHub (push to main)
  │
  ▼
GitHub Actions ── tests · security scans · image build · registry push
  │                                    │
  │                                    ▼
  │                          k8s/overlays/prod/kustomization.yaml
  │                          (image tag updated to the commit SHA)
  ▼
ArgoCD ── reconciles desired state from Git ──►  k3s on EC2
                                              │
                   ┌──────────────────────────┴───────────────────────┐
                   ▼                                                  ▼
            Application                                       Observability
    frontend · auth · user · post                     Prometheus · Grafana · Loki
    like · comment · analytics · worker              Alloy · node-exporter
    post-service ──► Redis queue ──► worker         kube-state-metrics · cAdvisor
                            │
                            ▼
                        PostgreSQL
```

### Services

| Service | Port | Role | Depends on |
| --- | ---: | --- | --- |
| `frontend` | 3000 | React UI plus an Nginx reverse proxy that routes `/api/*` to the services | all app services |
| `auth-service` | 8001 | Register, login, JWT | postgres |
| `user-service` | 8002 | Profiles and user data | postgres |
| `post-service` | 8003 | Accepts posts, enqueues to Redis | postgres, redis |
| `like-service` | 8004 | Post likes | postgres |
| `comment-service` | 8005 | Comments and comment likes | postgres |
| `analytics-service` | 8006 | Metrics, impressions, queue status | postgres, redis |
| `worker-service` | 9100 | Consumes the Redis queue, writes posts | postgres, redis |
| `postgres` | 5432 | Shared database | — |
| `redis` | 6379 | Cache and job queue | — |

Only `post-service`, `analytics-service`, and `worker-service` use Redis. The
other four app services depend on PostgreSQL alone.

### Request path

Two proxies sit in front of the application, and they do different jobs:

```
Internet
  └─ Traefik  (Ingress, host devops-circle.local)
       └─ frontend:80  →  Nginx inside the frontend pod
            ├─ /api/auth/      → auth-service:8001
            ├─ /api/user/      → user-service:8002
            ├─ /api/post/      → post-service:8003
            ├─ /api/like/      → like-service:8004
            ├─ /api/comment/   → comment-service:8005
            ├─ /api/analytics/ → analytics-service:8006
            └─ /              → index.html (SPA fallback)
```

The Ingress has a single rule, `/` → `frontend:80`. All path-based routing
happens in the Nginx configuration inside the frontend pod, which mirrors the
ALB path-routing model from the course material. Traefik handles only host and
entrypoint selection above it.

Traefik and the ServiceLB it depends on are **not defined in this repository**.
Both ship enabled by default with k3s and run in the `kube-system` namespace;
`scripts/02-install-k3s.sh` installs k3s without `--disable traefik`, and no
manifest here installs a controller. On a cluster where those defaults are off
— EKS, or k3s with Traefik disabled — the Ingress would carry no controller and
routing would fail silently, so the controller is an implicit dependency of
this deployment rather than a component of it.

## Build status

| Layer | Status | Where it lives |
| --- | --- | --- |
| Application source, running under Docker Compose | Built | `services/`, `frontend/`, `docker-compose.yml` |
| Repository hygiene (`.gitignore`, `.gitattributes`) | Built | `.gitignore`, `.gitattributes` |
| Compose topology contract test | Built | `tests/test_compose_contract.py` |
| Application identifier refactor | Built | `tests/test_no_legacy_identifiers.py` (enforced in CI) |
| Terraform EC2 provisioning | Built | `terraform/` |
| CI pipeline and security scanning | Built | `.github/workflows/ci-cd.yml` (`tests`, `security`, `changes`) |
| Image build and publish | Built | `ci-cd.yml` (`docker`) — build, Trivy scan, push to Docker Hub |
| Kubernetes manifests and Kustomize overlays | Built | `k8s/base/`, `k8s/overlays/prod/` |
| EC2 bootstrap scripts | Built | `scripts/01`–`06`, `scripts/run-all-ec2-bootstrap.sh` |
| ArgoCD GitOps reconciliation | Built | `k8s/argocd/`; `devops-circle` is Synced / Healthy |
| Application metrics and log pipeline | Built | `/prometheus` in 6 services, `k8s/base/60-servicemonitors.yaml`, `k8s/monitoring/` (Loki + Alloy) |
| CD verification and notifications | Built | `ci-cd.yml` (`gitops`, `cd-verify`, `notify`) |

The pipeline is a six-job DAG: `tests` → `security` → `changes` → `docker` →
`gitops` → `cd-verify`, with `notify` running last regardless of outcome. Every
job in the table above is green on `main`.

## Screenshots

Evidence that each layer is running, rather than only described. Captured from
the deployed environment on AWS EC2. The screenshots are ordered along the
delivery path rather than by feature, and are hosted externally rather than
committed to this repository.

### CI/CD — GitHub Actions

The six-job pipeline on `main`, green end to end.

<img src="https://i.ibb.co/kVVY5PZp/Screenshot-2026-09-29-052255.png"
     alt="GitHub Actions run for DevOps Circle CI/CD on main, showing the tests, security, changes, docker, gitops, and cd-verify jobs all completing successfully"
     width="900">

### GitOps — ArgoCD

The `devops-circle` application reconciled from `k8s/overlays/prod`. The
revision in the `Revision` column is the same commit SHA as the CI run above,
which is what makes the deployment traceable end to end.

<img src="https://i.ibb.co/nsZY8hLV/Screenshot-2026-09-29-045054.png"
     alt="ArgoCD application list showing devops-circle as Synced and Healthy, with the deployed revision matching the commit SHA from the CI run"
     width="900">

### Cluster state

Pods, deployments, and services on the k3s cluster behind the ingress.

<img src="https://i.ibb.co/pqTSqD7/Screenshot-2026-09-29-051948.png"
     alt="kubectl output showing pods, deployments, and services in the devops-circle namespace, all Running"
     width="900">

### Metrics — Grafana

Observability driven by the application rather than bolted on afterwards: the
services export their own Prometheus metrics as they serve traffic. Queue depth
and worker throughput are first-class because post creation is asynchronous by
design — `post-service` enqueues to Redis and returns immediately, and
`worker-service` drains the queue.

<img src="https://i.ibb.co/5XtbFXC3/Screenshot-2026-09-29-045008.png"
     alt="Grafana dashboard with request rate, latency, and Redis queue depth panels sourced from the services' own devops_circle Prometheus metrics"
     width="900">

### Scrape targets — Prometheus

All 21 scrape targets up, including cAdvisor, which needed adjusting for k3s and
containerd rather than Docker.

<img src="https://i.ibb.co/xtzdgB8q/Screenshot-2026-09-29-045021.png"
     alt="Prometheus targets page showing all 21 active scrape targets up, including the application ServiceMonitors and cAdvisor"
     width="900">

### Pipeline notification — SMTP

The `notify` job runs last regardless of outcome and emails the result.

<img src="https://i.ibb.co/HpNkf7jj/Screenshot-2026-09-29-122613.png"
     alt="SMTP server response confirming delivery of the CI/CD pipeline completion email"
     width="900">

### The application

Eight containers behind the Traefik Ingress: a React frontend, six FastAPI
services, and an asynchronous worker, on PostgreSQL and Redis.

<img src="https://i.ibb.co/FbwFPVqy/Screenshot-2026-09-29-044630.png"
     alt="DevOps Circle home UI served through the Traefik Ingress on the EC2 public IP"
     width="900">

## Running it locally

Requires Docker Desktop with Compose v2, Python 3.11+, and Node.js 20+.

```bash
git clone https://github.com/ahmed6394/DevOps-Circle.git
cd DevOps-Circle

cp .env.example .env
docker compose up --build -d
```

The UI is then at <http://localhost:3000>.

`.env` is required — the seven backend services load it via `env_file` and
Compose will not start them without it. `frontend` is the exception: it reads
no environment variables, because its Nginx configuration hardcodes the
upstream hosts. It still depends on all seven services, since the route table
points at them. `postgres` and `redis` read from `environment:` defaults and
start regardless.

Check the stack:

```bash
docker compose ps
docker compose logs -f worker-service
```

Verify Redis is accepting jobs:

```bash
docker exec -it devops-circle-redis redis-cli ping   # expect PONG
```

### Tests

```bash
python -m pip install -r requirements-dev.txt
pytest
```

```bash
cd frontend
npm install --legacy-peer-deps
npm test
npm run build
```

## Repository layout

```
services/          7 FastAPI microservices (6 HTTP + 1 queue worker)
frontend/          React UI and its Nginx configuration
tests/             contract, structure, and observability tests
terraform/         EC2 provisioning
k8s/               Kubernetes manifests, Kustomize overlays, ArgoCD, monitoring
scripts/           EC2 bootstrap scripts
.github/workflows/ CI/CD pipeline
```

The platform layers are written in dependency order: a layer that reads files
from the layer below it is never committed before that layer exists. Commits are
therefore individually runnable, and the history is a readable account of how
the platform came together rather than a single bulk drop.

## Development environment

Authored on Windows 11 with the primary toolchain — `git`, `pytest`, `npm`,
`kubectl`, and Terraform — running natively on Windows, with WSL2 used for
Docker image builds and shell tooling. The deployment target is Linux.

That split is deliberate, and `.gitattributes` exists because of it: the
bootstrap scripts are authored on Windows but executed on EC2 through a
shebang line, and a CRLF line ending would break them with
`bad interpreter: /usr/bin/env bash^M`. The file forces LF in the repository
regardless of any contributor's local `core.autocrlf` setting.

## Relationship to the course material

The application layer is **DevConnect Pro** by **bongoDev**, supplied to me as
course material for this assignment. The platform layer — Terraform, Kubernetes
manifests, and bootstrap scripts — is an **instructor-provided baseline**,
adapted in this repository rather than authored from nothing.

What is genuinely original work here is narrower, and stated precisely in
[CREDIT.md](CREDIT.md): the adaptations themselves, the test suite, the CI and
image pipelines, the observability configuration, the CD verification job, and
the documentation. Nothing in this repository should be read as claiming that
the Terraform, manifests, or bootstrap scripts are original.
