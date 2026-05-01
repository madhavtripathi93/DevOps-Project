import jenkins.model.*
import hudson.security.*
import com.cloudbees.plugins.credentials.*
import com.cloudbees.plugins.credentials.domains.*
import com.cloudbees.plugins.credentials.impl.*
import org.jenkinsci.plugins.plaincredentials.impl.*
import hudson.util.Secret
import hudson.plugins.git.*
import org.jenkinsci.plugins.workflow.job.WorkflowJob
import org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition

def instance = Jenkins.getInstance()

// 1. Create Admin User
println "Creating user 'madhav'..."
def hudsonRealm = new HudsonPrivateSecurityRealm(false)
hudsonRealm.createAccount("madhav", "madhjen12")
instance.setSecurityRealm(hudsonRealm)

def strategy = new FullControlOnceLoggedInAuthorizationStrategy()
strategy.setAllowAnonymousRead(false)
instance.setAuthorizationStrategy(strategy)

instance.save()
println "User created and security enabled."

// 2. Install Plugins
println "Installing plugins..."
def pm = instance.getPluginManager()
def uc = instance.getUpdateCenter()
uc.updateAllSites()

def plugins = ['workflow-aggregator', 'docker-workflow', 'git', 'kubernetes-cli', 'pipeline-stage-view', 'plain-credentials', 'credentials-binding']
def installed = false
plugins.each {
  if (!pm.getPlugin(it)) {
    println "Installing plugin ${it}..."
    def plugin = uc.getPlugin(it)
    if (plugin) {
      plugin.deploy()
      installed = true
    }
  }
}

// 3. Add Credentials
println "Adding Credentials..."
def domain = Domain.global()
def store = instance.getExtensionList('com.cloudbees.plugins.credentials.SystemCredentialsProvider')[0].getStore()

// Docker Hub Username (Secret Text)
def dockerUserCred = new StringCredentialsImpl(
  CredentialsScope.GLOBAL,
  "dockerhub-user",
  "Docker Hub Username",
  Secret.fromString("madhavtripathi93")
)
store.addCredentials(domain, dockerUserCred)

// Docker Hub Password (Username with password)
def dockerPassCred = new UsernamePasswordCredentialsImpl(
  CredentialsScope.GLOBAL,
  "docker-registry-creds",
  "Docker Hub Registry Credentials",
  "madhavtripathi93",
  "Madh@dock12"
)
store.addCredentials(domain, dockerPassCred)

// Kubeconfig is added manually or via file later in bash since Groovy runs inside Docker
println "Credentials added."

// 4. Create Pipeline Job
println "Creating Pipeline Job..."
def jobName = "AgentMarketplace-Pipeline"
if (instance.getItem(jobName) == null) {
  def job = new WorkflowJob(instance, jobName)
  def scm = new GitSCM("https://github.com/madhavtripathi93/Agent_MarketPlace.git")
  scm.branches = [new BranchSpec("*/main")]
  def defScm = new CpsScmFlowDefinition(scm, "jenkins/Jenkinsfile")
  defScm.setLightweight(true)
  job.setDefinition(defScm)
  job.save()
  println "Job ${jobName} created!"
} else {
  println "Job ${jobName} already exists."
}

if (installed) {
  println "Plugins installed. A restart may be required."
}

println "Jenkins setup complete."
