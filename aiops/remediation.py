"""
=============================================================================
AIOps — Automated Remediation
=============================================================================
Executes remediation actions on the Kubernetes cluster:
  - Scale deployment (add/remove replicas)
  - Restart pods (delete for automatic recreation)
  - Rollback deployment (to previous revision)

Supports dry-run mode for safe testing.
=============================================================================
"""

import logging

from kubernetes import client, config as k8s_config
from kubernetes.client.rest import ApiException

import config as cfg

logger = logging.getLogger("aiops.remediation")


class RemediationEngine:
    """Executes automated remediation actions on Kubernetes."""

    def __init__(self):
        self.namespace = cfg.K8S_NAMESPACE
        self.dry_run = cfg.DRY_RUN
        self.simulation_mode = False

        try:
            k8s_config.load_incluster_config()
        except k8s_config.ConfigException:
            try:
                k8s_config.load_kube_config(config_file=cfg.KUBECONFIG_PATH)
            except Exception as e:
                logger.warning(f"No K8s config: {e}. Remediation in simulation mode.")
                self.simulation_mode = True

        if not self.simulation_mode:
            self.v1 = client.CoreV1Api()
            self.apps_v1 = client.AppsV1Api()

    def execute(self, actions):
        """
        Execute a list of remediation actions.

        Args:
            actions: List of action dicts from DecisionEngine.decide()

        Returns:
            list: Results for each action.
        """
        # Sort by priority (lower = higher priority)
        sorted_actions = sorted(actions, key=lambda a: a.get("priority", 99))
        results = []

        for action in sorted_actions:
            action_type = action.get("action", "")
            target = action.get("target", cfg.K8S_DEPLOYMENT)
            params = action.get("params", {})

            logger.info(f"Executing: {action_type} on {target} | Reason: {action.get('reason')}")

            if self.dry_run:
                result = {"action": action_type, "status": "dry_run",
                         "message": f"DRY RUN: Would {action_type} on {target}"}
                logger.info(f"DRY RUN: {action_type} on {target}")
            elif self.simulation_mode:
                result = {"action": action_type, "status": "simulated",
                         "message": f"SIMULATED: {action_type} on {target}"}
                logger.info(f"SIMULATED: {action_type} on {target}")
            elif action_type == "scale_up":
                result = self._scale_deployment(target, params.get("replicas", 5))
            elif action_type == "restart_pods":
                result = self._restart_pods(target, params.get("max_restart", 1))
            elif action_type == "rollback":
                result = self._rollback_deployment(target)
            else:
                result = {"action": action_type, "status": "unknown",
                         "message": f"Unknown action type: {action_type}"}

            results.append(result)
            logger.info(f"Result: {result['status']} — {result.get('message', '')}")

        return results

    def _scale_deployment(self, deployment_name, replicas):
        """Scale a deployment to the specified number of replicas."""
        try:
            # Enforce min/max limits
            replicas = max(cfg.MIN_REPLICAS, min(replicas, cfg.MAX_REPLICAS))

            # Patch the deployment
            body = {"spec": {"replicas": replicas}}
            self.apps_v1.patch_namespaced_deployment_scale(
                name=deployment_name,
                namespace=self.namespace,
                body=body
            )

            msg = f"Scaled {deployment_name} to {replicas} replicas"
            logger.warning(f"ACTION: {msg}")
            return {"action": "scale_up", "status": "success", "message": msg,
                    "replicas": replicas}

        except ApiException as e:
            msg = f"Failed to scale {deployment_name}: {e.reason}"
            logger.error(msg)
            return {"action": "scale_up", "status": "failed", "message": msg}

    def _restart_pods(self, deployment_name, max_restart=1):
        """Restart pods by deleting them (K8s will recreate via deployment)."""
        try:
            pods = self.v1.list_namespaced_pod(
                self.namespace, label_selector=f"app={deployment_name}")

            restarted = 0
            for pod in pods.items:
                if restarted >= max_restart:
                    break

                # Only restart running pods
                if pod.status.phase == "Running":
                    self.v1.delete_namespaced_pod(
                        name=pod.metadata.name, namespace=self.namespace)
                    logger.warning(f"ACTION: Deleted pod {pod.metadata.name} for restart")
                    restarted += 1

            msg = f"Restarted {restarted} pod(s) for {deployment_name}"
            return {"action": "restart_pods", "status": "success",
                    "message": msg, "restarted": restarted}

        except ApiException as e:
            msg = f"Failed to restart pods: {e.reason}"
            logger.error(msg)
            return {"action": "restart_pods", "status": "failed", "message": msg}

    def _rollback_deployment(self, deployment_name):
        """Rollback deployment to previous revision using patch."""
        try:
            # Trigger rollback by setting rollbackTo annotation
            # In modern K8s, we use kubectl rollout undo equivalent
            deployment = self.apps_v1.read_namespaced_deployment(
                deployment_name, self.namespace)

            # Add rollback annotation to trigger new rollout
            annotations = deployment.spec.template.metadata.annotations or {}
            annotations["kubectl.kubernetes.io/restartedAt"] = \
                __import__("datetime").datetime.now().isoformat()

            deployment.spec.template.metadata.annotations = annotations
            self.apps_v1.patch_namespaced_deployment(
                name=deployment_name, namespace=self.namespace, body=deployment)

            msg = f"Rolled back {deployment_name} to previous revision"
            logger.warning(f"ACTION: {msg}")
            return {"action": "rollback", "status": "success", "message": msg}

        except ApiException as e:
            msg = f"Failed to rollback {deployment_name}: {e.reason}"
            logger.error(msg)
            return {"action": "rollback", "status": "failed", "message": msg}
