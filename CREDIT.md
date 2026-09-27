# Attribution and Licensing

## Summary

This repository is a **fork-and-rebuild of an application layer** on top of
which an original DevOps platform is being built. The two parts have different
origins, and the boundary between them is deliberate and permanent.

| Layer | Origin | License |
| --- | --- | --- |
| Application source (`services/`, `frontend/`, `docker-compose.yml`, `.env.example`, `pytest.ini`, `requirements-dev.txt`) | Third party — see [below](#the-upstream-application) | **Undetermined.** No license file was present in the source material. |
| Platform baseline (`terraform/`, `k8s/`, `scripts/`) | Instructor-provided — see [below](#the-instructor-provided-platform-baseline) | As supplied with the course materials |
| Adaptations to the baseline, and original work (`tests/`, `.github/`, `.gitignore`, `.gitattributes`, `README.md`, `CREDIT.md`, `task_plan.md`, `progress.md`, `findings.md`) | Authored in this repository | To be declared once the application question below is resolved |

Read the third row carefully: it is narrower than it may appear. The authorizations
and fixes listed in
[What is ours](#what-is-ours) are real work, but the underlying structure of
every layer they adapt is the instructor's.

## The upstream application

| Field | Value |
| --- | --- |
| Original project name | **DevConnect Pro** |
| Author / brand | **bongoDev** |
| Description | A 10-service microservices-style social application built as a teaching lab for DevOps and Cloud Engineering students |
| Source URL | **Not recorded in the source material** — see below |
| License | **None found.** No `LICENSE`, `COPYING`, or SPDX header exists anywhere in the upstream tree |
| Obtained from | Provided to this repository's author as a starting project |

The upstream project's own README describes it explicitly as a lab: *"This
project is intentionally designed as a strong DevOps learning project, not a
fully managed production AWS architecture,"* and closes with a
"What students should submit" checklist.

### Why the source URL is blank

Every GitHub reference inside the upstream files is a placeholder —
`https://github.com/YOUR_GITHUB_ORG/YOUR_REPO.git` in
`scripts/05-bootstrap-devconnect.sh`, and `<your-org-or-user>/<your-repo>` in
the README. The upstream tree therefore does not identify its own origin, and
no email address, copyright line, or author URL appears in any file.

This field is left deliberately unfilled rather than guessed. **The repository
owner must fill it in** from wherever the material was originally obtained, so
that a future reader can trace the provenance of the application layer.

## Redistribution status

Because the upstream material carries no license, the default position under
copyright is **exclusive rights reserved**. A project published without an
express grant grants no permission to copy, modify, or redistribute it.

Consequently this repository is being developed as a **private repository**, and
that is a licensing decision, not a preference. Two paths forward:

1. **Obtain written permission** from the upstream author, recording the grant
   here, then publish. This is the intended path.
2. **Replace the application layer** with an independently written or
   permissively licensed application, keeping the DevOps platform. The platform
   is the substance of this project and is not affected either way.

If permission is refused, path 2 is taken before anything is made public. The
platform work in commits 2 onward does not need to be redone — only the app
source under `services/` and `frontend/` and the Compose topology are affected.

## What was taken, and what was written

Deliberately taken from upstream, unmodified:

```
services/            8 FastAPI microservices
frontend/            React UI served by Nginx
docker-compose.yml   10-service local topology
.env.example         environment contract
pytest.ini           test configuration
requirements-dev.txt pinned test dependencies
```

Deliberately **not** taken from upstream, and written from scratch in this
repository:

```
tests/               contract and verification tests
```

## The instructor-provided platform baseline

The platform layers are supplied by the course instructor as a working
baseline:

```
terraform/           EC2 provisioning
k8s/                 Kubernetes manifests and Kustomize overlays
scripts/             EC2 bootstrap scripts
```

These are **not original work by this repository's author.** They are adapted
here, and the adaptations are the contribution. Each adaptation is a separate
commit so the delta is reviewable:

| Adaptation | Rationale |
| --- | --- |
| S3 remote backend with versioning, encryption, and locking | Local state is destroyed when the instance is replaced, after which `terraform destroy` can no longer find the instance |
| Separate `terraform/bootstrap` module for the state bucket | A backend cannot reference a bucket that does not exist yet |
| `t3.large` instead of the baseline's smaller type | The full stack needs roughly 5.2 GB; the baseline size OOMs |
| `chmod +x` moved inside the entry script | Git on Windows cannot record mode `100755`, so a fresh clone is not executable. As a manual README step it is a step people forget. |
| `usermod -aG docker` instead of `newgrp docker` | `newgrp` only changes group membership inside a spawned subshell, so the current session is unaffected |
| `set -euo pipefail` and idempotency on every script | Fail fast; re-runnable after a partial failure |
| Healthcheck-to-probe translation | Compose `healthcheck` and `service_healthy` startup ordering have no direct equivalent in Kubernetes |
| StatefulSet and PVC for `postgres` and `redis` | The baseline's `Deployment` cannot express the volume claim these need |
| CI gate, security scanning, image build and publish | Not present in the baseline |
| Image tag automation against the commit SHA | Required for traceable deployments |
| ServiceMonitors, Loki log shipping, Grafana dashboard | Not present in the baseline |
| CD verification job | Not present in the baseline |
| This repository's documentation | Written here |

The instructor baseline is retained outside the working tree at
`E:\DevOps\bongoDev\_upstream-platform-ref\` while it is being adapted, so that
it cannot enter the repository by accident.

## What is ours

Two things, and they should be stated precisely rather than generously:

1. **The adaptations above**, each in its own commit.
2. **Everything absent from the baseline** — the test suite, the CI pipeline,
   the image pipeline, the observability configuration, the CD verification
   job, and the documentation.

No claim is made that the Terraform, manifests, or scripts are original.

## Modifications to the application layer

Commit 1 imports the application unmodified. Subsequent commits rename internal
identifiers — infrastructure object names, PostgreSQL identifiers, Prometheus
metric names, Redis keys, and browser storage keys — from the upstream brand to
this project's name. These are mechanical identifier substitutions required
because a hyphen is not valid in a PostgreSQL identifier or a Prometheus metric
name. No application logic, API contract, or behavior is changed by the rename.
