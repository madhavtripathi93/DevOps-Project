"""
=============================================================================
AIOps — Failure Simulation Script
=============================================================================
Demonstrates AIOps self-healing by triggering various failure scenarios
and monitoring the automated response.

Usage:
    python simulate_failure.py cpu       # Trigger CPU spike
    python simulate_failure.py memory    # Trigger memory spike
    python simulate_failure.py crash     # Simulate pod crash
    python simulate_failure.py error     # Enable error mode
    python simulate_failure.py all       # Run all scenarios sequentially
    python simulate_failure.py stop      # Stop all simulations
=============================================================================
"""

import sys
import time
import logging
import requests
import subprocess

import config

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("simulate")

APP_URL = config.APP_SERVICE_URL


def simulate_cpu_spike(duration=60):
    """Trigger CPU spike via the application's simulation endpoint."""
    logger.info("=" * 50)
    logger.info("SCENARIO: CPU Spike Simulation")
    logger.info(f"Duration: {duration}s")
    logger.info("Expected AIOps Response: Scale up deployment")
    logger.info("=" * 50)

    try:
        r = requests.get(f"{APP_URL}/api/simulate/cpu?duration={duration}", timeout=10)
        logger.info(f"Response: {r.status_code} — {r.json().get('message', '')}")
        logger.info("Waiting for AIOps to detect and respond...")
        logger.info("Monitor AIOps logs: tail -f aiops.log")
    except requests.RequestException as e:
        logger.error(f"Failed to trigger CPU spike: {e}")
        logger.info("Alternative: Run CPU-intensive commands inside the pod")


def simulate_memory_spike(size_mb=200, duration=60):
    """Trigger memory spike via the application's simulation endpoint."""
    logger.info("=" * 50)
    logger.info("SCENARIO: Memory Spike Simulation")
    logger.info(f"Allocating {size_mb}MB for {duration}s")
    logger.info("Expected AIOps Response: Restart affected pods")
    logger.info("=" * 50)

    try:
        r = requests.get(
            f"{APP_URL}/api/simulate/memory?size_mb={size_mb}&duration={duration}",
            timeout=10
        )
        logger.info(f"Response: {r.status_code} — {r.json().get('message', '')}")
    except requests.RequestException as e:
        logger.error(f"Failed to trigger memory spike: {e}")


def simulate_pod_crash():
    """Simulate pod crash by deleting a pod via kubectl."""
    logger.info("=" * 50)
    logger.info("SCENARIO: Pod Crash Simulation")
    logger.info("Expected AIOps Response: Detect crash loop → Rollback")
    logger.info("=" * 50)

    try:
        # Get a pod name
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", config.K8S_NAMESPACE,
             "-l", f"app={config.K8S_DEPLOYMENT}",
             "-o", "jsonpath={.items[0].metadata.name}"],
            capture_output=True, text=True, timeout=10
        )

        if result.returncode == 0 and result.stdout:
            pod_name = result.stdout.strip()
            logger.info(f"Deleting pod: {pod_name}")

            subprocess.run(
                ["kubectl", "delete", "pod", pod_name,
                 "-n", config.K8S_NAMESPACE, "--grace-period=0", "--force"],
                timeout=15
            )
            logger.info(f"Pod {pod_name} deleted. K8s will recreate it.")
        else:
            logger.warning("No pods found. Is the deployment running?")

    except Exception as e:
        logger.error(f"Failed to simulate pod crash: {e}")


def simulate_error_mode():
    """Enable error simulation mode in the application."""
    logger.info("=" * 50)
    logger.info("SCENARIO: Error Rate Spike")
    logger.info("Expected AIOps Response: Detect health check failures")
    logger.info("=" * 50)

    try:
        r = requests.get(f"{APP_URL}/api/simulate/error?enable=true", timeout=10)
        logger.info(f"Response: {r.status_code} — {r.json().get('message', '')}")
    except requests.RequestException as e:
        logger.error(f"Failed to enable error mode: {e}")


def stop_all():
    """Stop all simulations."""
    logger.info("Stopping all simulations...")
    try:
        r = requests.get(f"{APP_URL}/api/simulate/stop", timeout=10)
        logger.info(f"Response: {r.status_code} — {r.json().get('message', '')}")
    except requests.RequestException as e:
        logger.error(f"Failed to stop simulations: {e}")


def run_all_scenarios():
    """Run all failure scenarios sequentially."""
    scenarios = [
        ("CPU Spike", lambda: simulate_cpu_spike(30)),
        ("Memory Spike", lambda: simulate_memory_spike(100, 30)),
        ("Error Mode", simulate_error_mode),
        ("Pod Crash", simulate_pod_crash),
    ]

    for name, scenario_fn in scenarios:
        logger.info(f"\n{'#' * 50}")
        logger.info(f"# Running: {name}")
        logger.info(f"{'#' * 50}\n")
        scenario_fn()
        logger.info(f"Waiting 45s for AIOps response before next scenario...")
        time.sleep(45)

    logger.info("\nAll scenarios completed. Check AIOps logs for responses.")
    stop_all()


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    scenario = sys.argv[1].lower()

    scenarios = {
        "cpu": simulate_cpu_spike,
        "memory": simulate_memory_spike,
        "crash": simulate_pod_crash,
        "error": simulate_error_mode,
        "all": run_all_scenarios,
        "stop": stop_all,
    }

    if scenario in scenarios:
        scenarios[scenario]()
    else:
        print(f"Unknown scenario: {scenario}")
        print(f"Available: {', '.join(scenarios.keys())}")
        sys.exit(1)


if __name__ == "__main__":
    main()
