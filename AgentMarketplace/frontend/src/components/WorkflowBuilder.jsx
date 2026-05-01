import React, { useState, useEffect } from 'react';
import { Plus, Trash2, ArrowRight, Play, Info, Sparkles, AlertCircle, Cpu, ChevronRight, Wand2, Save, Share2 } from 'lucide-react';
import { cn } from '../lib/utils';

export default function WorkflowBuilder({ workflow, setWorkflow, agents, onRun, onSave, onDeploy, isLoading, suggestWorkflow, autoTask }) {
  const [input, setInput] = useState('');
  const [localMode, setLocalMode] = useState('none'); // 'none', 'auto', 'manual'
  const [localAutoInput, setLocalAutoInput] = useState('');
  const [workflowName, setWorkflowName] = useState('');
  const [showSaveDialog, setShowSaveDialog] = useState(false);

  // Sync initial input when AI suggests a task
  useEffect(() => {
    if (autoTask && workflow.length > 0) {
      setInput(autoTask);
    }
  }, [autoTask, workflow.length]);

  const removeStep = (index) => {
    const newWorkflow = [...workflow];
    newWorkflow.splice(index, 1);
    setWorkflow(newWorkflow);
  };

  const addAgent = (agentId) => {
    setWorkflow([...workflow, agentId]);
  };

  const handleSuggest = async () => {
    await suggestWorkflow(localAutoInput);
    setLocalMode('none'); // Reset view after suggestion is handled by parent
  };

  return (
    <div className="max-w-4xl mx-auto space-y-12 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="text-center space-y-4">
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary/10 text-primary text-xs font-bold uppercase tracking-wider rounded-full border border-primary/20">
          <Sparkles size={14} /> Pipeline Orchestrator
        </div>
        <h2 className="text-4xl font-extrabold tracking-tight">Design Multi-Agent Flow</h2>
        <p className="text-muted-foreground text-lg">Chain multiple agents together to automate complex reasoning tasks.</p>
      </div>

      {workflow.length === 0 && localMode === 'none' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 py-12">
          <button 
            onClick={() => setLocalMode('auto')}
            className="p-8 rounded-[2.5rem] bg-indigo-600 text-white text-left space-y-6 hover:scale-[1.02] active:scale-[0.98] transition-all shadow-2xl shadow-indigo-500/20 group"
          >
            <div className="w-16 h-16 rounded-3xl bg-white/10 flex items-center justify-center">
              <Wand2 size={32} />
            </div>
            <div className="space-y-2">
              <h3 className="text-2xl font-bold">Build with AI</h3>
              <p className="text-indigo-100/70">Describe your task and let our router suggest the best agents.</p>
            </div>
            <div className="flex items-center gap-2 text-sm font-bold text-indigo-200 group-hover:gap-4 transition-all">
              GET STARTED <ChevronRight size={16} />
            </div>
          </button>

          <button 
            onClick={() => setLocalMode('manual')}
            className="p-8 rounded-[2.5rem] bg-card border-4 border-dashed border-border text-left space-y-6 hover:border-primary/50 hover:bg-primary/5 transition-all group"
          >
            <div className="w-16 h-16 rounded-3xl bg-secondary flex items-center justify-center text-muted-foreground group-hover:text-primary transition-all">
              <Plus size={32} />
            </div>
            <div className="space-y-2">
              <h3 className="text-2xl font-bold">Start from Scratch</h3>
              <p className="text-muted-foreground">Manually select and sequence agents from the marketplace.</p>
            </div>
            <div className="flex items-center gap-2 text-sm font-bold text-muted-foreground group-hover:text-primary transition-all">
              BUILD MANUALLY <ChevronRight size={16} />
            </div>
          </button>
        </div>
      ) : workflow.length === 0 && localMode === 'auto' ? (
        <div className="py-12 space-y-8 animate-in zoom-in duration-500">
           <button onClick={() => setLocalMode('none')} className="text-muted-foreground hover:text-foreground text-sm font-bold flex items-center gap-2">
             <ChevronRight size={16} className="rotate-180" /> BACK TO OPTIONS
           </button>
           <div className="bg-indigo-600/5 border-2 border-indigo-500/20 rounded-[3rem] p-12 text-center space-y-8">
              <div className="w-20 h-20 mx-auto rounded-full bg-indigo-600 text-white flex items-center justify-center shadow-xl shadow-indigo-600/30">
                <Cpu size={40} />
              </div>
              <div className="space-y-2">
                <h3 className="text-3xl font-extrabold tracking-tight">AI Workflow Assistant</h3>
                <p className="text-muted-foreground text-lg">What complex task should we orchestrate for you?</p>
              </div>
              <div className="relative max-w-2xl mx-auto group">
                <input 
                  type="text" 
                  placeholder="e.g. Write a research report on the state of AI..." 
                  value={localAutoInput}
                  onChange={(e) => setLocalAutoInput(e.target.value)}
                  className="w-full pl-8 pr-20 py-6 bg-card border-2 border-border rounded-[2rem] outline-none focus:border-indigo-500/50 focus:ring-8 ring-indigo-500/5 transition-all text-xl font-medium shadow-2xl"
                  onKeyDown={(e) => e.key === 'Enter' && handleSuggest()}
                  autoFocus
                />
                <button 
                  onClick={handleSuggest}
                  disabled={isLoading || !localAutoInput}
                  className="absolute right-4 top-1/2 -translate-y-1/2 p-4 bg-indigo-600 text-white rounded-2xl hover:scale-105 active:scale-95 disabled:scale-100 disabled:opacity-50 transition-all"
                >
                  {isLoading ? <Spinner className="animate-spin" /> : <ChevronRight size={24} />}
                </button>
              </div>
           </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-start">
          {/* Step List */}
          <div className="md:col-span-2 space-y-4">
            <div className="p-8 rounded-3xl border-2 border-dashed border-border bg-card/50 flex flex-col gap-6 relative overflow-hidden">
              {workflow.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center space-y-4">
                  <div className="p-4 rounded-full bg-secondary text-muted-foreground">
                    <Plus size={32} />
                  </div>
                  <div className="space-y-1">
                    <p className="font-semibold text-lg text-foreground">Manual Builder Active</p>
                    <p className="text-muted-foreground">Select agents from the right to begin.</p>
                  </div>
                  <button onClick={() => setLocalMode('none')} className="text-primary text-sm font-bold underline">Switch to AI Assistant</button>
                </div>
              ) : (
                <div className="flex flex-col gap-4">
                  {workflow.map((agentId, idx) => {
                    const agent = agents.find(a => a.agent_id === agentId);
                    return (
                      <div key={idx} className="flex items-center gap-4 group">
                        <div className="flex-none w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center font-bold text-sm">
                          {idx + 1}
                        </div>
                        <div className="flex-1 p-4 rounded-2xl bg-card border border-border shadow-sm flex items-center justify-between group-hover:border-primary/30 transition-all">
                          <div className="flex flex-col">
                            <span className="font-bold">{agent?.name || agentId}</span>
                            <span className="text-xs text-muted-foreground uppercase">{agent?.output_type}</span>
                          </div>
                          <button 
                            onClick={() => removeStep(idx)}
                            className="p-2 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-lg transition-all"
                          >
                            <Trash2 size={18} />
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {workflow.length > 0 && (
              <div className="p-6 rounded-3xl bg-secondary/50 border border-border space-y-4 animate-in slide-in-from-top-4 duration-500">
                <div className="flex items-center gap-2 text-sm font-semibold text-muted-foreground mb-4">
                  <Info size={16} /> Initial Stage Input
                </div>
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="What should the first agent start with?"
                  className="w-full h-32 p-4 bg-background border border-border rounded-2xl outline-none focus:ring-2 ring-primary/20 transition-all resize-none font-medium"
                />
                <button
                  onClick={() => onRun(input)}
                  disabled={isLoading || !input || workflow.length === 0}
                  className="w-full py-4 bg-primary text-primary-foreground rounded-2xl font-bold text-lg shadow-lg shadow-primary/20 hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-3"
                >
                  {isLoading ? <Spinner className="animate-spin text-primary-foreground/50" /> : <Play size={20} className="fill-current" />}
                  {isLoading ? 'Executing Sequence...' : 'Launch Workflow'}
                </button>

                <div className="flex gap-2">
                   <button
                    onClick={() => setShowSaveDialog(true)}
                    disabled={isLoading || workflow.length === 0}
                    className="flex-1 py-4 bg-secondary text-foreground rounded-2xl font-bold hover:bg-secondary/80 transition-all flex items-center justify-center gap-2"
                  >
                    <Save size={20} /> Save Template
                  </button>
                  <button
                    onClick={() => setShowSaveDialog(true)}
                    disabled={isLoading || workflow.length === 0}
                    className="flex-1 py-4 bg-indigo-600/10 text-indigo-600 rounded-2xl font-bold hover:bg-indigo-600/20 transition-all flex items-center justify-center gap-2"
                  >
                    <Share2 size={20} /> Deploy & Share
                  </button>
                </div>

                {showSaveDialog && (
                   <div className="p-6 rounded-3xl bg-card border-2 border-indigo-500/20 shadow-2xl space-y-4 animate-in zoom-in-95 duration-300">
                     <div className="font-bold text-lg">Name your automation</div>
                     <input 
                       type="text" 
                       placeholder="e.g. Automated Researcher" 
                       value={workflowName}
                       onChange={(e) => setWorkflowName(e.target.value)}
                       className="w-full px-4 py-3 bg-secondary/50 border border-border rounded-xl outline-none focus:ring-2 ring-indigo-500/20"
                     />
                     <div className="flex gap-2 pt-2">
                       <button 
                         onClick={() => { onSave(workflowName); setShowSaveDialog(false); }}
                         className="flex-1 py-3 bg-primary text-primary-foreground rounded-xl font-bold shadow-lg"
                       >
                         Save to Library
                       </button>
                       <button 
                         onClick={async () => { 
                           const saved = await onSave(workflowName);
                           if (saved && saved.id) onDeploy(saved.id);
                           setShowSaveDialog(false); 
                         }}
                         className="flex-1 py-3 bg-indigo-600 text-white rounded-xl font-bold shadow-lg shadow-indigo-600/20"
                       >
                         Save & Deploy
                       </button>
                       <button onClick={() => setShowSaveDialog(false)} className="px-4 py-3 text-muted-foreground font-bold hover:text-foreground">Cancel</button>
                     </div>
                   </div>
                )}
              </div>
            )}
          </div>

          {/* Sidebar Picker */}
          <div className="space-y-4">
            <h3 className="font-bold text-lg px-2">Available Agents</h3>
            <div className="grid grid-cols-1 gap-2">
              {agents.map(agent => (
                <button
                  key={agent.agent_id}
                  onClick={() => addAgent(agent.agent_id)}
                  className="flex items-center justify-between p-4 rounded-2xl bg-card border border-border hover:border-primary/50 hover:bg-primary/5 transition-all group text-left"
                >
                  <div className="flex flex-col">
                    <span className="font-semibold">{agent.name}</span>
                    <span className="text-xs text-muted-foreground line-clamp-1">{agent.description}</span>
                  </div>
                  <div className="p-1.5 rounded-lg bg-secondary text-muted-foreground group-hover:bg-primary group-hover:text-primary-foreground transition-all">
                    <Plus size={16} />
                  </div>
                </button>
              ))}
            </div>
            
            <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-500 flex gap-3 text-sm">
              <AlertCircle size={18} className="flex-shrink-0" />
              <p>Ensure each agent's <b>Output Type</b> matches the next agent's <b>Input Type</b> for logical chaining.</p>
            </div>
          </div>
        </div>
      )}
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
