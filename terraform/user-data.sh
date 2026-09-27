#!/usr/bin/env bash
set -euxo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get update -y
apt-get install -y \
  ca-certificates \
  curl \
  git \
  unzip \
  jq \
  htop \
  gnupg \
  lsb-release \
  apt-transport-https \
  software-properties-common

# Basic sysctl settings helpful for Kubernetes/k3s networking.
cat >/etc/sysctl.d/99-devops-circle-k8s.conf <<'SYSCTL'
net.bridge.bridge-nf-call-iptables=1
net.bridge.bridge-nf-call-ip6tables=1
net.ipv4.ip_forward=1
SYSCTL

modprobe br_netfilter || true
sysctl --system || true

# Convenience banner for students.
cat >/etc/motd <<'MOTD'
============================================================
DevOps Circle EC2 Lab Machine
Provisioned by Terraform for Mahabub Ahmed.

Next steps:
1. git clone your DevOps Circle repository
2. cd into the project
3. run scripts/01-install-docker.sh, 02-install-k3s.sh,
   03-install-argocd.sh, 04-install-monitoring.sh,
   and 05-bootstrap-devops-circle.sh
============================================================
MOTD
