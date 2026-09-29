# Monitoring Stack

This folder contains values/manifests for:

- kube-prometheus-stack: Prometheus, Grafana, Alertmanager, node-exporter, kube-state-metrics
- Loki: log storage
- Grafana Alloy: Kubernetes pod log collection to Loki
- cAdvisor: container-level resource metrics

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

