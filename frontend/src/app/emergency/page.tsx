'use client';

import React, { useState, useEffect } from 'react';
import { 
  ShieldAlert, 
  ShieldCheck, 
  OctagonAlert, 
  AlertTriangle, 
  RefreshCw, 
  Power, 
  XCircle, 
  Flame, 
  CheckCircle2, 
  RotateCcw
} from 'lucide-react';
import { EmergencyStatus, JobRecord } from '@/lib/types';

export default function EmergencyControlsPage() {
  const [status, setStatus] = useState<EmergencyStatus | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [togglingGlobal, setTogglingGlobal] = useState<boolean>(false);
  const [killingJobId, setKillingJobId] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      setLoading(true);
      const res = await fetch('http://localhost:8000/api/v1/emergency/status');
      if (res.ok) {
        const data = await res.json();
        setStatus(data);
      }
    } catch (err) {
      console.error('Failed to load emergency status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const toggleGlobalStop = async (enable: boolean) => {
    try {
      setTogglingGlobal(true);
      const res = await fetch('http://localhost:8000/api/v1/emergency/global-stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: enable, reason: 'Manual operator emergency override' })
      });
      if (res.ok) {
        await fetchStatus();
      }
    } catch (err) {
      console.error('Failed to toggle kill switch:', err);
    } finally {
      setTogglingGlobal(false);
    }
  };

  const killSpecificJob = async (jobId: string) => {
    try {
      setKillingJobId(jobId);
      const res = await fetch(`http://localhost:8000/api/v1/emergency/stop-job/${jobId}`, {
        method: 'POST'
      });
      if (res.ok) {
        await fetchStatus();
      }
    } catch (err) {
      console.error('Failed to kill job:', err);
    } finally {
      setKillingJobId(null);
    }
  };

  const isLocked = status?.global_emergency_stop ?? false;

  return (
    <div className="max-w-6xl mx-auto px-4 py-6 space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-xl bg-red-500/10 text-red-400 border border-red-500/20">
              <ShieldAlert className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-black text-white tracking-tight">Emergency Controls & Global Safety</h1>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Real-time kill switch, instant job termination, and cost safety safeguards.
          </p>
        </div>

        <button
          onClick={fetchStatus}
          className="self-start sm:self-auto p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
          title="Refresh Status"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-red-400' : ''}`} />
        </button>
      </div>

      {/* Master Kill Switch Card */}
      <div className={`rounded-2xl border p-8 shadow-2xl transition-all ${
        isLocked
          ? 'bg-red-950/40 border-red-600/50 shadow-red-950/30'
          : 'bg-slate-900/80 border-slate-800 shadow-slate-950/50'
      }`}>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              {isLocked ? (
                <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-red-500 text-white font-black text-xs uppercase tracking-wider animate-pulse">
                  <OctagonAlert className="w-4 h-4" /> Global Kill Switch Engaged
                </span>
              ) : (
                <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-400 font-bold text-xs">
                  <ShieldCheck className="w-4 h-4" /> System Guard Active (Normal)
                </span>
              )}
            </div>
            <h2 className="text-xl font-bold text-white">Master AI Pipeline Kill Switch</h2>
            <p className="text-xs text-slate-400 max-w-xl">
              Engaging this stops all active video generation runs immediately, blocks scheduled background triggers, and cancels downstream API provider calls across all channels.
            </p>
          </div>

          <div>
            {isLocked ? (
              <button
                disabled={togglingGlobal}
                onClick={() => toggleGlobalStop(false)}
                className="flex items-center gap-2 px-6 py-3.5 rounded-2xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm shadow-xl shadow-emerald-600/20 transition"
              >
                <CheckCircle2 className="w-4 h-4" /> DISENGAGE & RESUME SYSTEM
              </button>
            ) : (
              <button
                disabled={togglingGlobal}
                onClick={() => toggleGlobalStop(true)}
                className="flex items-center gap-2 px-6 py-3.5 rounded-2xl bg-red-600 hover:bg-red-500 text-white font-black text-sm shadow-xl shadow-red-600/30 transition hover:scale-105"
              >
                <Power className="w-4 h-4" /> ENGAGE EMERGENCY STOP
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Active Running Jobs Section */}
      <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-6 shadow-xl">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <h3 className="text-base font-bold text-white">Active Background Jobs</h3>
            <span className="px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 text-xs font-bold border border-blue-500/20">
              {status?.running_jobs_count || 0} Running
            </span>
          </div>
        </div>

        {(!status?.running_jobs || status.running_jobs.length === 0) ? (
          <div className="p-8 text-center rounded-xl bg-slate-950/40 border border-slate-800/60 text-xs text-slate-500">
            No active jobs currently running in queue.
          </div>
        ) : (
          <div className="space-y-3">
            {status.running_jobs.map((job) => (
              <div 
                key={job.id}
                className="flex items-center justify-between p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 text-xs"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-white font-bold">{job.id}</span>
                    <span className="px-2 py-0.5 rounded bg-purple-500/10 text-purple-400 font-semibold border border-purple-500/20">
                      {job.visual_mode}
                    </span>
                    <span className="text-slate-400">({job.job_type})</span>
                  </div>
                  <div className="text-slate-400 text-[11px]">
                    Current Stage: <span className="text-blue-400 font-semibold">{job.current_step}</span> ({job.progress_percentage}%)
                  </div>
                </div>

                <button
                  disabled={killingJobId === job.id}
                  onClick={() => killSpecificJob(job.id)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-red-600/15 hover:bg-red-600/30 text-red-300 border border-red-500/30 text-xs font-bold transition"
                >
                  <XCircle className="w-3.5 h-3.5" /> Kill Job
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
