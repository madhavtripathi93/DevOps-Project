# =============================================================================
# Main Terraform Configuration
# =============================================================================
# Provisions a local Minikube Kubernetes cluster with required addons,
# and creates dedicated namespaces for the application and monitoring.
# =============================================================================

# -----------------------------------------------------------------------------
# 1. Start Minikube Cluster
# -----------------------------------------------------------------------------
# Uses a null_resource with local-exec to start Minikube.
# The cluster is only created if it doesn't already exist.
# -----------------------------------------------------------------------------
resource "null_resource" "minikube_cluster" {
  # Re-run if any cluster configuration changes
  triggers = {
    cluster_name       = var.cluster_name
    kubernetes_version = var.kubernetes_version
    driver             = var.driver
    cpus               = var.cpus
    memory             = var.memory
  }

  provisioner "local-exec" {
    command = <<-EOT
      echo "============================================"
      echo "  Starting Minikube Cluster: ${var.cluster_name}"
      echo "============================================"

      # Check if Minikube is installed
      if ! command -v minikube &> /dev/null; then
        echo "ERROR: minikube is not installed. Please install it first."
        echo "  macOS:   brew install minikube"
        echo "  Linux:   curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64"
        exit 1
      fi

      # Check if the cluster already exists and is running
      STATUS=$(minikube status -p ${var.cluster_name} --format='{{.Host}}' 2>/dev/null || echo "NotFound")

      if [ "$STATUS" = "Running" ]; then
        echo "Minikube cluster '${var.cluster_name}' is already running. Skipping start."
      else
        echo "Starting Minikube cluster..."
        minikube start \
          --profile=${var.cluster_name} \
          --driver=${var.driver} \
          --cpus=${var.cpus} \
          --memory=${var.memory} \
          --disk-size=${var.disk_size} \
          --kubernetes-version=${var.kubernetes_version} \
          --addons=metrics-server \
          --addons=ingress \
          --addons=dashboard \
          --wait=all

        echo "Minikube cluster started successfully!"
      fi

      # Verify cluster is accessible
      echo ""
      echo "Cluster Info:"
      kubectl cluster-info --context ${var.cluster_name}
    EOT

    interpreter = ["/bin/bash", "-c"]
  }

  # Cleanup: stop and delete the cluster on terraform destroy
  provisioner "local-exec" {
    when    = destroy
    command = <<-EOT
      echo "Stopping and deleting Minikube cluster..."
      minikube stop -p devops-cluster 2>/dev/null || true
      minikube delete -p devops-cluster 2>/dev/null || true
      echo "Cluster deleted."
    EOT

    interpreter = ["/bin/bash", "-c"]
  }
}

# -----------------------------------------------------------------------------
# 2. Enable Additional Minikube Addons
# -----------------------------------------------------------------------------
# Enables each addon specified in the addons variable.
# Depends on the cluster being started first.
# -----------------------------------------------------------------------------
resource "null_resource" "minikube_addons" {
  depends_on = [null_resource.minikube_cluster]

  # Re-run if addons list changes
  triggers = {
    addons = join(",", var.addons)
  }

  provisioner "local-exec" {
    command = <<-EOT
      echo "Enabling Minikube addons..."
      %{for addon in var.addons~}
      echo "  Enabling addon: ${addon}"
      minikube addons enable ${addon} -p ${var.cluster_name} 2>/dev/null || true
      %{endfor~}
      echo "All addons enabled."
    EOT

    interpreter = ["/bin/bash", "-c"]
  }
}

# -----------------------------------------------------------------------------
# 3. Create Application Namespace
# -----------------------------------------------------------------------------
# Dedicated namespace for the DevOps project workloads.
# Using the Kubernetes provider ensures proper state management.
# -----------------------------------------------------------------------------
resource "kubernetes_namespace" "app" {
  depends_on = [null_resource.minikube_cluster]

  metadata {
    name = var.namespace

    labels = {
      project     = "ai-devops-pipeline"
      environment = "development"
      managed-by  = "terraform"
    }
  }
}

# -----------------------------------------------------------------------------
# 4. Create Monitoring Namespace
# -----------------------------------------------------------------------------
# Dedicated namespace for Prometheus and Grafana.
# -----------------------------------------------------------------------------
resource "kubernetes_namespace" "monitoring" {
  depends_on = [null_resource.minikube_cluster]

  metadata {
    name = var.monitoring_namespace

    labels = {
      project     = "ai-devops-pipeline"
      component   = "monitoring"
      managed-by  = "terraform"
    }
  }
}
