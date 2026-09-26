'use client';

import { useEffect, useState } from 'react';
import { fetchJobs, triggerWorkflow, fetchChannels, retryJob } from '@/lib/api';
import { JobRecord, YouTubeChannelItem, VisualMode } from '@/lib/types';
import AuthGuard from '@/components/AuthGuard';
import { 
  GitMerge, 
  Play, 
  CheckCircle2, 
  AlertCircle, 
  RefreshCw, 
  Zap, 
  Sparkles, 
  Activity, 
  ShieldCheck,
  Tv,
  Film,
  RotateCcw,
  Clapperboard,
  Sliders
} from 'lucide-react';

const fullAnimationAgentsList = [
  { id: 1, name: 'Master Orchestrator', role: 'Dual-mode graph state manager & cost protection', badge: 'Core' },
  { id: 2, name: 'Research Agent', role: 'Semantic memory & duplicate prevention', badge: 'AI' },
  { id: 3, name: 'Content Planner Agent', role: 'Kids format, hook targeting & duration planning', badge: 'AI' },
  { id: 4, name: 'Script Writer Agent', role: 'Devanagari Hindi dialogue & moral structure', badge: 'Gemini' },
  { id: 5, name: 'Script QA Agent', role: 'Quality gates (>=85) & automatic rewrite loop', badge: 'QA Gate' },
  { id: 6, name: 'Scene Director Agent', role: 'Scene breakdowns, character actions & mood', badge: 'Director' },
  { id: 7, name: 'Animation Director Agent', role: 'Continuity vector tracking & motion prompting', badge: 'Animation' },
  { id: 8, name: 'Visual Agent (Source Frames)', role: 'Character master reference consistency frames', badge: 'FLUX' },
  { id: 9, name: 'Animation Provider Manager', role: 'Fal AI Luma / Kling API temporal motion clips', badge: 'Fal / Luma' },
  { id: 10, name: 'Animation QA Agent', role: 'Optical-flow motion scoring & freeze detector', badge: 'Motion QA' },
  { id: 11, name: 'Voice Gen Agent', role: 'EdgeTTS Hindi Swara & Madhur voice synthesis', badge: 'Voice' },
  { id: 12, name: 'Audio Director Agent', role: 'Sound effects (SFX) & dynamic music ducking', badge: 'Audio' },
  { id: 13, name: 'Video Editor Agent', role: 'FFmpeg multi-clip concatenation & styling', badge: 'FFmpeg' },
  { id: 14, name: 'Video QA Agent', role: 'Full render integrity, audio sync & playback QA', badge: 'QA' },
  { id: 15, name: 'Metadata & SEO Agent', role: 'High-CTR titles, hashtags & Made for Kids tags', badge: 'SEO' },
  { id: 16, name: 'YouTube Upload Agent', role: 'Encrypted OAuth token upload & auto-publish', badge: 'Publish' },
];

const imageMotionAgentsList = [
  { id: 1, name: 'Master Orchestrator', role: '14-Agent pipeline coordinator', badge: 'Core' },
  { id: 2, name: 'Research Agent', role: 'Topic discovery & duplicate prevention', badge: 'AI' },
  { id: 3, name: 'Content Planner Agent', role: 'Format targeting & moral structure', badge: 'AI' },
  { id: 4, name: 'Script Writer Agent', role: 'Devanagari Hindi kids storytelling', badge: 'Gemini' },
  { id: 5, name: 'Script QA Agent', role: 'Hard Quality Gates (>=85)', badge: 'QA' },
  { id: 6, name: 'Scene Director Agent', role: 'Dynamic visual scene directions', badge: 'Director' },
  { id: 7, name: 'Voice Gen Agent', role: 'Character voice acting via EdgeTTS', badge: 'Voice' },
  { id: 8, name: 'Visual Gen Agent', role: 'FLUX.1-schnell & Pollinations 3D images', badge: 'Visual' },
  { id: 9, name: 'Video Editor Agent', role: 'FFmpeg Ken Burns motion pan & zoom', badge: 'FFmpeg' },
  { id: 10, name: 'Video QA Agent', role: 'Playback & subtitle alignment check', badge: 'QA' },
  { id: 11, name: 'Metadata SEO Agent', role: 'Hindi title, description & tags', badge: 'SEO' },
  { id: 12, name: 'Thumbnail Agent', role: 'High-CTR Devanagari 16:9 thumbnail', badge: 'Design' },
  { id: 13, name: 'YouTube Upload Agent', role: 'OAuth upload & privacy scheduling', badge: 'Publish' },
  { id: 14, name: 'Channel Learning Agent', role: 'Retention feedback optimization', badge: 'Feedback' },
];

export default function PipelinePage() {
  const [jobs, setJobs] = useState<JobRecord[]>([]);
  const [channels, setChannels] = useState<YouTubeChannelItem[]>([]);
  const [selectedChannelId, setSelectedChannelId] = useState<number | undefined>(undefined);
  const [selectedVisualMode, setSelectedVisualMode] = useState<VisualMode>('FULL_ANIMATION');
  const [loading, setLoading] = useState(true);
  const [runningType, setRunningType] = useState<string | null>(null);
  const [retryingJobId, setRetryingJobId] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const [jobsData, channelsData] = await Promise.all([
        fetchJobs(selectedChannelId),
        fetchChannels().catch(() => [])
      ]);
      setJobs(jobsData);
      setChannels(channelsData);
      if (channelsData.length > 0 && selectedChannelId === undefined) {
        setSelectedChannelId(channelsData[0].id);
        if (channelsData[0].profile?.visual_mode) {
          setSelectedVisualMode(channelsData[0].profile.visual_mode);
        }
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const timer = setInterval(loadData, 4000);
    return () => clearInterval(timer);
  }, [selectedChannelId]);

  const handleRun = async (type: 'DAILY_WORKFLOW' | 'SHORT' | 'LONG') => {
    try {
      setRunningType(type);
      await triggerWorkflow(type, selectedVisualMode, selectedChannelId);
      await loadData();
    } catch (e) {
      console.error(e);
    } finally {
      setRunningType(null);
    }
  };

  const handleRetry = async (jobId: string) => {
    try {
      setRetryingJobId(jobId);
      await retryJob(jobId);
      await loadData();
    } catch (e) {
      console.error(e);
    } finally {
      setRetryingJobId(null);
    }
  };

  const activeAgents = selectedVisualMode === 'FULL_ANIMATION' ? fullAnimationAgentsList : imageMotionAgentsList;

  return (
    <AuthGuard>
    <div className="space-y-8 animate-in fade-in duration-300 pb-12 max-w-7xl mx-auto px-4">
      {/* Header & Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-xl bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <Clapperboard className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-black text-white tracking-tight">AI Video Generation Studio</h1>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Autonomous multi-agent pipeline with real-time stage checkpoints and dual engine selection.
          </p>
        </div>

        {/* Studio Selectors */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Channel Selector */}
          {channels.length > 0 && (
            <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 px-3 py-1.5 rounded-xl text-xs">
              <Tv className="w-3.5 h-3.5 text-slate-400" />
              <select
                value={selectedChannelId}
                onChange={(e) => setSelectedChannelId(Number(e.target.value))}
                className="bg-transparent text-white font-medium focus:outline-none cursor-pointer"
              >
                {channels.map((ch) => (
                  <option key={ch.id} value={ch.id} className="bg-slate-900 text-white">
                    {ch.channel_name}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Visual Mode Selector */}
          <div className="flex items-center p-1 bg-slate-900 border border-slate-800 rounded-xl">
            <button
              onClick={() => setSelectedVisualMode('FULL_ANIMATION')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition ${
                selectedVisualMode === 'FULL_ANIMATION'
                  ? 'bg-purple-600 text-white shadow-md shadow-purple-600/20'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Zap className="w-3 h-3 text-amber-300" />
              FULL_ANIMATION
            </button>
            <button
              onClick={() => setSelectedVisualMode('IMAGE_MOTION')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition ${
                selectedVisualMode === 'IMAGE_MOTION'
                  ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              IMAGE_MOTION
            </button>
          </div>

          {/* Trigger Buttons */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => handleRun('SHORT')}
              disabled={runningType !== null}
              className="px-3 py-2 rounded-xl bg-purple-600/20 text-purple-300 border border-purple-500/30 text-xs font-bold hover:bg-purple-600/30 transition disabled:opacity-50"
            >
              Short (9:16)
            </button>
            <button
              onClick={() => handleRun('LONG')}
              disabled={runningType !== null}
              className="px-3 py-2 rounded-xl bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 text-xs font-bold hover:bg-indigo-600/30 transition disabled:opacity-50"
            >
              Story (16:9)
            </button>
            <button
              onClick={() => handleRun('DAILY_WORKFLOW')}
              disabled={runningType !== null}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white text-xs font-black hover:opacity-95 transition shadow-lg shadow-blue-600/20 flex items-center gap-2 disabled:opacity-50"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>{runningType === 'DAILY_WORKFLOW' ? 'Generating...' : 'Launch Workflow'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* Active Pipeline Architecture Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs">
        <div className="flex items-center gap-2">
          <span className="font-bold text-white">Active Engine Architecture:</span>
          <span className={`px-2 py-0.5 rounded font-black text-[11px] ${
            selectedVisualMode === 'FULL_ANIMATION' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' : 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
          }`}>
            {selectedVisualMode} ({activeAgents.length} Agents)
          </span>
          <span className="text-slate-400">
            {selectedVisualMode === 'FULL_ANIMATION' ? '• Temporal Motion Clips via Fal AI + Motion QA' : '• FLUX.1 + Pollinations Fallback + Ken Burns Motion'}
          </span>
        </div>
        <span className="text-emerald-400 font-medium">● Checkpoint Recovery Ready</span>
      </div>

      {/* Agents Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3.5">
        {activeAgents.map((agent) => (
          <div key={agent.id} className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800/80 space-y-2 relative overflow-hidden backdrop-blur-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-400 flex items-center justify-center font-black text-xs">
                  {agent.id}
                </div>
                <h3 className="font-bold text-xs text-white truncate max-w-[140px]">{agent.name}</h3>
              </div>
              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
                {agent.badge}
              </span>
            </div>
            <p className="text-[11px] text-slate-400 leading-relaxed pl-8">{agent.role}</p>
          </div>
        ))}
      </div>

      {/* Execution Jobs with Stage Checkpoints & Retry */}
      <div className="p-6 rounded-2xl bg-slate-900/90 border border-slate-800 space-y-4 shadow-xl">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <h2 className="text-sm font-bold text-white flex items-center gap-2">
            <Activity className="w-4 h-4 text-emerald-400" /> Pipeline Stage Execution History
          </h2>
          <span className="text-xs text-slate-500">Auto-refreshing live (4s)</span>
        </div>

        <div className="space-y-3">
          {jobs.length === 0 ? (
            <p className="text-xs text-slate-500 py-6 text-center">No video generation jobs triggered yet.</p>
          ) : (
            jobs.map((job) => {
              const isFailed = job.status?.includes('FAILED');
              const isRunning = job.status === 'RUNNING';

              return (
                <div 
                  key={job.id} 
                  className="p-4 rounded-xl bg-slate-950/70 border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                >
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-xs font-bold text-blue-400">{job.id}</span>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-slate-800 text-slate-300 border border-slate-700">
                        {job.visual_mode}
                      </span>
                      <span className="text-xs text-slate-300">({job.job_type})</span>
                    </div>

                    <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
                      <span>Checkpoint Stage:</span>
                      <code className="text-amber-300 font-bold px-1.5 py-0.5 rounded bg-amber-400/10">
                        {job.checkpoint_stage || job.current_step}
                      </code>
                      {job.error_message && (
                        <span className="text-red-400 text-[11px] block mt-1">{job.error_message}</span>
                      )}
                    </div>
                  </div>

                  <div className="flex sm:flex-col items-center sm:items-end justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider ${
                        job.status === 'COMPLETED' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' :
                        isRunning ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30 animate-pulse' :
                        'bg-red-500/20 text-red-400 border border-red-500/30'
                      }`}>
                        {job.status}
                      </span>

                      {/* Checkpoint Resume Button */}
                      {isFailed && (
                        <button
                          disabled={retryingJobId === job.id}
                          onClick={() => handleRetry(job.id)}
                          className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 text-[11px] font-bold transition"
                          title="Resume execution from checkpoint"
                        >
                          <RotateCcw className="w-3 h-3" />
                          {retryingJobId === job.id ? 'Resuming...' : 'Retry Checkpoint'}
                        </button>
                      )}
                    </div>

                    <div className="text-[11px] text-slate-400 font-mono">
                      {job.progress_percentage}% completed
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
    </AuthGuard>
  );
}
