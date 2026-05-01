import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Copy, CheckCircle2 } from 'lucide-react';

const ResultViewer = ({ content }) => {
  const [copied, setCopied] = React.useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!content) return null;

  return (
    <div className="relative group bg-secondary/30 rounded-2xl border border-border overflow-hidden">
      <div className="absolute top-4 right-4 z-10">
        <button
          onClick={handleCopy}
          className="p-2 bg-background/80 backdrop-blur-md border border-border rounded-lg text-muted-foreground hover:text-foreground transition-all"
          title="Copy to clipboard"
        >
          {copied ? <CheckCircle2 size={16} className="text-emerald-500" /> : <Copy size={16} />}
        </button>
      </div>

      <div className="p-6 prose prose-invert prose-sm max-w-none overflow-auto max-h-[600px] custom-scrollbar">
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {content}
        </ReactMarkdown>
      </div>
    </div>
  );
};

export default ResultViewer;
