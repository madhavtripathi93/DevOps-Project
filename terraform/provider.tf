# =============================================================================
# Provider Configuration
# =============================================================================
# This file configures the Terraform providers required for provisioning
# a local Minikube-based Kubernetes cluster.
# =============================================================================

terraform {
  required_version = ">= 1.0.0"

  required_providers {
    # Null provider — used for local-exec provisioners to run shell commands
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }

    # Kubernetes provider — used to create namespaces and verify cluster state
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }
}

# -----------------------------------------------------------------------------
# Kubernetes Provider Configuration
# -----------------------------------------------------------------------------
# Connects to the Minikube cluster using the default kubeconfig location.
# This provider is used AFTER Minikube has been started by the null_resource.
# -----------------------------------------------------------------------------
provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = "minikube"
}
