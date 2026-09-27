# DevOps Circle

A 10-service microservices social platform, delivered to a Kubernetes cluster
on AWS EC2 through a CI/CD and GitOps pipeline, with metrics and logs collected
from the application's own instrumentation.

> **Status: under construction.**
>
> This repository is being built in 23 sequential commits. The application runs
> locally today. The platform layers — Terraform, CI, Kubernetes manifests,
> ArgoCD, observability, and CD verification — are added in later commits and
> are listed as planned below so that no part of this README describes
> something that does not exist yet.
>
> The application layer is imported from a third-party teaching project and
> carries no license from its author. **This repository is private for that
> reason.** See [CREDIT.md](CREDIT.md) for full attribution and the
> redistribution path.

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
| `frontend` | 3000 | React UI served by Nginx (no backend config) | all app services |
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

## Build status

| Layer | Status |
| --- | --- |
| Application source, running under Docker Compose | Built |
| Repository hygiene (`.gitignore`, `.gitattributes`) | Built |
| Compose topology contract test | Built |
| Application identifier refactor | Planned |
| Terraform EC2 provisioning | Planned |
| CI pipeline and security scanning | Planned |
| Image build and publish | Planned |
| Kubernetes manifests and Kustomize overlays | Planned |
| EC2 bootstrap scripts | Planned |
| ArgoCD GitOps reconciliation | Planned |
| Application metrics and log pipeline | Planned |
| CD verification and notifications | Planned |

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
Compose will not start them without it. `frontend` is the exception: it serves
static assets through Nginx and holds no backend configuration. `postgres` and
`redis` read from `environment:` defaults and start regardless.

Check the stack:

```bash
docker compose ps
docker compose logs -f worker-service
```

Verify Redis is accepting jobs:

```bash
docker exec -it cloudconnect-redis redis-cli ping   # expect PONG
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
services/          8 FastAPI microservices
frontend/          React UI and its Nginx configuration
tests/             contract and verification tests
terraform/         EC2 provisioning                    (planned)
k8s/               Kubernetes manifests, Kustomize     (planned)
scripts/           EC2 bootstrap scripts               (planned)
.github/workflows/ CI/CD pipelines                     (planned)
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

## Relationship to the upstream project

The application layer comes from **DevConnect Pro** by **bongoDev**, a teaching
project with no license file. The platform layer is an **instructor-provided
baseline**, adapted in this repository rather than authored from nothing. What
is genuinely original work here is narrower, and stated precisely in
[CREDIT.md](CREDIT.md): the adaptations themselves, the test suite, the CI and
image pipelines, the observability configuration, the CD verification job, and
the documentation.

Nothing in this repository should be read as claiming that the Terraform,
manifests, or bootstrap scripts are original.
