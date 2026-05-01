import React, { useState } from 'react';
import { Play, Plus, Search, Info, Terminal, ChevronRight, Activity, Share2, ShoppingBag, Code, CheckCircle2 } from 'lucide-react';
import { cn } from '../lib/utils';
import ApiGuide from './ApiGuide';

export default function AgentCard({ agent, onRun, onAddToWorkflow, onShare, onAcquire, isOwned, hideRun, isLoading, apiKey }) {
  const [input, setInput] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);
  const [showApi, setShowApi] = useState(false);

  return (
    <div className={cn(
      "group relative flex flex-col p-6 rounded-3xl border bg-card transition-all duration-300",
      "border-border hover:border-primary/50 hover:shadow-2xl hover:shadow-primary/5",
      isExpanded || showApi ? "ring-2 ring-primary/20" : ""
    )}>
      <div className="flex items-start justify-between mb-4">
        <div className="p-3 rounded-2xl bg-secondary text-primary group-hover:bg-primary/20 transition-colors">
          <Terminal size={24} />
        </div>
        <div className="flex gap-1">
          {isOwned ? (
            <>
              <button 
                onClick={() => onShare()}
                className="p-2 rounded-lg text-muted-foreground hover:bg-primary/10 hover:text-primary transition-all"
                title="Deploy & Share"
              >
                <Share2 size={18} />
              </button>
              <button 
                onClick={() => setShowApi(!showApi)}
                className={cn("p-2 rounded-lg transition-all", showApi ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-secondary hover:text-foreground")}
                title="API Integration"
              >
                <Code size={18} />
              </button>
              <button 
                onClick={() => onAddToWorkflow()}
                className="p-2 rounded-lg text-muted-foreground hover:bg-secondary hover:text-foreground transition-all"
                title="Add to Workflow"
              >
                <Plus size={18} />
              </button>
            </>
          ) : (
            <div className="px-3 py-1 rounded-full bg-primary/10 text-primary text-[10px] font-bold uppercase tracking-wider">
               Marketplace
            </div>
          )}
          <button 
            onClick={() => setIsExpanded(!isExpanded)}
            className={cn("p-2 rounded-lg transition-all", isExpanded ? "bg-secondary text-foreground" : "text-muted-foreground hover:bg-secondary hover:text-foreground")}
            title="Details"
          >
            <Info size={18} />
          </button>
        </div>
      </div>

      <div className="space-y-1 mb-4">
        <h3 className="text-2xl font-bold tracking-tight group-hover:text-primary transition-colors">{agent.name}</h3>
        <p className="text-sm text-muted-foreground leading-relaxed">{agent.description}</p>
      </div>

      {/* Expertise & Skills Badges */}
      <div className="flex flex-wrap gap-1.5 mb-6">
        {agent.capabilities?.map((cap, i) => (
          <span key={i} className="px-2 py-0.5 bg-blue-500/10 text-blue-500 text-[10px] font-bold uppercase tracking-tight rounded-md border border-blue-500/10">
            {cap}
          </span>
        ))}
        {agent.skills?.map((skill, i) => (
          <span key={i} className="px-2 py-0.5 bg-emerald-500/10 text-emerald-500 text-[10px] font-bold uppercase tracking-tight rounded-md border border-emerald-500/10">
            {skill}
          </span>
        ))}
      </div>

      {showApi && isOwned && (
        <div className="mb-6 animate-in fade-in slide-in-from-top-4 duration-300">
           <ApiGuide agentId={agent.agent_id} apiKey={apiKey} />
        </div>
      )}

      {isExpanded && (
        <div className="mb-6 p-4 rounded-xl bg-secondary/50 border border-border/50 text-xs text-muted-foreground space-y-2 animate-in fade-in zoom-in-95 duration-200">
           <div className="font-bold text-foreground">Metadata</div>
           <div className="grid grid-cols-2 gap-2">
              <div>Input Type: <span className="text-foreground">{agent.input_type}</span></div>
              <div>Output Type: <span className="text-foreground">{agent.output_type}</span></div>
              <div>Model: <span className="text-foreground">llama3.2:3b</span></div>
              <div>Status: <span className="text-emerald-500">Live</span></div>
           </div>
        </div>
      )}

      <div className="mt-auto space-y-4">
        {isOwned && !hideRun ? (
          <div className="flex flex-col gap-2 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={`Enter task for ${agent.name}...`}
              className="w-full px-4 py-3 bg-secondary/50 border border-border rounded-xl outline-none focus:ring-2 ring-primary/20 transition-all text-sm font-medium"
            />
            <button
              onClick={() => input && onRun(input)}
              disabled={isLoading || !input}
              className="w-full py-3 px-4 bg-primary text-primary-foreground rounded-xl font-bold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 group/btn shadow-lg shadow-primary/20 hover:shadow-primary/40"
            >
              <Play size={18} className={cn("fill-current", isLoading && "animate-pulse")} />
              {isLoading ? 'Running Task...' : 'Run from Library'}
            </button>
          </div>
        ) : isOwned && hideRun ? (
          <div className="w-full py-3.5 px-4 bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 rounded-xl font-bold flex items-center justify-center gap-2">
            <CheckCircle2 size={18} />
            Already in Library
          </div>
        ) : (
          <button
            onClick={() => onAcquire()}
            disabled={isLoading}
            className="w-full py-3.5 px-4 bg-secondary text-foreground border border-border rounded-xl font-bold hover:bg-primary hover:text-primary-foreground hover:border-primary transition-all flex items-center justify-center gap-2 group/btn shadow-sm"
          >
            <ShoppingBag size={18} className="transition-transform group-hover:scale-110" />
            {isLoading ? 'Processing...' : 'Acquire for Free'}
          </button>
        )}
      </div>
    </div>
  );
}
