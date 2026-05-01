# =============================================================================
# Terraform Variables
# =============================================================================
# Configurable parameters for the Minikube Kubernetes cluster.
# Override defaults via terraform.tfvars or -var flags.
# =============================================================================

variable "cluster_name" {
  description = "Name of the Minikube cluster profile"
  type        = string
  default     = "devops-cluster"
}

variable "kubernetes_version" {
  description = "Kubernetes version to deploy (leave empty for Minikube default)"
  type        = string
  default     = "stable"
}

variable "driver" {
  description = "Minikube driver to use (docker, virtualbox, hyperkit, etc.)"
  type        = string
  default     = "docker"
}

variable "cpus" {
  description = "Number of CPUs to allocate to the Minikube VM"
  type        = number
  default     = 2
}

variable "memory" {
  description = "Amount of memory (in MB) to allocate to the Minikube VM"
  type        = number
  default     = 4096
}

variable "disk_size" {
  description = "Disk size to allocate to the Minikube VM (e.g., '20g')"
  type        = string
  default     = "20g"
}

variable "namespace" {
  description = "Kubernetes namespace for the DevOps project workloads"
  type        = string
  default     = "devops-project"
}

variable "monitoring_namespace" {
  description = "Kubernetes namespace for monitoring stack (Prometheus + Grafana)"
  type        = string
  default     = "monitoring"
}

variable "addons" {
  description = "List of Minikube addons to enable"
  type        = list(string)
  default     = ["metrics-server", "ingress", "dashboard"]
}
