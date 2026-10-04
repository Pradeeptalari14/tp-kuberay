# ☸️ tp-kuberay: KubeRay Operator Studio

Production-ready [KubeRay](https://github.com/ray-project/kuberay) manifests and workloads for running Ray on Kubernetes:
long-lived **RayClusters**, batch **RayJobs** that delete themselves when finished, and **RayServices** with zero-downtime Ray Serve upgrades.

🔗 **Interactive studio:** [talaripradeep.info/tools/kuberay/](https://talaripradeep.info/tools/kuberay/). Generate these manifests with your own worker profile, autoscaling limits and fault-tolerance settings.

![KubeRay operator architecture](docs/kuberay_flow.png)

## What's inside

| Path | Purpose |
|------|---------|
| `manifests/redis-gcs-ft.yaml` | Redis + Secret backing **GCS fault tolerance** (head pod can restart without losing cluster state) |
| `manifests/raycluster.yaml` | Interactive `RayCluster`: head + autoscaling GPU worker group (1 → 8), autoscaler v2 |
| `manifests/rayjob.yaml` | Batch `RayJob`: Ray Train job, `shutdownAfterJobFinishes` + TTL so GPUs are released |
| `manifests/rayservice.yaml` | `RayService`: Ray Serve app with `upgradeStrategy: NewCluster` (blue/green) |
| `monitoring/podmonitor.yaml` | Prometheus Operator `PodMonitor` + alert when pinned at `maxReplicas` |
| `workloads/` | Python code run by each resource (`cluster_tasks.py`, `train_job.py`, `serve_app.py`) |
| `scripts/install-operator.sh` | Installs the KubeRay operator v1.3.0 via Helm |
| `scripts/validate.sh` | Server-side dry-run of every manifest against the live CRD schemas |
| `kind-cluster.yaml` | 3-node local cluster for testing |

## Quick start (local, kind)

```bash
kind create cluster --config kind-cluster.yaml
bash scripts/install-operator.sh          # KubeRay operator + CRDs
kubectl apply -f manifests/redis-gcs-ft.yaml
kubectl apply -f manifests/raycluster.yaml
kubectl get rayclusters -n ray-system
kubectl port-forward -n ray-system svc/ray-cluster-a100-head-svc 8265:8265   # Ray dashboard
```

> On kind there are no GPUs. To try the cluster locally, remove the `nvidia.com/gpu` requests, the `nodeSelector` and the `tolerations` from the worker group (or pick the **CPU** profile in the studio).

## Production guardrails baked in

- **Pinned images**: `rayproject/ray:2.41.0-py311(-gpu)`, never `:latest`
- **Head pod is not a worker**: `num-cpus: "0"` keeps tasks off the head (protects the GCS)
- **Requests = limits** on every container for predictable scheduling (Guaranteed QoS)
- **Autoscaler v2** (`RAY_enable_autoscaler_v2=1`, worker `restartPolicy: Never`) with `idleTimeoutSeconds: 120`
- **GCS fault tolerance** via external Redis; credentials come from a Secret, never inline
- **RayJob teardown**: `shutdownAfterJobFinishes: true`, `ttlSecondsAfterFinished: 300`, `activeDeadlineSeconds`
- **Blue/green Serve upgrades**: a new cluster is warmed up before traffic switches

> [!WARNING]
> `manifests/redis-gcs-ft.yaml` ships a placeholder Redis password (`change-me`). In production, source it from External Secrets / Vault / your cloud secret manager, and use a managed HA Redis (e.g. Memorystore, ElastiCache) instead of the single-replica Deployment.

## Compatibility

| Component | Version |
|-----------|---------|
| KubeRay operator | **v1.3.0+** (uses `gcsFaultToleranceOptions` and `upgradeStrategy`) |
| Ray | 2.41.0 |
| Kubernetes | 1.27+ |

## CI

`.github/workflows/validate.yml` spins up a kind cluster, installs the KubeRay operator, and runs `kubectl apply --dry-run=server` on every manifest, so schema mistakes fail the build. It also byte-compiles the Python workloads.

## License

MIT © 2026 Talari Pradeep
