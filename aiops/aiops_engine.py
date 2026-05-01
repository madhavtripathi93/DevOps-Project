"""
=============================================================================
AIOps — Main Engine (Orchestrator)
=============================================================================
The main AIOps loop that coordinates:
  1. Collect metrics → 2. Detect anomalies → 3. Decide action → 4. Remediate

Usage:
    python aiops_engine.py              # Normal mode
    python aiops_engine.py --dry-run    # Dry-run mode (no real actions)
    python aiops_engine.py --simulate   # Force simulation mode
=============================================================================
"""

import sys
import time
import json
import signal
import logging
import argparse
from datetime import datetime, timezone

import config
from metrics_collector import MetricsCollector
from anomaly_detector import AnomalyDetector
from decision_engine import DecisionEngine
from remediation import RemediationEngine

# =============================================================================
# Logging Setup
# =============================================================================

def setup_logging():
    """Configure structured logging."""
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)-20s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console = logging.StreamHandler()
    console.setFormatter(formatter)

    # File handler (if configured)
    handlers = [console]
    if config.LOG_FILE:
        file_handler = logging.FileHandler(config.LOG_FILE)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL, logging.INFO),
        handlers=handlers,
    )


# =============================================================================
# Main AIOps Engine
# =============================================================================

class AIOpsEngine:
    """Main orchestrator for the AIOps self-healing system."""

    def __init__(self, dry_run=False, simulate=False):
        self.running = True
        self.cycle_count = 0

        # Override config if flags are set
        if dry_run:
            config.DRY_RUN = True
        if simulate:
            # Force simulation mode in the collector
            pass

        # Initialize components
        self.collector = MetricsCollector()
        self.detector = AnomalyDetector()
        self.decision = DecisionEngine()
        self.remediation = RemediationEngine()

        if simulate:
            self.collector.simulation_mode = True
            self.remediation.simulation_mode = True

        self.logger = logging.getLogger("aiops.engine")

    def run(self):
        """Main monitoring loop."""
        self.logger.info("=" * 60)
        self.logger.info("  AIOps Self-Healing Engine Started")
        self.logger.info(f"  Namespace:  {config.K8S_NAMESPACE}")
        self.logger.info(f"  Deployment: {config.K8S_DEPLOYMENT}")
        self.logger.info(f"  Interval:   {config.MONITORING_INTERVAL}s")
        self.logger.info(f"  Dry Run:    {config.DRY_RUN}")
        self.logger.info(f"  Simulation: {self.collector.simulation_mode}")
        self.logger.info("=" * 60)

        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

        while self.running:
            try:
                self._run_cycle()
                time.sleep(config.MONITORING_INTERVAL)
            except Exception as e:
                self.logger.error(f"Cycle error: {e}", exc_info=True)
                time.sleep(config.MONITORING_INTERVAL)

        self.logger.info("AIOps Engine stopped.")

    def _run_cycle(self):
        """Execute one monitoring cycle."""
        self.cycle_count += 1
        self.logger.info(f"--- Cycle #{self.cycle_count} ---")

        # Step 1: Collect metrics
        self.logger.debug("Collecting metrics...")
        metrics = self.collector.collect()
        agg = metrics.get("aggregated", {})
        health = metrics.get("app_health", {})
        self.logger.info(
            f"Metrics: CPU={agg.get('avg_cpu_percent', 0):.1f}% | "
            f"Memory={agg.get('avg_memory_percent', 0):.1f}% | "
            f"Response={health.get('response_time_ms', 0):.0f}ms | "
            f"Pods={agg.get('running_pods', 0)}/{agg.get('total_pods', 0)} | "
            f"Restarts={agg.get('total_restarts', 0)}"
        )

        # Step 2: Detect anomalies
        anomaly_report = self.detector.analyze(metrics)
        if anomaly_report["is_anomaly"]:
            self.logger.warning(
                f"ANOMALY [{anomaly_report['method']}]: "
                f"{len(anomaly_report['anomalies'])} issue(s) detected"
            )
        else:
            self.logger.info("Status: Normal")

        # Step 3: Decide on actions
        actions = self.decision.decide(anomaly_report, metrics)

        # Step 4: Execute remediation
        if actions:
            self.logger.warning(f"Executing {len(actions)} remediation action(s)...")
            results = self.remediation.execute(actions)
            for r in results:
                self.logger.info(f"  Result: {r['action']} → {r['status']}")
        else:
            self.logger.debug("No actions needed.")

    def _shutdown(self, signum, frame):
        """Handle graceful shutdown on SIGINT/SIGTERM."""
        self.logger.info(f"Received signal {signum}. Shutting down...")
        self.running = False


# =============================================================================
# Entry Point
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="AIOps Self-Healing Engine for Kubernetes"
    )
    parser.add_argument("--dry-run", action="store_true",
                       help="Log actions without executing them")
    parser.add_argument("--simulate", action="store_true",
                       help="Use simulated metrics (no real cluster needed)")
    args = parser.parse_args()

    setup_logging()
    engine = AIOpsEngine(dry_run=args.dry_run, simulate=args.simulate)
    engine.run()


if __name__ == "__main__":
    main()
