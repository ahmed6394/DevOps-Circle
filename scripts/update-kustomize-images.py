#!/usr/bin/env python3
"""Update all DevOps Circle image tags in k8s/overlays/prod/kustomization.yaml."""
from __future__ import annotations

import re
import sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit("Usage: update-kustomize-images.py <new-tag>")

new_tag = sys.argv[1]
path = Path("k8s/overlays/prod/kustomization.yaml")
text = path.read_text()

images = [
    "ahmed63/devops-circle-frontend",
    "ahmed63/devops-circle-auth-service",
    "ahmed63/devops-circle-user-service",
    "ahmed63/devops-circle-post-service",
    "ahmed63/devops-circle-like-service",
    "ahmed63/devops-circle-comment-service",
    "ahmed63/devops-circle-analytics-service",
    "ahmed63/devops-circle-worker-service",
]

for image in images:
    pattern = rf"(name:\s*{re.escape(image)}\n\s*newTag:\s*)([^\n]+)"
    text, count = re.subn(pattern, rf"\g<1>{new_tag}", text)
    if count != 1:
        raise SystemExit(f"Could not update image tag for {image}")

path.write_text(text)
print(f"Updated DevOps Circle image tags to {new_tag}")
