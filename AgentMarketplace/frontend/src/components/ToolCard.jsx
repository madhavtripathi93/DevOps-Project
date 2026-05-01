import React, { useState } from 'react';
import { Settings, Info, ShoppingBag, CheckCircle2, Cpu, Play, Code } from 'lucide-react';
import { cn } from '../lib/utils';
import ApiGuide from './ApiGuide';

export default function ToolCard({ tool, onAcquire, onRun, isOwned, isLoading, apiKey }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showApi, setShowApi] = useState(false);
  const [input, setInput] = useState('');

  return (
    <div className={cn(
      "group relative flex flex-col p-6 rounded-3xl border bg-card transition-all duration-300",
      "border-border hover:border-primary/50 hover:shadow-2xl hover:shadow-primary/5",
      isExpanded || showApi ? "ring-2 ring-primary/20" : ""
    )}>
      <div className="flex items-start justify-between mb-4">
        <div className="p-3 rounded-2xl bg-secondary text-primary group-hover:bg-primary/20 transition-colors">
          <Settings size={24} />
        </div>
        <div className="flex gap-1">
          {isOwned ? (
            <>
              <button 
                onClick={() => setShowApi(!showApi)}
                className={cn("p-2 rounded-lg transition-all", showApi ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-secondary hover:text-foreground")}
                title="API Integration"
              >
                <Code size={18} />
              </button>
              <div className="px-3 py-1 rounded-full bg-emerald-500/10 text-emerald-500 text-[10px] font-bold uppercase tracking-wider flex items-center gap-1">
                 <CheckCircle2 size={10} /> Active
              </div>
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

      <div className="space-y-1 mb-4 flex-1">
        <h3 className="text-2xl font-bold tracking-tight group-hover:text-primary transition-colors">{tool.name}</h3>
        <p className="text-sm text-muted-foreground leading-relaxed line-clamp-2">{tool.description}</p>
      </div>

      {showApi && isOwned && (
        <div className="mb-6 animate-in fade-in slide-in-from-top-4 duration-300">
           <ApiGuide id={tool.name} type="tool" apiKey={apiKey} />
        </div>
      )}

      {isExpanded && (
        <div className="mb-6 p-4 rounded-xl bg-secondary/50 border border-border/50 text-xs text-muted-foreground space-y-2 animate-in fade-in zoom-in-95 duration-200">
           <div className="font-bold text-foreground">Input Schema</div>
           <pre className="text-[10px] font-mono p-2 bg-black/20 rounded-lg overflow-x-auto text-emerald-400">
             {JSON.stringify(tool.input_schema, null, 2)}
           </pre>
           <div className="pt-2 flex items-center gap-2 text-[10px] font-bold uppercase">
             <Cpu size={12} /> MCP Compatible Tool
           </div>
        </div>
      )}

      <div className="mt-4 space-y-3">
        {isOwned ? (
          <div className="space-y-3 animate-in fade-in slide-in-from-bottom-2 duration-300">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={`Input for ${tool.name}...`}
              className="w-full px-4 py-3 bg-secondary/50 border border-border rounded-xl outline-none focus:ring-2 ring-primary/20 transition-all text-sm font-medium"
            />
            <button
              onClick={() => input && onRun(input)}
              disabled={isLoading || !input}
              className="w-full py-3 px-4 bg-primary text-primary-foreground rounded-xl font-bold hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2 group/btn shadow-lg shadow-primary/20"
            >
              <Play size={18} className={cn("fill-current", isLoading && "animate-pulse")} />
              {isLoading ? 'Executing Function...' : 'Direct Execution'}
            </button>
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
