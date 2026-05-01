"""
=============================================================================
AIOps — Decision Engine
=============================================================================
Analyzes anomaly reports to determine root cause and prescribe remediation
actions. Implements cooldown to prevent action storms.
=============================================================================
"""

import time
import logging

import config

logger = logging.getLogger("aiops.decision")


class DecisionEngine:
    """Root cause analysis and action prescription engine."""

    def __init__(self):
        # Track last action time per resource to enforce cooldown
        self.last_action_time = {}
        self.cooldown = config.ACTION_COOLDOWN

    def decide(self, anomaly_report, metrics):
        """
        Analyze anomalies and decide on remediation actions.

        Args:
            anomaly_report: Output from AnomalyDetector.analyze()
            metrics: Current metrics from MetricsCollector.collect()

        Returns:
            list: Actions to take, e.g.:
                [{"action": "scale_up", "reason": "High CPU", "params": {...}}]
        """
        if not anomaly_report.get("is_anomaly"):
            return []

        actions = []
        anomalies = anomaly_report.get("anomalies", [])

        for anomaly in anomalies:
            anomaly_type = anomaly.get("type", "")
            severity = anomaly.get("severity", "warning")

            # Only act on critical anomalies (log warnings)
            if severity == "warning":
                logger.info(f"Warning anomaly (no action): {anomaly_type}")
                continue

            # Determine action based on anomaly type
            action = self._map_anomaly_to_action(anomaly, metrics)
            if action:
                # Check cooldown
                resource_key = f"{action['action']}:{action.get('target', 'default')}"
                if self._check_cooldown(resource_key):
                    actions.append(action)
                    self.last_action_time[resource_key] = time.time()
                else:
                    logger.info(
                        f"Action {resource_key} in cooldown, skipping"
                    )

        if actions:
            logger.warning(f"Decision: {len(actions)} action(s) prescribed")
            for a in actions:
                logger.warning(f"  → {a['action']}: {a['reason']}")

        return actions

    def _map_anomaly_to_action(self, anomaly, metrics):
        """
        Map an anomaly type to a remediation action.

        Decision matrix:
            high_cpu            → Scale up deployment
            high_memory         → Restart affected pods
            high_response_time  → Scale up deployment
            crash_loop          → Rollback deployment
            pod_unavailable     → Restart failed pods
            health_check_failed → Restart pods + scale up
        """
        anomaly_type = anomaly.get("type", "")
        deployment = metrics.get("deployment", {})
        current_replicas = deployment.get("replicas_desired", 3)

        if anomaly_type == "high_cpu":
            new_replicas = min(
                current_replicas + config.SCALE_INCREMENT,
                config.MAX_REPLICAS
            )
            if new_replicas > current_replicas:
                return {
                    "action": "scale_up",
                    "target": config.K8S_DEPLOYMENT,
                    "reason": f"High CPU ({anomaly.get('value', 0):.1f}%)",
                    "params": {"replicas": new_replicas},
                    "priority": 1,
                }

        elif anomaly_type == "high_memory":
            return {
                "action": "restart_pods",
                "target": config.K8S_DEPLOYMENT,
                "reason": f"High memory ({anomaly.get('value', 0):.1f}%)",
                "params": {"max_restart": 1},
                "priority": 2,
            }

        elif anomaly_type == "high_response_time":
            new_replicas = min(
                current_replicas + config.SCALE_INCREMENT,
                config.MAX_REPLICAS
            )
            if new_replicas > current_replicas:
                return {
                    "action": "scale_up",
                    "target": config.K8S_DEPLOYMENT,
                    "reason": f"High response time ({anomaly.get('value', 0):.0f}ms)",
                    "params": {"replicas": new_replicas},
                    "priority": 1,
                }

        elif anomaly_type == "crash_loop":
            return {
                "action": "rollback",
                "target": config.K8S_DEPLOYMENT,
                "reason": f"Pod crash loop ({anomaly.get('value', 0)} restarts)",
                "params": {},
                "priority": 0,  # Highest priority
            }

        elif anomaly_type in ("pod_unavailable", "health_check_failed"):
            return {
                "action": "restart_pods",
                "target": config.K8S_DEPLOYMENT,
                "reason": f"Pods unhealthy: {anomaly_type}",
                "params": {"max_restart": 2},
                "priority": 1,
            }

        return None

    def _check_cooldown(self, resource_key):
        """Check if the cooldown period has passed for a resource."""
        last_time = self.last_action_time.get(resource_key, 0)
        elapsed = time.time() - last_time
        return elapsed >= self.cooldown
