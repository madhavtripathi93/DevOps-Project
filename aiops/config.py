"""
=============================================================================
AIOps Configuration
=============================================================================
Central configuration for the AIOps self-healing module.
All thresholds, intervals, and Kubernetes settings are defined here.
=============================================================================
"""

import os

# =============================================================================
# Kubernetes Settings
# =============================================================================

# Namespace where the application is deployed
K8S_NAMESPACE = os.environ.get("K8S_NAMESPACE", "devops-project")

# Name of the Kubernetes deployment to monitor
K8S_DEPLOYMENT = "agent-backend"

# Kubeconfig path (None = use in-cluster config or default ~/.kube/config)
KUBECONFIG_PATH = None

# =============================================================================
# Monitoring Intervals
# =============================================================================

# How often to collect metrics and run anomaly detection (seconds)
MONITORING_INTERVAL = 15

# Size of the sliding window for anomaly detection (number of data points)
METRICS_WINDOW_SIZE = 50

# Minimum number of data points before ML model starts working
MIN_TRAINING_SAMPLES = 10

# =============================================================================
# Anomaly Detection Thresholds
# =============================================================================
# These are used by the threshold-based detector as a fallback
# and as a sanity check for the ML-based detector.

THRESHOLDS = {
    "cpu_percent": {
        "warning": 70.0,     # Warning level (log only)
        "critical": 85.0,    # Critical level (trigger action)
    },
    "memory_percent": {
        "warning": 75.0,
        "critical": 90.0,
    },
    "response_time_ms": {
        "warning": 500.0,    # 500ms warning
        "critical": 2000.0,  # 2s critical
    },
    "error_rate": {
        "warning": 0.05,     # 5% error rate warning
        "critical": 0.10,    # 10% error rate critical
    },
    "pod_restart_count": {
        "warning": 3,        # 3 restarts = warning
        "critical": 5,       # 5 restarts = critical (crash loop)
    },
}

# =============================================================================
# Isolation Forest Settings
# =============================================================================

# Contamination parameter (expected proportion of anomalies)
IF_CONTAMINATION = 0.1

# Number of estimators (trees) in the Isolation Forest
IF_N_ESTIMATORS = 100

# Random state for reproducibility
IF_RANDOM_STATE = 42

# =============================================================================
# Remediation Settings
# =============================================================================

# Cooldown period between actions on the same resource (seconds)
ACTION_COOLDOWN = 120

# Maximum number of replicas to scale to
MAX_REPLICAS = 10

# Minimum number of replicas to maintain
MIN_REPLICAS = 3

# Number of replicas to add when scaling out
SCALE_INCREMENT = 2

# Enable dry-run mode (log actions without executing)
DRY_RUN = False

# =============================================================================
# Application Endpoint
# =============================================================================

# URL of the application service (for health checks and metrics)
# We will use the internal Kubernetes DNS name by default
APP_SERVICE_URL = os.environ.get("APP_SERVICE_URL", "http://agent-backend:8000")

# =============================================================================
# Logging Settings
# =============================================================================

# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = "INFO"

# Log file path (None = stdout only)
LOG_FILE = "aiops.log"
