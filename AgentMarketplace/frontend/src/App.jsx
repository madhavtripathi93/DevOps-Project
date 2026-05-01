import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Layout, Search, Zap, Plus, Play, History, CheckCircle2, XCircle, Info, Key, ChevronRight, Cpu, User, Globe, LogOut, ShoppingBag, Settings } from 'lucide-react';
import { cn } from './lib/utils';
import { Routes, Route, useNavigate, useParams } from 'react-router-dom';
import AgentCard from './components/AgentCard';
import ToolCard from './components/ToolCard';
import WorkflowBuilder from './components/WorkflowBuilder';
import ExecutionPanel from './components/ExecutionPanel';
import PublicAgent from './pages/PublicAgent';
import Toast from './components/Toast';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

function App() {
  const [marketplaceAgents, setMarketplaceAgents] = useState([]);
  const [myAgents, setMyAgents] = useState([]);
  const [marketplaceWorkflows, setMarketplaceWorkflows] = useState([]);
  const [myWorkflows, setMyWorkflows] = useState([]);
  const [marketplaceTools, setMarketplaceTools] = useState([]);
  const [myTools, setMyTools] = useState([]);
  
  const [apiKey, setApiKey] = useState(sessionStorage.getItem('ag_api_key') || '');
  const [activeTab, setActiveTab] = useState('marketplace'); // marketplace, library, workflow, logs
  const [workflow, setWorkflow] = useState([]);
  const [executionResult, setExecutionResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [isRegistering, setIsRegistering] = useState(false);
  const [authMode, setAuthMode] = useState('login'); // login, register, key
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [user, setUser] = useState(JSON.parse(sessionStorage.getItem('ag_user') || 'null'));
  const [autoTask, setAutoTask] = useState('');
  const [toast, setToast] = useState(null);
  const [activeMarketCategory, setActiveMarketCategory] = useState('agents'); // agents, tools, workflows

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
  };

  useEffect(() => {
    if (apiKey) {
      fetchAllAssets();
    }
  }, [apiKey]);

  const fetchAllAssets = async () => {
    try {
      const config = { headers: { 'x-api-key': apiKey } };
      const [mAgents, myA, mWorkflows, myW, mTools, myT] = await Promise.all([
        axios.get(`${API_BASE}/agents/`, config),
        axios.get(`${API_BASE}/agents/my`, config),
        axios.get(`${API_BASE}/workflow/list`, config),
        axios.get(`${API_BASE}/workflow/my`, config),
        axios.get(`${API_BASE}/tools/`, config),
        axios.get(`${API_BASE}/tools/my`, config)
      ]);
      setMarketplaceAgents(mAgents.data);
      setMyAgents(myA.data);
      setMarketplaceWorkflows(mWorkflows.data);
      setMyWorkflows(myW.data);
      setMarketplaceTools(mTools.data);
      setMyTools(myT.data);
    } catch (err) {
      console.error('Failed to fetch assets', err);
    }
  };

  const acquireAgent = async (agentId) => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/agents/acquire/${agentId}`, {}, {
        headers: { 'x-api-key': apiKey }
      });
      fetchAllAssets();
      showToast('Agent added to your library!', 'success');
    } catch (err) {
      showToast('Failed to acquire agent. Please check your connection.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const acquireWorkflow = async (workflowId) => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/workflow/acquire/${workflowId}`, {}, {
        headers: { 'x-api-key': apiKey }
      });
      fetchAllAssets();
      showToast('Workflow template added to library!', 'success');
    } catch (err) {
      showToast('Failed to acquire workflow template.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const acquireTool = async (toolId) => {
    setLoading(true);
    try {
      await axios.post(`${API_BASE}/tools/acquire/${toolId}`, {}, {
        headers: { 'x-api-key': apiKey }
      });
      fetchAllAssets();
      showToast('Function tool integrated into your library!', 'success');
    } catch (err) {
      showToast('Failed to acquire tool.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const saveWorkflow = async (name, isPublic = false) => {
    if (!name || workflow.length === 0) {
      showToast('Name and steps are required', 'error');
      return null;
    }
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/workflow/save`, 
        { name, steps: workflow, is_public: isPublic },
        { headers: { 'x-api-key': apiKey } }
      );
      fetchAllAssets();
      showToast('Workflow saved to your library!', 'success');
      return res.data;
    } catch (err) {
      showToast('Failed to save workflow. Name might be taken.', 'error');
      return null;
    } finally {
      setLoading(false);
    }
  };

  const deployWorkflow = async (workflowId) => {
     try {
       const res = await axios.post(`${API_BASE}/deploy/workflow/${workflowId}`, {}, {
         headers: { 'x-api-key': apiKey }
       });
       const shareUrl = `${window.location.origin}/use/${res.data.slug}?type=workflow`;
       navigator.clipboard.writeText(shareUrl);
       showToast(`Workflow deployed! Link copied to clipboard.`, 'success');
     } catch (err) {
       showToast('Failed to deploy workflow.', 'error');
     }
  };

  const register = async () => {
    if (!username || username.length < 3 || !password || password.length < 6) {
      showToast('Username (min 3) and Password (min 6) are required', 'error');
      return;
    }
    setIsRegistering(true);
    try {
      const res = await axios.post(`${API_BASE}/auth/register`, { username, password });
      setApiKey(res.data.api_key);
      setUser({ username: res.data.username });
      sessionStorage.setItem('ag_api_key', res.data.api_key);
      sessionStorage.setItem('ag_user', JSON.stringify({ username: res.data.username }));
      showToast('Welcome potential orchestrator! Registration successful.', 'success');
    } catch (err) {
      showToast(err.response?.data?.detail || 'Registration failed.', 'error');
    } finally {
      setIsRegistering(false);
    }
  };

  const login = async () => {
    if (!username || !password) {
      showToast('Username and Password are required', 'error');
      return;
    }
    setIsRegistering(true);
    try {
      const res = await axios.post(`${API_BASE}/auth/login`, { username, password });
      setApiKey(res.data.api_key);
      setUser({ username: res.data.username });
      sessionStorage.setItem('ag_api_key', res.data.api_key);
      sessionStorage.setItem('ag_user', JSON.stringify({ username: res.data.username }));
      showToast('Authorized. Welcome back.', 'success');
    } catch (err) {
      showToast(err.response?.data?.detail || 'Login failed.', 'error');
    } finally {
      setIsRegistering(false);
    }
  };

  const suggestWorkflow = async (input) => {
    if (!input) return;
    setAutoTask(input);
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/run/suggest`, 
        { input },
        { headers: { 'x-api-key': apiKey } }
      );
      if (res.data.workflow) {
        setWorkflow(res.data.workflow);
        setActiveTab('workflow');
      }
    } catch (err) {
      alert('Failed to suggest workflow: ' + err.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const runSingleAgent = async (agentId, input) => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/run/`, 
        { 
          mode: agentId === 'router' ? 'auto' : 'manual', 
          agent_id: agentId === 'router' ? undefined : agentId, 
          input 
        },
        { headers: { 'x-api-key': apiKey } }
      );
      setExecutionResult(res.data);
      setActiveTab('logs');
    } catch (err) {
      setExecutionResult({ 
        agent: agentId,
        status: 'failed', 
        output: err.response?.data?.detail || err.message,
        input: input,
        steps: [{ agent: agentId, status: 'failed', output: err.response?.data?.detail || err.message, input: input }]
      });
      setActiveTab('logs');
    } finally {
      setLoading(false);
    }
  };

  const runWorkflow = async (input) => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/run/`, 
        { mode: 'manual', agent_ids: workflow, input },
        { headers: { 'x-api-key': apiKey } }
      );
      setExecutionResult(res.data);
      setActiveTab('logs');
    } catch (err) {
      setExecutionResult({ 
        status: 'failed', 
        output: err.response?.data?.detail || err.message,
        input: input,
        steps: [{ agent: 'Workflow', status: 'failed', output: err.response?.data?.detail || err.message, input: input }]
      });
      setActiveTab('logs');
    } finally {
      setLoading(false);
    }
  };

  const deployAgent = async (agentId) => {
     try {
       const res = await axios.post(`${API_BASE}/deploy/agent/${agentId === 'router' ? 'auto' : agentId}`, {}, {
         headers: { 'x-api-key': apiKey }
       });
       const shareUrl = `${window.location.origin}/use/${res.data.slug}`;
       navigator.clipboard.writeText(shareUrl);
       alert(`Public URL copied to clipboard: ${shareUrl}`);
     } catch (err) {
       alert('Failed to deploy agent: ' + (err.response?.data?.detail || err.message));
     }
  };

  const runSingleTool = async (tool, input) => {
    setLoading(true);
    try {
      let finalInput = {};
      try {
        // Try parsing as JSON first
        finalInput = JSON.parse(input);
      } catch (e) {
        // Smart Mapping: wrap simple string into the tool's required property
        const schema = tool.input_schema || {};
        const requiredProps = schema.required || [];
        const primaryProp = requiredProps[0] || Object.keys(schema.properties || {})[0];
        
        if (primaryProp) {
          finalInput = { [primaryProp]: input };
        } else {
          finalInput = { input: input };
        }
      }

      const res = await axios.post(`${API_BASE}/tools/execute/${tool.name}`, 
        finalInput,
        { headers: { 'x-api-key': apiKey } }
      );
      
      const resStatus = res.data.status || 'success';
      const outputStr = typeof res.data.result === 'string' 
        ? res.data.result 
        : JSON.stringify(res.data.result, null, 2);

      // Transform result for the Terminal view
      setExecutionResult({
        agent: `Function:${tool.name}`,
        status: resStatus,
        output: outputStr,
        steps: [{ 
          agent: `Function:${tool.name}`, 
          status: resStatus,
          output: outputStr,
          input: finalInput,
          metadata: { model: 'Local Function', duration: 0 }
        }]
      });
      setActiveTab('logs');
    } catch (err) {
      console.error('Tool execution failed', err);
      setExecutionResult({ 
        agent: 'System',
        status: 'failed', 
        output: err.response?.data?.detail || err.message,
        steps: [] 
      });
      setActiveTab('logs');
    } finally {
      setLoading(false);
    }
  };

  const Dashboard = () => (
    <div className="min-h-screen flex flex-col bg-background selection:bg-primary/20">
      <header className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-xl text-primary">
            <Zap className="fill-current" /> <span>AgentMarket</span>
          </div>
          <nav className="flex gap-1 p-1 bg-secondary rounded-xl">
            {[
              { id: 'marketplace', label: 'Discover', icon: Globe },
              { id: 'library', label: 'Library', icon: Layout },
              { id: 'workflow', label: 'Builder', icon: Plus },
              { id: 'logs', label: 'Terminal', icon: History }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-bold transition-all",
                  activeTab === tab.id ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
                )}
              >
                <tab.icon size={16} />
                {tab.label}
              </button>
            ))}
          </nav>

          <div className="flex items-center gap-4">
            <div className="hidden md:flex items-center gap-2 text-xs font-bold text-muted-foreground bg-secondary px-3 py-1.5 rounded-full border border-border">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              {user ? user.username : 'Guest'}
            </div>
            <button onClick={() => { sessionStorage.clear(); setApiKey(''); setUser(null); window.location.reload(); }} className="p-2 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-xl transition-all" title="Logout">
              <LogOut size={20} />
            </button>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl mx-auto w-full p-4 md:p-8">
        {activeTab === 'marketplace' && (
          <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex flex-col gap-6">
              <div className="flex flex-col gap-2">
                <h2 className="text-4xl font-extrabold tracking-tight">Marketplace</h2>
                <p className="text-muted-foreground text-lg">Acquire elite AI agents, function tools, and workflow templates.</p>
              </div>
              
              <div className="flex gap-2 p-1 bg-secondary w-fit rounded-xl">
                 {[
                   { id: 'agents', label: 'Agents', icon: Cpu },
                   { id: 'tools', label: 'Function Tools', icon: Settings },
                   { id: 'workflows', label: 'Workflows', icon: Zap }
                 ].map(cat => (
                   <button
                     key={cat.id}
                     onClick={() => setActiveMarketCategory(cat.id)}
                     className={cn(
                       "flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold transition-all",
                       activeMarketCategory === cat.id ? "bg-card text-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"
                     )}
                   >
                     <cat.icon size={14} /> {cat.label}
                   </button>
                 ))}
              </div>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-4 gap-12">
              <div className="lg:col-span-3 space-y-10">
                {activeMarketCategory === 'agents' && (
                  <section className="space-y-6">
                    <h3 className="text-xl font-bold flex items-center gap-2"><Cpu size={20} className="text-primary" /> Verified Agents</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {marketplaceAgents.filter(a => a.agent_id !== 'router').map(agent => (
                        <AgentCard 
                          key={agent.agent_id} 
                          agent={agent} 
                          isOwned={myAgents.some(m => m.agent_id === agent.agent_id)}
                          hideRun={true}
                          onAcquire={() => acquireAgent(agent.agent_id)}
                          onRun={(input) => runSingleAgent(agent.agent_id, input)}
                          onAddToWorkflow={() => {
                            setWorkflow([...workflow, agent.agent_id]);
                            setActiveTab('workflow');
                          }}
                          onShare={() => deployAgent(agent.agent_id)}
                          isLoading={loading}
                          apiKey={apiKey}
                        />
                      ))}
                    </div>
                  </section>
                )}

                {activeMarketCategory === 'tools' && (
                  <section className="space-y-6">
                    <h3 className="text-xl font-bold flex items-center gap-2"><Settings size={20} className="text-primary" /> Function Tools</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {marketplaceTools.map(tool => (
                        <ToolCard 
                          key={tool.id} 
                          tool={tool}
                          isOwned={myTools.some(m => m.id === tool.id)}
                          onAcquire={() => acquireTool(tool.id)}
                          onRun={(input) => runSingleTool(tool, input)}
                          isLoading={loading}
                          apiKey={apiKey}
                        />
                      ))}
                    </div>
                  </section>
                )}

                {activeMarketCategory === 'workflows' && (
                  <section className="space-y-6">
                    <h3 className="text-xl font-bold flex items-center gap-2"><Zap size={20} className="text-primary" /> Workflow Templates</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {marketplaceWorkflows.map(w => (
                        <div key={w.id} className="p-6 rounded-3xl border border-border bg-card hover:border-primary/40 transition-all group flex flex-col justify-between h-full">
                          <div className="space-y-4">
                            <div className="flex justify-between items-start">
                               <div className="font-extrabold text-xl group-hover:text-primary transition-colors">{w.name}</div>
                               {!myWorkflows.some(m => m.id === w.id) && <div className="text-[10px] font-bold bg-primary/10 text-primary px-2 py-1 rounded-full uppercase">Template</div>}
                            </div>
                            <div className="flex gap-2 flex-wrap pb-4">
                               {w.steps.map((s, i) => (
                                 <span key={i} className="px-2 py-1 bg-secondary text-[10px] font-bold rounded-lg border border-border">{s}</span>
                               ))}
                            </div>
                          </div>
                          {myWorkflows.some(m => m.id === w.id) ? (
                            <button onClick={() => { setWorkflow(w.steps); setActiveTab('workflow'); }} className="w-full py-3 bg-secondary text-foreground rounded-xl font-bold hover:bg-secondary/80 transition-all flex items-center justify-center gap-2">
                               <Play size={16} /> Open in Builder
                            </button>
                          ) : (
                            <button onClick={() => acquireWorkflow(w.id)} className="w-full py-3 bg-primary text-primary-foreground rounded-xl font-bold hover:opacity-90 transition-all flex items-center justify-center gap-2 shadow-lg shadow-primary/20">
                               <ShoppingBag size={16} /> Acquire Template
                            </button>
                          )}
                        </div>
                      ))}
                    </div>
                  </section>
                )}
              </div>

              <div className="space-y-8">
                 <div className="p-8 rounded-[2rem] border border-border bg-card/50 shadow-xl space-y-6 sticky top-24">
                    <div className="flex items-center justify-between">
                       <h3 className="text-lg font-bold flex items-center gap-2"><Layout size={18} className="text-primary" /> My Stats</h3>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                       <div className="p-4 rounded-2xl bg-secondary/50 border border-border text-center">
                          <div className="text-2xl font-black text-primary">{myAgents.length}</div>
                          <div className="text-[10px] uppercase font-bold text-muted-foreground">Agents</div>
                       </div>
                       <div className="p-4 rounded-2xl bg-secondary/50 border border-border text-center">
                          <div className="text-2xl font-black text-primary">{myWorkflows.length}</div>
                          <div className="text-[10px] uppercase font-bold text-muted-foreground">Workflows</div>
                       </div>
                    </div>
                    <div className="pt-4 border-t border-border">
                       <p className="text-[11px] text-muted-foreground leading-relaxed italic">
                         Your library contains all tools and automation chains you've acquired or built. Use the API integration guides on each card to connect them to your apps.
                       </p>
                    </div>
                 </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'library' && (
          <div className="space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex flex-col gap-2">
              <h2 className="text-4xl font-extrabold tracking-tight">My Library</h2>
              <p className="text-muted-foreground text-lg">Manage and execute your acquired AI assets.</p>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
               {myTools.map(tool => (
                 <ToolCard 
                    key={tool.id} 
                    tool={tool}
                    isOwned={true}
                    onAcquire={() => {}}
                    onRun={(input) => runSingleTool(tool, input)}
                    isLoading={loading}
                    apiKey={apiKey}
                  />
               ))}
               {myAgents.map(agent => (
                 <AgentCard 
                    key={agent.agent_id} 
                    agent={agent} 
                    isOwned={true}
                    onRun={(input) => runSingleAgent(agent.agent_id, input)}
                    onAddToWorkflow={() => {
                      setWorkflow([...workflow, agent.agent_id]);
                      setActiveTab('workflow');
                    }}
                    onShare={() => deployAgent(agent.agent_id)}
                    isLoading={loading}
                    apiKey={apiKey}
                  />
               ))}
               {myWorkflows.map(w => (
                 <div key={w.id} className="p-6 rounded-3xl border border-border bg-card hover:border-primary/40 transition-all group flex flex-col h-[280px]">
                    <div className="flex items-start justify-between mb-4">
                        <div className="p-3 rounded-2xl bg-secondary text-primary">
                          <Plus size={24} />
                        </div>
                    </div>
                    <div className="flex-1">
                       <div className="font-extrabold text-2xl group-hover:text-primary transition-colors mb-2">{w.name}</div>
                       <div className="flex gap-1 flex-wrap">
                          {w.steps.map((s, i) => (
                             <span key={i} className="px-2 py-0.5 bg-secondary text-[10px] font-bold rounded-md border border-border">{s}</span>
                          ))}
                       </div>
                    </div>
                    <button onClick={() => { setWorkflow(w.steps); setActiveTab('workflow'); }} className="mt-4 w-full py-3 bg-primary text-primary-foreground rounded-xl font-bold hover:opacity-90 transition-all flex items-center justify-center gap-2">
                       <Play size={16} /> Load into Builder
                    </button>
                 </div>
               ))}
            </div>
          </div>
        )}

        {activeTab === 'workflow' && (
          <WorkflowBuilder 
            workflow={workflow} 
            setWorkflow={setWorkflow} 
            agents={myAgents} // Only use owned agents in builder
            onRun={runWorkflow}
            onSave={saveWorkflow}
            onDeploy={deployWorkflow}
            isLoading={loading}
            suggestWorkflow={suggestWorkflow}
            autoTask={autoTask}
          />
        )}

        {activeTab === 'logs' && (
          <ExecutionPanel result={executionResult} />
        )}
      </main>
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );

  if (!apiKey) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen p-4 bg-background selection:bg-primary/20">
        <div className="w-full max-w-md p-10 rounded-[2.5rem] border border-border bg-card shadow-2xl animate-in fade-in zoom-in duration-500">
          <div className="flex justify-center mb-8">
            <div className="p-5 rounded-3xl bg-primary/10 text-primary shadow-inner">
              <Zap size={56} className="fill-current" />
            </div>
          </div>
          <h1 className="text-4xl font-black text-center tracking-tight mb-2">AgentMarket</h1>
          <p className="text-muted-foreground text-center mb-10 font-medium">Own and orchestrate elite AI intelligence.</p>
          
          <div className="flex gap-1 p-1 bg-secondary rounded-2xl mb-8">
            {['login', 'register', 'key'].map(mode => (
              <button 
                key={mode}
                onClick={() => setAuthMode(mode)} 
                className={cn(
                  "flex-1 py-2.5 text-xs font-black uppercase tracking-widest rounded-xl transition-all", 
                  authMode === mode ? "bg-card text-foreground shadow-lg" : "text-muted-foreground hover:text-foreground"
                )}
              >
                {mode}
              </button>
            ))}
          </div>

          <div className="space-y-5">
            {authMode !== 'key' ? (
              <>
                <div className="relative">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground" size={20} />
                  <input 
                    type="text" 
                    placeholder="Username" 
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    className="w-full pl-12 pr-4 py-4 bg-secondary border border-border rounded-2xl outline-none focus:ring-2 ring-primary/20 transition-all font-bold"
                  />
                </div>
                <div className="relative">
                  <Key className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground" size={20} />
                  <input 
                    type="password" 
                    placeholder="Password" 
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full pl-12 pr-4 py-4 bg-secondary border border-border rounded-2xl outline-none focus:ring-2 ring-primary/20 transition-all font-bold"
                  />
                </div>
                <button
                  onClick={authMode === 'login' ? login : register}
                  disabled={isRegistering || !username || !password}
                  className="w-full py-4 px-4 bg-primary text-primary-foreground rounded-2xl font-black uppercase tracking-widest hover:opacity-90 disabled:opacity-50 transition-all flex items-center justify-center gap-2 group shadow-xl shadow-primary/20"
                >
                  {isRegistering ? 'Connecting...' : (authMode === 'login' ? 'Enter Terminal' : 'Create Identity')}
                  <ChevronRight size={18} className="group-hover:translate-x-1 transition-transform" />
                </button>
              </>
            ) : (
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Key className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground" size={20} />
                    <input 
                      type="text" 
                      placeholder="ag-... private key" 
                      className="w-full pl-12 pr-4 py-4 bg-secondary border border-border rounded-2xl outline-none focus:ring-2 ring-primary/20 transition-all font-bold font-mono"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          setApiKey(e.target.value);
                          localStorage.setItem('ag_api_key', e.target.value);
                        }
                      }}
                    />
                  </div>
                </div>
            )}
          </div>
        </div>
        {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
      </div>
    );
  }

  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/use/:slug" element={<PublicAgent />} />
    </Routes>
  );
}

export default App;
