import React, { useEffect } from 'react';
import { CheckCircle2, XCircle, Info, X } from 'lucide-react';
import { cn } from '../lib/utils';

export default function Toast({ message, type = 'info', onClose, duration = 5000 }) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose();
    }, duration);
    return () => clearTimeout(timer);
  }, [onClose, duration]);

  const icons = {
    success: <CheckCircle2 className="text-emerald-500" size={20} />,
    error: <XCircle className="text-destructive" size={20} />,
    info: <Info className="text-blue-500" size={20} />
  };

  const bgColors = {
    success: 'bg-emerald-500/10 border-emerald-500/20',
    error: 'bg-destructive/10 border-destructive/20',
    info: 'bg-blue-500/10 border-blue-500/20'
  };

  return (
    <div className={cn(
      "fixed bottom-8 right-8 z-[100] flex items-center gap-4 p-4 pr-12 rounded-2xl border bg-card/80 backdrop-blur-md shadow-2xl animate-in slide-in-from-right-8 duration-300",
      bgColors[type] || bgColors.info
    )}>
      <div className="shrink-0">
        {icons[type] || icons.info}
      </div>
      <div className="flex flex-col gap-0.5">
        <div className="text-sm font-bold capitalize">{type}</div>
        <div className="text-xs text-muted-foreground font-medium leading-tight max-w-[240px]">
          {message}
        </div>
      </div>
      <button 
        onClick={onClose}
        className="absolute top-2 right-2 p-1 rounded-lg text-muted-foreground hover:bg-secondary transition-all"
      >
        <X size={14} />
      </button>
      
      {/* Progress Bar */}
      <div className="absolute bottom-0 left-0 h-1 bg-primary/20 overflow-hidden rounded-b-2xl w-full">
         <div 
           className={cn("h-full transition-all linear", 
            type === 'success' ? 'bg-emerald-500' : type === 'error' ? 'bg-destructive' : 'bg-blue-500'
           )}
           style={{ 
             animation: `shrink ${duration}ms linear forwards`,
             width: '100%'
           }} 
         />
      </div>

      <style dangerouslySetInnerHTML={{ __html: `
        @keyframes shrink {
          from { width: 100%; }
          to { width: 0%; }
        }
      `}} />
    </div>
  );
}
