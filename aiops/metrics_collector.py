"""
=============================================================================
AIOps — Metrics Collector
=============================================================================
Collects metrics from Kubernetes cluster and app. Falls back to simulation.
=============================================================================
"""

import time
import logging
import random
import requests
from datetime import datetime, timezone

from kubernetes import client, config as k8s_config
from kubernetes.client.rest import ApiException

import config

logger = logging.getLogger("aiops.metrics")


class MetricsCollector:
    """Collects infrastructure and application metrics."""

    def __init__(self):
        self.namespace = config.K8S_NAMESPACE
        self.deployment = config.K8S_DEPLOYMENT
        self.simulation_mode = False

        try:
            k8s_config.load_incluster_config()
            logger.info("Loaded in-cluster K8s config")
        except k8s_config.ConfigException:
            try:
                k8s_config.load_kube_config(config_file=config.KUBECONFIG_PATH)
                logger.info("Loaded kubeconfig from file")
            except Exception as e:
                logger.warning(f"No K8s config: {e}. Using simulation mode.")
                self.simulation_mode = True

        if not self.simulation_mode:
            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()
            self.custom_api = client.CustomObjectsApi()

    def collect(self):
        """Collect all metrics. Returns structured dict."""
        if self.simulation_mode:
            return self._collect_simulated()

        metrics = {"timestamp": datetime.now(timezone.utc).isoformat(),
                   "pods": [], "deployment": {}, "app_health": {}, "aggregated": {}}
        try:
            metrics["pods"] = self._collect_pod_metrics()
            metrics["deployment"] = self._collect_deployment_status()
            metrics["app_health"] = self._check_app_health()
            metrics["aggregated"] = self._aggregate(metrics["pods"])
        except Exception as e:
            logger.error(f"Metrics error: {e}")
            return self._collect_simulated()
        return metrics

    def _collect_pod_metrics(self):
        pods = self.v1.list_namespaced_pod(
            self.namespace, label_selector=f"app={self.deployment}")
        try:
            md = self.custom_api.list_namespaced_custom_object(
                "metrics.k8s.io", "v1beta1", self.namespace, "pods")
            by_pod = {i["metadata"]["name"]: i for i in md.get("items", [])}
        except ApiException:
            by_pod = {}

        results = []
        for pod in pods.items:
            name = pod.metadata.name
            restarts = sum(cs.restart_count for cs in (pod.status.container_statuses or []))
            cpu, mem = 0.0, 0.0
            if name in by_pod:
                for c in by_pod[name].get("containers", []):
                    u = c.get("usage", {})
                    cpu += self._parse_cpu(u.get("cpu", "0"))
                    mem += self._parse_memory(u.get("memory", "0"))
            results.append({"name": name, "phase": pod.status.phase,
                           "restart_count": restarts, "cpu_millicores": cpu,
                           "memory_mb": mem, "ready": pod.status.phase == "Running"})
        return results

    def _collect_deployment_status(self):
        d = self.apps_v1.read_namespaced_deployment(self.deployment, self.namespace)
        return {"name": self.deployment, "replicas_desired": d.spec.replicas,
                "replicas_ready": d.status.ready_replicas or 0,
                "replicas_available": d.status.available_replicas or 0,
                "generation": d.metadata.generation}

    def _check_app_health(self):
        try:
            start = time.time()
            r = requests.get(f"{config.APP_SERVICE_URL}/health", timeout=5)
            rt = (time.time() - start) * 1000
            return {"status_code": r.status_code, "response_time_ms": round(rt, 2),
                    "healthy": r.status_code == 200}
        except requests.RequestException as e:
            logger.warning(f"Health check failed: {e}")
            return {"status_code": 0, "response_time_ms": -1, "healthy": False}

    def _aggregate(self, pods):
        if not pods:
            return {}
        n = len(pods)
        cpus = [p["cpu_millicores"] for p in pods]
        mems = [p["memory_mb"] for p in pods]
        return {"total_pods": n, "running_pods": sum(1 for p in pods if p["ready"]),
                "total_restarts": sum(p["restart_count"] for p in pods),
                "avg_cpu_percent": round(sum(cpus)/n/500*100, 2),
                "avg_memory_percent": round(sum(mems)/n/512*100, 2)}

    def _collect_simulated(self):
        spike = random.random() < 0.15
        cpu, mem, resp = random.uniform(20,40), random.uniform(30,50), random.uniform(50,150)
        if spike:
            t = random.choice(["cpu","memory","resp"])
            if t == "cpu": cpu = random.uniform(85, 99)
            elif t == "memory": mem = random.uniform(88, 98)
            else: resp = random.uniform(2000, 5000)
        return {"timestamp": datetime.now(timezone.utc).isoformat(), "simulated": True,
                "pods": [{"name": f"devops-app-sim-{i}", "phase": "Running",
                          "restart_count": random.randint(0,2), "cpu_millicores": cpu*5,
                          "memory_mb": mem*5.12, "ready": True} for i in range(3)],
                "deployment": {"name": self.deployment, "replicas_desired": 3,
                               "replicas_ready": 3, "replicas_available": 3, "generation": 1},
                "app_health": {"status_code": 200, "response_time_ms": round(resp,2), "healthy": True},
                "aggregated": {"total_pods": 3, "running_pods": 3, "total_restarts": random.randint(0,2),
                               "avg_cpu_percent": round(cpu,2), "avg_memory_percent": round(mem,2)}}

    @staticmethod
    def _parse_cpu(s):
        if s.endswith("n"): return float(s[:-1])/1e6
        if s.endswith("u"): return float(s[:-1])/1e3
        if s.endswith("m"): return float(s[:-1])
        return float(s)*1000

    @staticmethod
    def _parse_memory(s):
        if s.endswith("Ki"): return float(s[:-2])/1024
        if s.endswith("Mi"): return float(s[:-2])
        if s.endswith("Gi"): return float(s[:-2])*1024
        return float(s)/(1024*1024)
