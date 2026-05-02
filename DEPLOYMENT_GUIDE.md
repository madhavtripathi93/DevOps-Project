# Zero-to-Hero: Complete AIOps DevOps Pipeline Guide

This guide outlines exactly how to deploy your **Agent Marketplace DevOps Pipeline** from scratch in one go. It is specifically tailored for your AWS EC2 limitations (**8GB RAM, 25GB Storage**) and clearly separates what you should run on your Local PC versus the AWS Server.

---

## 💻 Phase 1: Local PC Setup

First, you need to prepare the code and let Ansible configure your AWS server remotely.

### Step 1: Push to GitHub
From your local PC terminal, push this newly cleaned project to your GitHub repository:
```bash
git init
git add .
git commit -m "Initial commit - Cleaned AIOps architecture"
git branch -M main
git remote add origin https://github.com/your-username/your-repo-name.git
git push -u origin main
```

### Step 2: Configure Ansible Inventory
Open `ansible/inventory.ini` on your Local PC and update it with your AWS EC2 instance's public IP and SSH key path:
```ini
[ec2_server]
your-aws-ec2-ip ansible_user=ubuntu ansible_ssh_private_key_file=~/.ssh/your-aws-key.pem
```

### Step 3: Run Ansible Provisioning
From your Local PC, run Ansible to install Docker, Jenkins, `kubectl`, and `minikube` on your AWS server.
```bash
cd ansible
ansible-playbook -i inventory.ini playbook.yml
```
*Note: This might take 5-10 minutes. Once it completes, your AWS server will have all the necessary software installed.*

---

## ☁️ Phase 2: AWS EC2 Operations

Now, you will SSH into your AWS server to initialize the Kubernetes cluster.

### Step 4: SSH into your AWS EC2 Instance
```bash
ssh -i ~/.ssh/your-aws-key.pem ubuntu@your-aws-ec2-ip
```

### Step 5: Start the Kubernetes Cluster
Since you only have **8GB RAM**, Minikube is the perfect orchestrator. We will start it using the Docker driver. Run this on your AWS server:
```bash
minikube start --profile=devops-cluster --driver=docker --cpus=2 --memory=3000 --addons=metrics-server,ingress
```
> [!TIP]
> **Resource Optimization:** We explicitly limit Minikube to 3GB of RAM (`--memory=3000`). This ensures Jenkins and Docker have enough remaining memory (out of your 8GB total) to build images without crashing the server!

### Step 6: Prepare the Kubeconfig for Jenkins
Jenkins will need access to your Kubernetes cluster to deploy the application. On your AWS server, copy the config to a safe location so we can upload it to Jenkins later:
```bash
sudo cp ~/.kube/config /tmp/kubeconfig
sudo chmod 777 /tmp/kubeconfig
# Download this file to your Local PC, or cat it and copy the contents
```

---

## ⚙️ Phase 3: Jenkins Configuration (Web Browser)

Open your web browser on your Local PC and navigate to `http://<your-aws-ec2-ip>:8080`.

### Step 7: Initial Jenkins Setup
1. Retrieve the initial admin password from your AWS server:
   ```bash
   sudo cat /home/ubuntu/jenkins_home/secrets/initialAdminPassword
   ```
2. Paste it into Jenkins, select **"Install suggested plugins"**, and create your admin user.

### Step 8: Add Credentials
Jenkins needs two sets of credentials to run the pipeline. Navigate to **Manage Jenkins -> Credentials -> System -> Global credentials**:

1. **Docker Hub Credentials**:
   - Kind: **Username with password**
   - Username: `madhavtripathi93` (Your Docker Hub username)
   - Password: `<your-docker-hub-password>`
   - ID: `docker-registry-creds`
   - Description: Docker Hub login

2. **Kubernetes Credentials**:
   - Kind: **Secret file**
   - File: Upload the `/tmp/kubeconfig` file you generated in Step 6.
   - ID: `kubeconfig-creds`
   - Description: Kubernetes config

### Step 9: Create and Run the Pipeline
1. Go to Jenkins Dashboard -> **New Item**.
2. Enter a name (e.g., `AgentMarketplace`), select **Pipeline**, and click OK.
3. Scroll down to the **Pipeline** section.
4. Definition: **Pipeline script from SCM**.
5. SCM: **Git**.
6. Repository URL: `https://github.com/your-username/your-repo-name.git`.
7. Branch Specifier: `*/main`.
8. Script Path: `jenkins/Jenkinsfile`.
9. Click **Save** and then click **Build Now**.

---

## 🚀 Phase 4: Automated Execution & Monitoring

Once you click **Build Now**, the Jenkins pipeline will execute all the steps automatically:

1. **Checkout**: Pulls your code from GitHub.
2. **Build**: Builds the Backend, Frontend, and AIOps Docker images.
3. **Push**: Pushes all three images to your Docker Hub (`madhavtripathi93`).
4. **Deploy**: Deploys the MySQL database, Backend API, React Frontend, and AIOps engine into Kubernetes.
5. **Cleanup**: Executes aggressive Docker pruning (`docker system prune -af`).
> [!IMPORTANT]
> **Storage Optimization:** This final cleanup step is crucial for your **25GB storage limit**. By wiping dangling images and stopped containers immediately after deployment, your server will never run out of disk space!

### Verification
Once the pipeline shows a green **Success**, access your application:
- **Frontend UI**: `http://<your-aws-ec2-ip>:30081`
- **Backend API Docs**: `http://<your-aws-ec2-ip>:30080/docs`
- **Prometheus Metrics**: `http://<your-aws-ec2-ip>:30090`

Your **AIOps Engine** is now running invisibly inside the cluster. If your backend pods ever crash or experience high CPU load, the AIOps pod will detect it via Prometheus metrics and automatically restart them!
