"""
=============================================================================
AIOps — Anomaly Detector
=============================================================================
Dual detection: Isolation Forest ML model + threshold-based fallback.
Flags anomalies if either method triggers.
=============================================================================
"""

import logging
import numpy as np
from collections import deque
from sklearn.ensemble import IsolationForest

import config

logger = logging.getLogger("aiops.anomaly")


class AnomalyDetector:
    """Detects anomalies using Isolation Forest and threshold-based detection."""

    def __init__(self):
        # Sliding window of historical metrics for ML training
        self.history = deque(maxlen=config.METRICS_WINDOW_SIZE)
        self.model = None
        self.is_trained = False
        self.thresholds = config.THRESHOLDS

    def analyze(self, metrics):
        """
        Analyze metrics for anomalies using both ML and threshold detection.

        Args:
            metrics: Dict with 'aggregated' and 'app_health' sub-dicts.

        Returns:
            dict: {
                "is_anomaly": bool,
                "anomalies": [{"type": str, "severity": str, "value": float, "threshold": float}],
                "method": "ml" | "threshold" | "both"
            }
        """
        aggregated = metrics.get("aggregated", {})
        app_health = metrics.get("app_health", {})

        # Build feature vector for this data point
        feature = self._extract_features(aggregated, app_health)
        self.history.append(feature)

        anomalies = []
        ml_anomaly = False
        threshold_anomaly = False

        # --- Method 1: Threshold-based detection (always active) ---
        threshold_results = self._threshold_detect(aggregated, app_health, metrics)
        if threshold_results:
            threshold_anomaly = True
            anomalies.extend(threshold_results)

        # --- Method 2: Isolation Forest ML detection ---
        if len(self.history) >= config.MIN_TRAINING_SAMPLES:
            ml_result = self._ml_detect(feature)
            if ml_result:
                ml_anomaly = True
                if not threshold_anomaly:
                    anomalies.append({
                        "type": "ml_detected",
                        "severity": "warning",
                        "detail": "Isolation Forest flagged abnormal pattern",
                    })

        is_anomaly = ml_anomaly or threshold_anomaly

        if is_anomaly:
            method = "both" if (ml_anomaly and threshold_anomaly) else (
                "ml" if ml_anomaly else "threshold")
            logger.warning(f"ANOMALY DETECTED [{method}]: {anomalies}")

        return {
            "is_anomaly": is_anomaly,
            "anomalies": anomalies,
            "method": "both" if (ml_anomaly and threshold_anomaly) else (
                "ml" if ml_anomaly else "threshold") if is_anomaly else "none",
        }

    def _extract_features(self, aggregated, app_health):
        """Extract a numerical feature vector from metrics."""
        return [
            aggregated.get("avg_cpu_percent", 0),
            aggregated.get("avg_memory_percent", 0),
            app_health.get("response_time_ms", 0),
            aggregated.get("total_restarts", 0),
            aggregated.get("running_pods", 0),
        ]

    def _threshold_detect(self, aggregated, app_health, metrics):
        """Detect anomalies using static thresholds from config."""
        results = []

        # CPU check
        cpu = aggregated.get("avg_cpu_percent", 0)
        if cpu >= self.thresholds["cpu_percent"]["critical"]:
            results.append({"type": "high_cpu", "severity": "critical",
                           "value": cpu, "threshold": self.thresholds["cpu_percent"]["critical"]})
        elif cpu >= self.thresholds["cpu_percent"]["warning"]:
            results.append({"type": "high_cpu", "severity": "warning",
                           "value": cpu, "threshold": self.thresholds["cpu_percent"]["warning"]})

        # Memory check
        mem = aggregated.get("avg_memory_percent", 0)
        if mem >= self.thresholds["memory_percent"]["critical"]:
            results.append({"type": "high_memory", "severity": "critical",
                           "value": mem, "threshold": self.thresholds["memory_percent"]["critical"]})
        elif mem >= self.thresholds["memory_percent"]["warning"]:
            results.append({"type": "high_memory", "severity": "warning",
                           "value": mem, "threshold": self.thresholds["memory_percent"]["warning"]})

        # Response time check
        rt = app_health.get("response_time_ms", 0)
        if rt > 0:
            if rt >= self.thresholds["response_time_ms"]["critical"]:
                results.append({"type": "high_response_time", "severity": "critical",
                               "value": rt, "threshold": self.thresholds["response_time_ms"]["critical"]})
            elif rt >= self.thresholds["response_time_ms"]["warning"]:
                results.append({"type": "high_response_time", "severity": "warning",
                               "value": rt, "threshold": self.thresholds["response_time_ms"]["warning"]})

        # Pod restart / crash loop check
        restarts = aggregated.get("total_restarts", 0)
        if restarts >= self.thresholds["pod_restart_count"]["critical"]:
            results.append({"type": "crash_loop", "severity": "critical",
                           "value": restarts, "threshold": self.thresholds["pod_restart_count"]["critical"]})

        # Health check failure
        if not app_health.get("healthy", True):
            results.append({"type": "health_check_failed", "severity": "critical",
                           "value": app_health.get("status_code", 0), "threshold": 200})

        # Pod availability check
        total = aggregated.get("total_pods", 0)
        running = aggregated.get("running_pods", 0)
        if total > 0 and running < total:
            results.append({"type": "pod_unavailable", "severity": "critical",
                           "value": running, "threshold": total})

        return results

    def _ml_detect(self, feature):
        """Run Isolation Forest anomaly detection."""
        try:
            X = np.array(list(self.history))

            # Retrain model periodically
            if not self.is_trained or len(self.history) % 10 == 0:
                self.model = IsolationForest(
                    contamination=config.IF_CONTAMINATION,
                    n_estimators=config.IF_N_ESTIMATORS,
                    random_state=config.IF_RANDOM_STATE,
                )
                self.model.fit(X)
                self.is_trained = True
                logger.debug(f"Retrained IF model on {len(X)} samples")

            # Predict: -1 = anomaly, 1 = normal
            prediction = self.model.predict([feature])
            score = self.model.score_samples([feature])[0]

            if prediction[0] == -1:
                logger.info(f"IF anomaly score: {score:.4f}")
                return True

        except Exception as e:
            logger.error(f"ML detection error: {e}")

        return False
