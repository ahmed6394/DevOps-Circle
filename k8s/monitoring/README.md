# Monitoring Stack

This folder contains values/manifests for:

- kube-prometheus-stack: Prometheus, Grafana, Alertmanager, node-exporter, kube-state-metrics
- Loki: log storage
- Grafana Alloy: Kubernetes pod log collection to Loki
- cAdvisor: container-level resource metrics

## Prerequisites (single-node k3s)

cAdvisor needs higher inotify limits than the Ubuntu defaults:

```bash
printf 'fs.inotify.max_user_instances=1024\nfs.inotify.max_user_watches=524288\n' \
  | sudo tee /etc/sysctl.d/99-cadvisor.conf
sudo sysctl --system
```

If nodes cannot pull from Docker Hub (rate limits / no egress), pre-cache the
chart images, plus the local-path helper image used to provision PVCs:

```bash
sudo /var/lib/rancher/k3s/data/current/bin/ctr --address /run/k3s/containerd/containerd.sock \
  -n k8s.io images pull docker.io/rancher/mirrored-library-busybox:1.37.0
```

Install with:

```bash
./scripts/04-install-monitoring.sh
```

Access Grafana locally from the EC2 machine:

```bash
kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3001:80
```

Login as `admin` with the password from `GRAFANA_PASSWORD` (exported by the
installer, e.g. from `.env`). Example remote access via SSH tunnel:

```bash
ssh -i <key> -L 3001:localhost:3001 ubuntu@<ec2-host>
# then, on the EC2: kubectl -n monitoring port-forward svc/kube-prometheus-stack-grafana 3001:80
```

