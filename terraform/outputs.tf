# =============================================================================
# Terraform Outputs
# =============================================================================
# Outputs the connection details needed to interact with the provisioned
# Minikube Kubernetes cluster.
# =============================================================================

output "cluster_name" {
  description = "Name of the Minikube cluster profile"
  value       = var.cluster_name
}

output "kubeconfig_path" {
  description = "Path to the kubeconfig file for cluster access"
  value       = "~/.kube/config"
}

output "kube_context" {
  description = "Kubernetes context name for kubectl commands"
  value       = var.cluster_name
}

output "app_namespace" {
  description = "Kubernetes namespace where the application is deployed"
  value       = kubernetes_namespace.app.metadata[0].name
}

output "monitoring_namespace" {
  description = "Kubernetes namespace where monitoring stack is deployed"
  value       = kubernetes_namespace.monitoring.metadata[0].name
}

output "cluster_access_command" {
  description = "Command to set kubectl context to this cluster"
  value       = "kubectl config use-context ${var.cluster_name}"
}

output "dashboard_command" {
  description = "Command to open the Kubernetes dashboard"
  value       = "minikube dashboard -p ${var.cluster_name}"
}

output "minikube_ip_command" {
  description = "Command to get the Minikube node IP address"
  value       = "minikube ip -p ${var.cluster_name}"
}
