'use client';

import { useEffect, useState } from 'react';
import { fetchLogs } from '@/lib/api';
import { JobLogItem } from '@/lib/types';
import { Terminal as TerminalIcon, Filter, Search, ShieldCheck } from 'lucide-react';

export default function LogsPage() {
  const [logs, setLogs] = useState<JobLogItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [filterLevel, setFilterLevel] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchLogs();
        setLogs(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    load();
    const interval = setInterval(load, 3000);
    return () => clearInterval(interval);
  }, []);

  const filteredLogs = logs.filter((l) => {
    const matchesLevel = filterLevel === 'ALL' || l.log_level === filterLevel;
    const matchesSearch = 
      l.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
      l.agent_name.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesLevel && matchesSearch;
  });

  return (
    <div className="space-y-8 animate-in fade-in duration-300 pb-12">
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-extrabold text-white flex items-center gap-2">
            <TerminalIcon className="w-6 h-6 text-blue-400" /> Structured System Logs
          </h1>
          <p className="text-xs text-slate-400 mt-1">Real-time trace logs from all 14 autonomous agents & QA gates</p>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative w-full sm:w-64">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search agent or message..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-4 py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>

          <div className="flex items-center gap-1 p-1 rounded-xl bg-slate-900 border border-slate-800/80">
            {['ALL', 'INFO', 'SUCCESS', 'WARNING', 'ERROR'].map((lvl) => (
              <button
                key={lvl}
                onClick={() => setFilterLevel(lvl)}
                className={`px-2.5 py-1 rounded-lg text-xs font-bold transition-all ${
                  filterLevel === lvl
                    ? 'bg-blue-600 text-white shadow-sm'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {lvl}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Terminal View Container */}
      <div className="rounded-3xl glass-card border border-slate-800/90 overflow-hidden shadow-2xl">
        {/* Terminal Titlebar */}
        <div className="h-10 bg-slate-900/90 border-b border-slate-800/80 px-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-red-500/80 inline-block"></span>
            <span className="w-3 h-3 rounded-full bg-amber-500/80 inline-block"></span>
            <span className="w-3 h-3 rounded-full bg-emerald-500/80 inline-block"></span>
            <span className="text-xs font-mono text-slate-400 ml-2">autotube-agent.log</span>
          </div>
          <span className="text-[11px] font-mono text-emerald-400 flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5" /> LIVE STREAMING
          </span>
        </div>

        {/* Log Entries */}
        <div className="p-4 font-mono text-xs space-y-2 max-h-[600px] overflow-y-auto bg-slate-950/80">
          {loading ? (
            <div className="py-12 text-center space-y-2">
              <div className="w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto"></div>
              <p className="text-slate-400 font-mono text-xs">Streaming logs from agents...</p>
            </div>
          ) : filteredLogs.length === 0 ? (
            <p className="text-slate-500 py-8 text-center">No log traces match the selected criteria.</p>
          ) : (
            filteredLogs.map((log) => (
              <div
                key={log.id}
                className="p-2.5 rounded-xl bg-slate-900/50 border border-slate-800/60 flex items-start gap-3 hover:bg-slate-900/90 transition-colors"
              >
                <span className="text-slate-500 text-[11px] shrink-0 pt-0.5">{log.timestamp}</span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-black uppercase shrink-0 ${
                    log.log_level === 'SUCCESS'
                      ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                      : log.log_level === 'WARNING'
                      ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                      : log.log_level === 'ERROR'
                      ? 'bg-red-500/15 text-red-400 border border-red-500/30'
                      : 'bg-blue-500/15 text-blue-400 border border-blue-500/30'
                  }`}
                >
                  {log.log_level}
                </span>
                <span className="text-blue-300 font-bold shrink-0">[{log.agent_name}]</span>
                <span className="text-slate-200 leading-relaxed">{log.message}</span>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}

