import React, { useState } from 'react';
import { Terminal, Copy, CheckCircle2, Globe, Code } from 'lucide-react';

const ApiGuide = ({ id, type = 'agent', apiKey }) => {
  const [activeLang, setActiveLang] = useState('curl');
  const [copied, setCopied] = useState(false);

  const baseUrl = 'http://localhost:8000';
  const endpoint = type === 'agent' ? `${baseUrl}/run/` : `${baseUrl}/tools/execute/${id}`;
  
  const getPayload = () => {
    if (type === 'agent') {
      return {
        mode: "manual",
        agent_id: id,
        input: "Your task here"
      };
    } else {
      return {
        input: "Your tool input here"
      };
    }
  };

  const payload = getPayload();

  const snippets = {
    curl: `curl -X POST ${endpoint} \\
  -H "Content-Type: application/json" \\
  -H "x-api-key: ${apiKey}" \\
  -d '${JSON.stringify(payload, null, 2)}'`,

    javascript: `fetch('${endpoint}', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'x-api-key': '${apiKey}'
  },
  body: JSON.stringify(${JSON.stringify(payload, null, 2)})
}).then(res => res.json()).then(console.log);`,

    python: `import requests

url = "${endpoint}"
headers = {"x-api-key": "${apiKey}", "Content-Type": "application/json"}
data = ${JSON.stringify(payload, null, 2)}

response = requests.post(url, json=data, headers=headers)
print(response.json())`
  };

  const handleCopy = () => {
    navigator.clipboard.writeText(snippets[activeLang]);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-secondary/50 rounded-2xl border border-border overflow-hidden">
      <div className="px-6 py-4 border-b border-border flex items-center justify-between bg-card">
        <div className="flex items-center gap-2 font-bold text-sm">
          <Terminal size={16} className="text-primary" />
          {type === 'agent' ? 'Agent' : 'Tool'} Integration
        </div>
        <div className="flex gap-2">
          {['curl', 'javascript', 'python'].map(lang => (
            <button
              key={lang}
              onClick={() => setActiveLang(lang)}
              className={`px-3 py-1 text-[10px] uppercase font-bold rounded-md transition-all ${
                activeLang === lang ? 'bg-primary text-primary-foreground' : 'text-muted-foreground hover:bg-secondary'
              }`}
            >
              {lang}
            </button>
          ))}
        </div>
      </div>

      <div className="relative p-6 bg-black/40">
        <button
          onClick={handleCopy}
          className="absolute top-4 right-4 p-2 bg-background/50 border border-border/50 rounded-lg text-muted-foreground hover:text-foreground transition-all"
        >
          {copied ? <CheckCircle2 size={16} className="text-emerald-500" /> : <Copy size={16} />}
        </button>
        <pre className="text-xs font-mono text-emerald-400 overflow-x-auto whitespace-pre-wrap leading-relaxed">
          {snippets[activeLang]}
        </pre>
      </div>

      <div className="px-6 py-4 bg-muted/30 flex items-center gap-4 text-[11px] text-muted-foreground border-t border-border overflow-x-auto scrollbar-hide">
         <div className="flex items-center gap-1 whitespace-nowrap"><Globe size={12} /> Endpoint: {endpoint.replace('http://', '')}</div>
         <div className="flex items-center gap-1 whitespace-nowrap"><Code size={12} /> Format: JSON</div>
      </div>
    </div>
  );
};

export default ApiGuide;
