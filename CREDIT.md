# Attribution and Licensing

## Summary

This repository is a **fork-and-rebuild of an application layer** on top of
which an original DevOps platform is being built. The two parts have different
origins, and the boundary between them is deliberate and permanent.

| Layer | Origin | License |
| --- | --- | --- |
| Application source (`services/`, `frontend/`, `docker-compose.yml`, `.env.example`, `pytest.ini`, `requirements-dev.txt`) | Third party — see below | **Undetermined.** No license file was present in the source material. |
| DevOps platform (`terraform/`, `k8s/`, `scripts/`, `.github/`, `tests/`, `.gitignore`, `.gitattributes`, `README.md`, `CREDIT.md`) | Original work authored in this repository | To be declared once the application question below is resolved. |

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
terraform/           EC2 provisioning
k8s/                 Kubernetes manifests and Kustomize overlays
scripts/             EC2 bootstrap scripts
.github/workflows/   CI/CD pipelines
tests/               contract and verification tests
```

Upstream copies of the platform layers were used as a technical reference while
authoring. They are not present in this repository and are not in its history.

## Modifications to the application layer

Commit 1 imports the application unmodified. Subsequent commits rename internal
identifiers — infrastructure object names, PostgreSQL identifiers, Prometheus
metric names, Redis keys, and browser storage keys — from the upstream brand to
this project's name. These are mechanical identifier substitutions required
because a hyphen is not valid in a PostgreSQL identifier or a Prometheus metric
name. No application logic, API contract, or behavior is changed by the rename.
