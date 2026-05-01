import React from 'react';
import { Terminal, CheckCircle2, XCircle, Clock, Database, User, Cpu, ChevronRight, Activity } from 'lucide-react';
import { cn } from '../lib/utils';
import ResultViewer from './ResultViewer';

export default function ExecutionPanel({ result }) {
  if (!result) {
    return (
      <div className="flex flex-col items-center justify-center py-[20vh] text-center space-y-4 animate-in fade-in duration-700">
        <div className="p-6 rounded-full bg-secondary/50 text-muted-foreground animate-pulse">
          <Terminal size={48} />
        </div>
        <div className="space-y-1">
          <h2 className="text-2xl font-bold">Waiting for Request</h2>
          <p className="text-muted-foreground max-w-md">Run an agent or launch a workflow to see real-time execution logs and final outputs.</p>
        </div>
      </div>
    );
  }

  const steps = result.agent ? [result] : (result.steps || []);
  const status = result.workflow_status || result.status;

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className={cn(
            "p-2 rounded-xl border flex items-center justify-center",
            status === 'success' || status === 'completed' ? "bg-emerald-500/10 text-emerald-500 border-emerald-500/20" : "bg-red-500/10 text-red-500 border-red-500/20"
          )}>
            {status === 'success' || status === 'completed' ? <CheckCircle2 size={24} /> : <XCircle size={24} />}
          </div>
          <div>
            <h2 className="text-2xl font-bold tracking-tight">Execution Result</h2>
            <p className="text-sm text-muted-foreground">{steps.length} Step(s) Processed</p>
          </div>
        </div>
        
      </div>
      
      {result.input && (
        <div className="p-6 rounded-[2rem] bg-secondary/30 border border-border space-y-3">
          <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-primary">
            <User size={14} /> Primary Query
          </div>
          <div className="text-lg font-medium tracking-tight text-foreground leading-relaxed">
            {result.input}
          </div>
        </div>
      )}

      {steps.length === 0 && status === 'failed' && (
        <div className="p-6 rounded-[2rem] bg-red-500/10 border border-red-500/20 space-y-3">
          <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-red-500">
            <XCircle size={14} /> Execution Error
          </div>
          <div className="text-sm font-mono tracking-tight text-red-500 leading-relaxed whitespace-pre-wrap">
            {result.output || result.error || "An unknown error occurred during execution."}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6">
        {steps.map((step, idx) => (
          <div key={idx} className="group relative rounded-3xl border border-border bg-card overflow-hidden transition-all hover:border-primary/30">
            <div className="flex flex-col md:flex-row">
              {/* Sidebar Info */}
              <div className="w-full md:w-64 p-6 bg-secondary/30 border-b md:border-b-0 md:border-r border-border space-y-6">
                <div className="flex items-center gap-2">
                  <div className="w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-[10px] font-bold">
                    STEP {idx + 1}
                  </div>
                  <span className="font-bold text-sm">{step.agent}</span>
                </div>

                <div className="space-y-4">
                    <div className="flex items-center gap-2 text-[10px] text-muted-foreground uppercase font-bold tracking-wider">
                      <Clock size={12} /> Latency
                    </div>
                    <div className="text-sm font-mono text-primary">{step.latency || ((step.metadata?.duration || 0) / 1e9).toFixed(2) + 's'}</div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 text-[10px] text-muted-foreground uppercase font-bold tracking-wider">
                      <Cpu size={12} /> Model
                    </div>
                    <div className="text-sm font-mono">{step.metadata?.model || 'llama3'}</div>
                  </div>
                </div>

                <div className={cn(
                  "px-3 py-1.5 rounded-lg text-xs font-bold uppercase tracking-tight flex items-center justify-center gap-2",
                  step.status === 'success' ? "bg-emerald-500/10 text-emerald-500" : "bg-red-500/10 text-red-500"
                )}>
                  {step.status === 'success' ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
                  {step.status}
                </div>
              </div>

              {/* Main Output */}
              <div className="flex-1 flex flex-col p-6 overflow-hidden space-y-6">
                {step.input && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground">
                      <Terminal size={14} /> QUERY_INPUT
                    </div>
                    <div className="p-4 rounded-xl bg-primary/5 border border-primary/10 text-xs font-mono whitespace-pre-wrap overflow-x-auto max-h-32 custom-scrollbar">
                      {typeof step.input === 'object' ? JSON.stringify(step.input, null, 2) : step.input}
                    </div>
                  </div>
                )}

                <div className="space-y-4 flex-1 flex flex-col">
                  {step.steps && step.steps.length > 0 && (
                    <div className="space-y-3 mb-4 border-b border-border/50 pb-4">
                      <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground">
                        <Terminal size={14} /> INTERNAL_TOOLS_EXECUTED ({step.steps.length})
                      </div>
                      <div className="grid grid-cols-1 gap-2">
                        {step.steps.map((s, i) => (
                          <div key={i} className="p-3 rounded-lg bg-black/20 border border-border/50">
                            <div className="text-xs font-bold text-primary font-mono mb-1">▶ {s.tool}</div>
                            <div className="text-[10px] text-muted-foreground font-mono truncate">{JSON.stringify(s.input)}</div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  <div className="flex items-center gap-2 text-xs font-mono text-muted-foreground">
                    <Terminal size={14} /> RESULT_OUTPUT
                  </div>
                  {step.status === 'failed' ? (
                    <div className="p-4 rounded-xl bg-red-500/5 text-red-500 border border-red-500/20 whitespace-pre-wrap font-mono text-sm">
                      Error generating response: {step.output}
                    </div>
                  ) : (
                    <ResultViewer content={step.output} />
                  )}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {steps.length > 0 && (status === 'completed' || status === 'success') && (
        <div className="p-8 rounded-3xl bg-primary/5 border border-primary/20 flex flex-col items-center justify-center text-center space-y-6 animate-in zoom-in duration-700">
          <div className="p-4 rounded-full bg-primary/10 text-primary shadow-2xl shadow-primary/20">
            <CheckCircle2 size={48} />
          </div>
          <div className="space-y-2">
            <h3 className="text-3xl font-extrabold tracking-tight">Sequence Terminated Successfully</h3>
            <p className="text-muted-foreground max-w-md">The workflow has been orchestrated and execution is complete. All outputs were chained across agents.</p>
          </div>
        </div>
      )}
    </div>
  );
}
