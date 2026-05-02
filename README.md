# Agent Marketplace - DevOps CI/CD Pipeline

Welcome to the **Agent Marketplace**, an intelligent system powered by an autonomous, multi-agent LLM backend and a React-based frontend. This repository contains the complete infrastructure code required to deploy the application on a Kubernetes cluster with a fully automated CI/CD pipeline and an AIOps self-healing engine.

## Architecture Overview

The system is deployed using modern DevOps practices:

1. **Infrastructure as Code (IaC)**: Terraform provisions a Minikube Kubernetes cluster.
2. **Configuration Management**: Ansible installs and configures Docker, Kubernetes, and Jenkins.
3. **CI/CD Automation**: Jenkins automatically builds the React frontend and FastAPI backend Docker images and deploys them to Kubernetes.
4. **Self-Healing (AIOps)**: A custom Python-based AIOps engine monitors application health and automatically scales pods, restarts services, or rolls back deployments when anomalies are detected.
5. **Observability**: Prometheus and Grafana provide real-time metrics and visualizations.

---

## Prerequisites

Before starting, ensure you have the following installed on your machine (or your EC2 instance):

- **Docker**
- **Terraform**
- **Ansible**
- **Minikube** & **kubectl**
- **Python 3.10+**

> **Note on Hardware Requirements:** To run the full stack (Minikube, Jenkins, and the application), you need at least **8GB of RAM** and **20GB of free disk space**. Our Jenkins pipeline includes aggressive Docker pruning to ensure you don't run out of disk space during continuous deployments.

---

## Quick Start Guide

### 1. Provision Infrastructure
Start by spinning up the Minikube cluster using Terraform:

```bash
cd terraform
terraform init
terraform apply -auto-approve
```

### 2. Configure the Environment
Use Ansible to install required dependencies (Docker, Jenkins, etc.) on your server:

```bash
cd ../ansible
# Update inventory.ini with your server IP and SSH key path first
ansible-playbook -i inventory.ini playbook.yml
```

### 3. Deploy the Application via Jenkins
1. Open Jenkins in your browser: `http://<your-server-ip>:8080`.
2. Configure your Docker Hub credentials (`docker-registry-creds`) and Kubernetes configuration (`kubeconfig-creds`).
3. Create a Pipeline Job pointing to this repository and branch.
4. Click **Build Now**.

Jenkins will:
- Check out the latest code.
- Build the `agent-backend` and `agent-frontend` Docker images.
- Push the images to your Docker Hub.
- Apply the Kubernetes manifests located in the `kubernetes/` folder.
- Clean up dangling Docker images to preserve disk space.

### 4. Monitor & Self-Heal (AIOps)
Once the application is running, start the AIOps engine:

```bash
cd ../aiops
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Start the continuous monitoring daemon
python aiops_engine.py
```

The AIOps engine will monitor the `/health` endpoint and automatically scale up pods or restart them if it detects high load or failure.

---

## Directory Structure

```text
.
├── AgentMarketplace/         # Core application code
│   ├── backend/              # FastAPI Python backend (LLM Agents)
│   └── frontend/             # React & NGINX frontend
├── aiops/                    # Self-healing Python engine
├── ansible/                  # Server configuration playbooks
├── jenkins/                  # CI/CD Jenkinsfile configuration
├── kubernetes/               # Kubernetes Deployment and Service manifests
├── monitoring/               # Prometheus & Grafana K8s manifests
└── terraform/                # Infrastructure provisioning scripts
```
