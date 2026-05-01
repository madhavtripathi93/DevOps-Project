import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';
import { Zap, Play, CheckCircle2, XCircle, Info, Cpu, Sparkles, Terminal, Activity, Clock, Key, ChevronRight } from 'lucide-react';
import { cn } from '../lib/utils';
import ResultViewer from '../components/ResultViewer';
import Toast from '../components/Toast';
import { useLocation } from 'react-router-dom';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export default function PublicAgent() {
  const { slug } = useParams();
  const location = useLocation();
  const isWorkflow = new URLSearchParams(location.search).get('type') === 'workflow';
  const [agent, setAgent] = useState(null);
  const [input, setInput] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState('loading'); // 'loading', 'ready', 'error'
  const [apiKey, setApiKey] = useState(sessionStorage.getItem('ag_api_key') || '');
  const [toast, setToast] = useState(null);
  const [localUsername, setLocalUsername] = useState('');
  const [localPassword, setLocalPassword] = useState('');

  const showToast = (message, type = 'info') => {
    setToast({ message, type });
  };

  useEffect(() => {
    if (apiKey) {
      fetchAgentInfo();
    } else {
      setStatus('ready'); // Ready to show login state
    }
  }, [slug, apiKey]);

  const login = async () => {
    if (!localUsername || !localPassword) {
      showToast('Username and Password are required', 'error');
      return;
    }
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE}/auth/login`, { username: localUsername, password: localPassword });
      const key = res.data.api_key;
      setApiKey(key);
      sessionStorage.setItem('ag_api_key', key);
      showToast('Authorized successfully.', 'success');
      // fetchAgentInfo will trigger due to useEffect [apiKey]
    } catch (err) {
      showToast(err.response?.data?.detail || 'Login failed.', 'error');
    } finally {
      setLoading(false);
    }
  };

  const fetchAgentInfo = async () => {
    try {
      const endpoint = isWorkflow ? `/deploy/public/workflow/${slug}` : `/deploy/public/agent/${slug}`;
      const res = await axios.get(`${API_BASE}${endpoint}`, {
        headers: { 'x-api-key': apiKey }
      });
      setAgent(res.data);
      setStatus('ready');
    } catch (err) {
      console.error('Failed to fetch agent', err);
      setStatus('error');
    }
  };

  const runAgent = async () => {
    if (!input || !apiKey) return;
    setLoading(true);
    try {
      const endpoint = isWorkflow ? `/deploy/public/workflow/${slug}/run` : `/deploy/public/agent/${slug}/run`;
      const res = await axios.post(`${API_BASE}${endpoint}`, 
        { input },
        { headers: { 'x-api-key': apiKey } }
      );
      setResult(res.data);
      sessionStorage.setItem('ag_api_key', apiKey); // Ensure it's in session for next refreshes
      showToast('Task completed successfully!', 'success');
    } catch (err) {
      if (err.response?.status === 401) {
        setApiKey('');
        sessionStorage.removeItem('ag_api_key');
        showToast('Your session has expired or API key is invalid. Please log in.', 'error');
      } else {
        showToast(err.response?.data?.message || err.message, 'error');
      }
      setResult({ status: 'failed', output: err.response?.data?.message || err.message });
    } finally {
      setLoading(false);
    }
  };

  if (!apiKey) {
     return (
        <div className="flex flex-col items-center justify-center min-h-screen p-4 bg-background">
          <div className="w-full max-w-md p-10 rounded-[2.5rem] border border-border bg-card shadow-2xl animate-in zoom-in-95 duration-500 text-center">
            <div className="flex justify-center mb-8">
              <div className="p-5 rounded-3xl bg-amber-500/10 text-amber-500">
                <Key size={48} />
              </div>
            </div>
            <h1 className="text-3xl font-black mb-4">Authentication Required</h1>
            <p className="text-muted-foreground mb-10 leading-relaxed font-medium capitalize">
               To protect platform resources, this {isWorkflow ? 'workflow pipeline' : 'agent tool'} requires a valid identity to proceed. 
            </p>
            <div className="space-y-4">
               <input 
                  type="text" 
                  placeholder="Username" 
                  value={localUsername} 
                  onChange={(e) => setLocalUsername(e.target.value)}
                  className="w-full px-4 py-4 bg-secondary border border-border rounded-2xl outline-none focus:ring-2 ring-primary/20 text-center font-bold"
               />
               <input 
                  type="password" 
                  placeholder="Password" 
                  value={localPassword} 
                  onChange={(e) => setLocalPassword(e.target.value)}
                  className="w-full px-4 py-4 bg-secondary border border-border rounded-2xl outline-none focus:ring-2 ring-primary/20 text-center font-bold"
               />
               <button 
                  onClick={login}
                  className="w-full py-4 bg-primary text-primary-foreground rounded-2xl font-black uppercase tracking-widest hover:opacity-90 flex items-center justify-center gap-2"
               >
                  Verify Identity <ChevronRight size={18} />
               </button>
            </div>
          </div>
          {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
        </div>
      );
    }

  if (status === 'loading') {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-background">
        <div className="w-12 h-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
        <p className="mt-4 text-muted-foreground font-medium">Connecting to AgentFlow...</p>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-background p-4 text-center">
        <div className="p-4 rounded-full bg-destructive/10 text-destructive mb-6">
          <XCircle size={48} />
        </div>
        <h1 className="text-3xl font-bold mb-2">Link Expired or Invalid</h1>
        <p className="text-muted-foreground max-w-md">The agent deployment you are looking for does not exist or has been deactivated by the owner.</p>
        <a href="/" className="mt-8 text-primary font-bold hover:underline">Go to Marketplace</a>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-20">
      {/* Premium Header */}
      <nav className="h-20 border-b border-border bg-background/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-4 h-full flex items-center justify-between">
          <div className="flex items-center gap-2 font-bold text-xl text-primary">
            <Zap /> <span>AgentFlow <span className="text-muted-foreground/50 font-medium">Shared</span></span>
          </div>
          <div className="px-4 py-1.5 rounded-full bg-primary/10 text-primary text-xs font-bold uppercase tracking-widest border border-primary/20">
            Hosted Instance
          </div>
        </div>
      </nav>

      <main className="max-w-4xl mx-auto px-4 pt-12 space-y-12">
        <div className="text-center space-y-4">
          <div className="p-5 rounded-3xl bg-indigo-600 text-white inline-flex shadow-2xl shadow-indigo-600/30 mb-4 animate-in zoom-in duration-700">
            <Cpu size={40} />
          </div>
          <h1 className="text-5xl font-extrabold tracking-tight">{agent.name}</h1>
          <p className="text-xl text-muted-foreground max-w-2xl mx-auto">{agent.description}</p>{agent.steps && (<div className="flex flex-wrap justify-center gap-1.5 pt-4">{agent.steps.map((s, i) => (<span key={i} className="px-2 py-0.5 bg-secondary text-[8px] font-bold rounded border border-border uppercase">{s}</span>))} </div>)}
          
          <div className="flex flex-wrap justify-center gap-2 pt-4">
            {agent.capabilities?.map((cap, i) => (
              <span key={i} className="px-3 py-1 bg-blue-500/10 text-blue-500 text-[10px] font-bold uppercase tracking-widest rounded-full border border-blue-500/20">
                {cap}
              </span>
            ))}
            {agent.skills?.map((skill, i) => (
              <span key={i} className="px-3 py-1 bg-emerald-500/10 text-emerald-500 text-[10px] font-bold uppercase tracking-widest rounded-full border border-emerald-500/20">
                {skill}
              </span>
            ))}
          </div>
        </div>

        <div className="bg-card border-2 border-border rounded-[2.5rem] p-8 shadow-2xl relative overflow-hidden group">
          <div className="absolute top-0 right-0 p-8 text-primary/5 -z-10 group-hover:scale-110 transition-transform duration-1000">
             <Sparkles size={120} />
          </div>
          
          <div className="space-y-6">
            <div className="flex items-center gap-2 text-sm font-bold text-muted-foreground uppercase tracking-widest">
              <Info size={16} /> Describe your task
            </div>
            <textarea 
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={`Enter input for ${agent.name}...`}
              className="w-full min-h-[160px] p-6 bg-secondary/50 border-2 border-border rounded-3xl outline-none focus:border-primary/50 focus:ring-8 ring-primary/5 transition-all text-lg font-medium resize-none shadow-inner"
            />
            {apiKey ? (
              <button 
                onClick={runAgent}
                disabled={loading || !input}
                className="w-full py-5 px-8 bg-primary text-primary-foreground rounded-[2rem] font-extrabold text-xl shadow-xl shadow-primary/20 hover:scale-[1.01] active:scale-[0.99] disabled:opacity-50 disabled:scale-100 transition-all flex items-center justify-center gap-3"
              >
                {loading ? <Spinner className="animate-spin" /> : <Play size={24} className="fill-current" />}
                {loading ? 'Executing Agent...' : `Run ${agent.name}`}
              </button>
            ) : (
              <div className="space-y-4 p-8 rounded-3xl bg-secondary/50 border-2 border-dashed border-border text-center animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="w-16 h-16 bg-background rounded-2xl flex items-center justify-center mx-auto mb-2 text-primary shadow-lg">
                  <Terminal size={32} />
                </div>
                <div className="space-y-1">
                  <h3 className="font-bold text-lg">Secure Execution Required</h3>
                  <p className="text-sm text-muted-foreground">You must be a platform member to run shared agents. This ensures secure usage and tracking.</p>
                </div>
                <div className="flex gap-3 pt-2">
                  <a 
                    href="/" 
                    className="flex-1 py-4 bg-primary text-primary-foreground rounded-2xl font-bold hover:opacity-90 transition-all"
                  >
                    Log In / Register
                  </a>
                </div>
              </div>
            )}
          </div>
        </div>

        {result && (
          <div className="animate-in fade-in slide-in-from-top-8 duration-500">
            <div className="flex items-center gap-4 mb-6">
              <div className="h-px flex-1 bg-border" />
              <div className="px-4 py-1 rounded-full border border-border bg-secondary text-muted-foreground text-xs font-bold uppercase tracking-widest">
                Execution Result
              </div>
              <div className="h-px flex-1 bg-border" />
            </div>

            <div className="p-8 rounded-[2.5rem] bg-card border-2 border-border shadow-2xl space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  {result.status === 'success' ? (
                    <div className="p-2 rounded-xl bg-emerald-500/10 text-emerald-500">
                      <CheckCircle2 size={24} />
                    </div>
                  ) : (
                    <div className="p-2 rounded-xl bg-destructive/10 text-destructive">
                      <XCircle size={24} />
                    </div>
                  )}
                  <div>
                    <h3 className="font-bold text-lg">{result.status === 'success' ? 'Task Completed' : 'Execution Failed'}</h3>
                    <p className="text-sm text-muted-foreground">{new Date().toLocaleTimeString()}</p>
                  </div>
                </div>
                <div className="text-xs font-bold text-primary px-3 py-1 bg-primary/10 rounded-lg uppercase">
                  {agent.output_type}
                </div>
              </div>

              {/* Multi-step A2A Output or Single Result */}
              <div className="space-y-6">
                {result.steps ? (
                   <div className="space-y-4">
                     {result.steps.map((step, idx) => (
                       <div key={idx} className="p-6 rounded-3xl bg-secondary/20 border border-border space-y-4">
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <div className="w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-[10px] font-bold">
                                {idx + 1}
                              </div>
                              <span className="font-bold text-sm text-foreground">{step.agent}</span>
                            </div>
                            <div className="text-[10px] font-mono text-muted-foreground">
                              {step.status === 'success' ? 'COMPLETED' : 'FAILED'}
                            </div>
                          </div>
                          <ResultViewer content={step.output} />
                       </div>
                     ))}
                   </div>
                ) : (
                  <ResultViewer content={result.output} />
                )}
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="mt-20 text-center text-muted-foreground text-sm flex items-center justify-center gap-2">
        Powered by <Zap size={14} className="text-primary fill-current" /> <span className="font-bold">AgentFlow Marketplace</span>
      </footer>
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
}

function Spinner({ className }) {
  return (
    <svg className={className} width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeOpacity="0.25" strokeWidth="3" />
      <path d="M12 2C6.47715 2 2 6.47715 2 12C2 13.9113 2.53508 15.6974 3.46821 17.2188" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
}
