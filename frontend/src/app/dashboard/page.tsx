'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { 
  fetchDashboardSummary, 
  fetchVideos, 
  triggerWorkflow, 
  fetchChannels, 
  fetchSubscriptionStatus 
} from '@/lib/api';
import { 
  DashboardSummary, 
  VideoRecord, 
  YouTubeChannelItem, 
  VisualMode, 
  SubscriptionStatus 
} from '@/lib/types';
import { 
  CheckCircle2, Clock, PlayCircle, Video as VideoIcon, Youtube, ArrowUpRight, 
  Zap, Play, Download, X, Film, Activity, AlertTriangle,
  Tv, ShieldAlert, RotateCcw, Crown, Search, FileText,
  Palette, Mic, RefreshCw, ChevronRight, Check, Sparkles
} from 'lucide-react';
import AuthGuard from '@/components/AuthGuard';

function getMediaUrl(path?: string, ytId?: string, isThumb = false): string {
  if (!path) {
    if (isThumb && ytId && !ytId.startsWith('yt_demo') && !ytId.startsWith('NO_UPLOAD') && !ytId.startsWith('LOCAL_TEST')) {
      return `https://i.ytimg.com/vi/${ytId}/hqdefault.jpg`;
    }
    return '';
  }
  if (path.startsWith('http://') || path.startsWith('https://')) return path;
  const clean = path.replace(/\\/g, '/').replace(/^\.?\/?storage\//, '/storage/');
  return clean.startsWith('/') ? clean : `/${clean}`;
}

export default function DashboardOverview() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [videos, setVideos] = useState<VideoRecord[]>([]);
  const [channels, setChannels] = useState<YouTubeChannelItem[]>([]);
  const [subscription, setSubscription] = useState<SubscriptionStatus | null>(null);
  const [selectedChannelId, setSelectedChannelId] = useState<number | undefined>(undefined);
  const [loading, setLoading] = useState(true);
  const [selectedVideo, setSelectedVideo] = useState<VideoRecord | null>(null);
  const [activeTab, setActiveTab] = useState<'ALL' | 'SHORT' | 'LONG'>('ALL');
  const [triggering, setTriggering] = useState<string | null>(null);
  const [actionNotice, setActionNotice] = useState<{ msg: string; type: 'success' | 'info' | 'error' } | null>(null);

  async function loadData() {
    try {
      const [sumData, vidData, chanData, subData] = await Promise.all([
        fetchDashboardSummary(selectedChannelId),
        fetchVideos(selectedChannelId),
        fetchChannels().catch(() => []),
        fetchSubscriptionStatus().catch(() => null)
      ]);
      setSummary(sumData);
      setVideos(vidData);
      setChannels(chanData);
      setSubscription(subData);
      if (chanData.length > 0 && selectedChannelId === undefined) {
        setSelectedChannelId(chanData[0].id);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 4000);
    return () => clearInterval(interval);
  }, [selectedChannelId]);

  const handleQuickRun = async (type: 'DAILY_WORKFLOW' | 'SHORT' | 'LONG') => {
    try {
      setTriggering(type);
      setActionNotice({ msg: `Initiating ${type}...`, type: 'info' });
      const activeChan = channels.find(c => c.id === selectedChannelId);
      const mode = (activeChan?.profile?.visual_mode || 'IMAGE_MOTION') as VisualMode;
      const res = await triggerWorkflow(type, mode, selectedChannelId);
      setActionNotice({ msg: `Mission Started: ${res.job_id || 'Queued'}`, type: 'success' });
      await loadData();
      setTimeout(() => setActionNotice(null), 4000);
    } catch (e: any) {
      console.error(e);
      setActionNotice({ msg: `Failed: ${e.message || 'Error'}`, type: 'error' });
      setTimeout(() => setActionNotice(null), 5000);
    } finally {
      setTriggering(null);
    }
  };

  const latestJob = summary?.latest_job;
  const currentStep = latestJob?.current_step || 'IDLE';
  const jobStatus = latestJob?.status || 'IDLE';
  
  const isJobRunning = Boolean(summary?.is_job_active || jobStatus === 'RUNNING');
  const isJobFailed = ['FAILED', 'DEAD_LETTER', 'ERROR'].includes(jobStatus);
  const isJobComplete = jobStatus === 'COMPLETED';
  const isEmergencyStop = summary?.global_emergency_stop ?? false;

  const currentChannel = channels.find(c => c.id === selectedChannelId) || channels[0];

  // Precision 6-Stage Workflow steps
  const missionSteps = [
    {
      num: '1',
      name: 'Topic & Idea',
      sub: 'Dupe Check',
      isActive: isJobRunning && ['RESEARCH', 'PLANNER'].includes(currentStep),
      isFailed: isJobFailed && ['RESEARCH', 'PLANNER'].includes(currentStep),
      completed: isJobComplete || (!isJobFailed && ['SCRIPT_WRITER', 'SCRIPT_QA', 'SCENE_DIRECTOR', 'ANIMATION_DIRECTOR', 'VISUAL_GEN', 'ANIMATION_GEN', 'ANIMATION_QA', 'VOICE_GEN', 'AUDIO_DIRECTOR', 'VIDEO_EDITOR', 'VIDEO_QA', 'METADATA_SEO', 'THUMBNAIL_GEN', 'YOUTUBE_UPLOAD', 'COMPLETED'].includes(currentStep)) || (isJobFailed && !['RESEARCH', 'PLANNER', 'IDLE'].includes(currentStep)),
    },
    {
      num: '2',
      name: 'Script & QA',
      sub: 'Devanagari >=85',
      isActive: isJobRunning && ['SCRIPT_WRITER', 'SCRIPT_QA'].includes(currentStep),
      isFailed: isJobFailed && ['SCRIPT_WRITER', 'SCRIPT_QA'].includes(currentStep),
      completed: isJobComplete || (!isJobFailed && ['SCENE_DIRECTOR', 'ANIMATION_DIRECTOR', 'VISUAL_GEN', 'ANIMATION_GEN', 'ANIMATION_QA', 'VOICE_GEN', 'AUDIO_DIRECTOR', 'VIDEO_EDITOR', 'VIDEO_QA', 'METADATA_SEO', 'THUMBNAIL_GEN', 'YOUTUBE_UPLOAD', 'COMPLETED'].includes(currentStep)) || (isJobFailed && ['ANIMATION_DIRECTOR', 'VISUAL_GEN', 'ANIMATION_GEN', 'VOICE_GEN', 'AUDIO_DIRECTOR', 'VIDEO_EDITOR', 'METADATA_SEO', 'YOUTUBE_UPLOAD'].includes(currentStep)),
    },
    {
      num: '3',
      name: 'Visuals & 3D',
      sub: 'Fal AI Luma',
      isActive: isJobRunning && ['ANIMATION_DIRECTOR', 'VISUAL_GEN', 'ANIMATION_GEN', 'ANIMATION_QA'].includes(currentStep),
      isFailed: isJobFailed && ['ANIMATION_DIRECTOR', 'VISUAL_GEN', 'ANIMATION_GEN', 'ANIMATION_QA'].includes(currentStep),
      completed: isJobComplete || (!isJobFailed && ['VOICE_GEN', 'AUDIO_DIRECTOR', 'VIDEO_EDITOR', 'VIDEO_QA', 'METADATA_SEO', 'THUMBNAIL_GEN', 'YOUTUBE_UPLOAD', 'COMPLETED'].includes(currentStep)),
    },
    {
      num: '4',
      name: 'Voice & SFX',
      sub: 'EdgeTTS Hindi',
      isActive: isJobRunning && ['VOICE_GEN', 'AUDIO_DIRECTOR'].includes(currentStep),
      isFailed: isJobFailed && ['VOICE_GEN', 'AUDIO_DIRECTOR'].includes(currentStep),
      completed: isJobComplete || (!isJobFailed && ['VIDEO_EDITOR', 'VIDEO_QA', 'METADATA_SEO', 'THUMBNAIL_GEN', 'YOUTUBE_UPLOAD', 'COMPLETED'].includes(currentStep)),
    },
    {
      num: '5',
      name: 'Assembly & QA',
      sub: 'FFmpeg 60fps',
      isActive: isJobRunning && ['VIDEO_EDITOR', 'VIDEO_QA'].includes(currentStep),
      isFailed: isJobFailed && ['VIDEO_EDITOR', 'VIDEO_QA'].includes(currentStep),
      completed: isJobComplete || (!isJobFailed && ['METADATA_SEO', 'THUMBNAIL_GEN', 'YOUTUBE_UPLOAD', 'COMPLETED'].includes(currentStep)),
    },
    {
      num: '6',
      name: 'YouTube Publish',
      sub: 'OAuth Sync',
      isActive: isJobRunning && ['METADATA_SEO', 'THUMBNAIL_GEN', 'YOUTUBE_UPLOAD'].includes(currentStep),
      isFailed: isJobFailed && ['METADATA_SEO', 'THUMBNAIL_GEN', 'YOUTUBE_UPLOAD'].includes(currentStep),
      completed: isJobComplete || currentStep === 'COMPLETED',
    },
  ];

  const filteredVideos = videos.filter((v) => activeTab === 'ALL' || v.video_type === activeTab);

  return (
    <AuthGuard>
    <div className="max-w-7xl mx-auto px-2 sm:px-4 py-4 space-y-6">
      {/* Toast Notice */}
      {actionNotice && (
        <div className="p-3.5 rounded-2xl bg-white border border-gray-200 shadow-lg flex items-center justify-between text-xs animate-in slide-in-from-top-2">
          <div className="flex items-center gap-2.5">
            {actionNotice.type === 'success' ? <CheckCircle2 className="w-4 h-4 text-emerald-600" /> :
             actionNotice.type === 'error' ? <AlertTriangle className="w-4 h-4 text-rose-600" /> :
             <RefreshCw className="w-4 h-4 text-gray-800 animate-spin" />}
            <span className="font-semibold text-gray-900">{actionNotice.msg}</span>
          </div>
          <button 
            onClick={() => setActionNotice(null)}
            className="text-gray-400 hover:text-gray-700 text-xs px-2"
          >
            ✕
          </button>
        </div>
      )}

      {/* Emergency Alert */}
      {isEmergencyStop && (
        <div className="p-4 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-2.5">
            <ShieldAlert className="w-4 h-4 text-rose-600 shrink-0" />
            <span className="font-medium">Global Emergency Stop is active. Autonomous pipeline generation is currently paused.</span>
          </div>
          <Link href="/emergency" className="font-bold underline text-rose-900 hover:text-rose-950">
            Manage Controls
          </Link>
        </div>
      )}

      {/* Polymer Ambient Backdrop Wrapper (Signature Polymer.co container) */}
      <div className="polymer-ambient-frame space-y-6">
        {/* Main Application Cockpit Panel */}
        <div className="bg-white rounded-3xl p-6 sm:p-8 shadow-sm border border-white/60 space-y-7">
          
          {/* Top Bar: Title & Quick Execution Actions */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-100 pb-6">
            <div>
              <div className="flex items-center gap-2.5 mb-1">
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold tracking-wide uppercase bg-pink-100/70 text-pink-800 border border-pink-200/60">
                  Autonomous Studio
                </span>
                <span className="flex items-center gap-1 text-xs font-semibold text-emerald-700">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  Live Operational
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight">
                AutoTube AI Command Studio
              </h1>
              <p className="text-xs sm:text-sm text-gray-500 mt-1">
                Full-lifecycle autonomous YouTube production &bull; Next scheduled trigger: <strong className="text-gray-800">Daily 09:00 AM IST</strong>
              </p>
            </div>

            {/* Quick Actions in Polymer Style */}
            <div className="flex flex-wrap items-center gap-2.5">
              {channels.length > 0 && (
                <div className="flex items-center gap-2 px-3 py-2 rounded-xl bg-gray-50 border border-gray-200 text-xs font-semibold text-gray-700">
                  <Tv className="w-3.5 h-3.5 text-gray-500" />
                  <select
                    value={selectedChannelId || ''}
                    onChange={(e) => setSelectedChannelId(Number(e.target.value))}
                    className="bg-transparent text-xs font-bold text-gray-900 focus:outline-none cursor-pointer"
                  >
                    {channels.map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.channel_name}
                      </option>
                    ))}
                  </select>
                </div>
              )}

              <button
                onClick={() => handleQuickRun('DAILY_WORKFLOW')}
                disabled={Boolean(triggering) || isJobRunning}
                className="flex items-center gap-2 px-4 py-2.5 btn-polymer-black text-xs font-bold transition-all disabled:opacity-50"
              >
                {triggering === 'DAILY_WORKFLOW' ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Play className="w-3.5 h-3.5 fill-current" />
                )}
                <span>Run Pipeline</span>
              </button>

              <button
                onClick={() => handleQuickRun('SHORT')}
                disabled={Boolean(triggering) || isJobRunning}
                className="px-3.5 py-2.5 rounded-xl bg-pink-50 hover:bg-pink-100/80 text-pink-900 border border-pink-200/80 text-xs font-bold transition disabled:opacity-50"
              >
                + Short (9:16)
              </button>
            </div>
          </div>

          {/* 6-Step Horizontal Pipeline Tracker (Polymer Application Timeline Style) */}
          <div className="p-5 rounded-2xl bg-gray-50/70 border border-gray-200/70 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-gray-900 uppercase tracking-wider">Workflow Pipeline</span>
                <span className="text-gray-300">&bull;</span>
                {isJobRunning ? (
                  <span className="px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-800 text-[11px] font-bold animate-pulse">
                    Live Generating ({latestJob?.progress ? `${Math.round(latestJob.progress)}%` : 'In Progress'})
                  </span>
                ) : isJobFailed ? (
                  <span className="px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 text-[11px] font-bold">
                    Standby &bull; Last run paused at Stage 3
                  </span>
                ) : isJobComplete ? (
                  <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[11px] font-bold">
                    ✓ Last Run Complete
                  </span>
                ) : (
                  <span className="px-2.5 py-0.5 rounded-full bg-gray-200 text-gray-700 text-[11px] font-medium">
                    Standby &bull; Ready
                  </span>
                )}
              </div>

              <div className="flex items-center gap-2 text-xs">
                <span className="text-gray-500 font-medium">Target Job:</span>
                <code className="font-mono px-2 py-0.5 rounded-md bg-white border border-gray-200 text-gray-800 font-semibold text-[11px]">
                  {latestJob?.id || 'IDLE_WAITING'}
                </code>
                {isJobFailed && (
                  <button
                    onClick={() => handleQuickRun('DAILY_WORKFLOW')}
                    disabled={Boolean(triggering)}
                    className="text-xs font-bold text-gray-700 hover:text-black px-2 py-0.5 rounded-md bg-white border border-gray-200 hover:bg-gray-100 transition ml-1"
                  >
                    Retry Run
                  </button>
                )}
              </div>
            </div>

            {/* Steps Timeline Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 pt-1">
              {missionSteps.map((step, idx) => (
                <div
                  key={idx}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    step.isActive
                      ? 'bg-blue-50 border-blue-300 text-blue-900 shadow-sm'
                      : step.isFailed
                      ? 'bg-amber-50/60 border-amber-200 text-amber-900'
                      : step.completed
                      ? 'bg-white border-emerald-200 text-gray-800 shadow-xs'
                      : 'bg-white/60 border-gray-200 text-gray-500'
                  }`}
                >
                  <div className="flex items-center justify-between text-[11px] font-bold mb-1">
                    <span className="text-gray-400">Step {step.num}</span>
                    {step.completed ? (
                      <span className="w-4 h-4 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-[10px] font-black">
                        ✓
                      </span>
                    ) : step.isActive ? (
                      <span className="w-2 h-2 rounded-full bg-blue-600 animate-ping" />
                    ) : (
                      <span className="w-3.5 h-3.5 rounded-full border border-gray-300 inline-block" />
                    )}
                  </div>
                  <h4 className="text-xs font-bold text-gray-900 truncate">{step.name}</h4>
                  <p className="text-[10px] text-gray-500 truncate">{step.sub}</p>
                  <div className="mt-2 text-[10px] font-bold">
                    {step.isActive ? (
                      <span className="text-blue-700">In Progress</span>
                    ) : step.isFailed ? (
                      <span className="text-amber-700">Stopped</span>
                    ) : step.completed ? (
                      <span className="text-emerald-700 font-medium">Completed</span>
                    ) : (
                      <span className="text-gray-400 font-normal">Pending</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* 4 Metric KPI Cards (Polymer Clean Style) */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 rounded-2xl bg-white border border-gray-200/80 shadow-xs space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-gray-500">Total Videos</span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700">
                  +100%
                </span>
              </div>
              <div className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight">
                {summary?.total_videos || 0}
              </div>
              <p className="text-[11px] text-gray-400 font-medium">Autonomous Generation</p>
            </div>

            <div className="p-4 rounded-2xl bg-white border border-gray-200/80 shadow-xs space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-gray-500">Daily Shorts</span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-purple-50 text-purple-700">
                  Viral 9:16
                </span>
              </div>
              <div className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight">
                {summary?.shorts_generated || 0}
              </div>
              <p className="text-[11px] text-gray-400 font-medium">Devanagari Scripted</p>
            </div>

            <div className="p-4 rounded-2xl bg-white border border-gray-200/80 shadow-xs space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-gray-500">Long Stories</span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-indigo-50 text-indigo-700">
                  16:9
                </span>
              </div>
              <div className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight">
                {summary?.long_videos_generated || 0}
              </div>
              <p className="text-[11px] text-gray-400 font-medium">Character Bible 3D</p>
            </div>

            <div className="p-4 rounded-2xl bg-white border border-gray-200/80 shadow-xs space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-gray-500">Channels Connected</span>
                <span className="px-1.5 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700">
                  Live
                </span>
              </div>
              <div className="text-2xl sm:text-3xl font-extrabold text-gray-900 tracking-tight">
                {summary?.total_connected_channels || channels.length || 1}
              </div>
              <p className="text-[11px] text-gray-400 font-medium">Isolated OAuth Storage</p>
            </div>
          </div>

          {/* Generated Video Projects Library */}
          <div className="space-y-4 pt-2 border-t border-gray-100">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-extrabold text-gray-900">Generated Video Projects</h3>
                <p className="text-xs text-gray-500">High-definition ready-to-publish MP4 assets</p>
              </div>

              <div className="flex items-center gap-1 p-1 rounded-xl bg-gray-100">
                {(['ALL', 'SHORT', 'LONG'] as const).map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-3 py-1 rounded-lg text-xs font-bold transition ${
                      activeTab === tab
                        ? 'bg-white text-gray-900 shadow-xs'
                        : 'text-gray-500 hover:text-gray-900'
                    }`}
                  >
                    {tab === 'ALL' ? 'All Formats' : tab === 'SHORT' ? 'Shorts' : 'Long Stories'}
                  </button>
                ))}
              </div>
            </div>

            {filteredVideos.length === 0 ? (
              <div className="py-12 text-center rounded-2xl bg-gray-50 border border-gray-200/60 text-xs text-gray-500 space-y-2">
                <Film className="w-8 h-8 text-gray-400 mx-auto" />
                <p className="font-semibold text-gray-700">No videos found for this filter</p>
                <p>Click &quot;Run Pipeline&quot; to trigger autonomous generation.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredVideos.slice(0, 6).map((v) => (
                  <div
                    key={v.id}
                    className="group rounded-2xl bg-white border border-gray-200/90 overflow-hidden shadow-xs hover:shadow-md transition-all duration-200 flex flex-col justify-between"
                  >
                    <div>
                      {/* Video Thumbnail Box */}
                      <div 
                        onClick={() => setSelectedVideo(v)}
                        className="relative aspect-video bg-gray-900 cursor-pointer overflow-hidden group"
                      >
                        {getMediaUrl(v.thumbnail_path, v.youtube_video_id, true) ? (
                          <img 
                            src={getMediaUrl(v.thumbnail_path, v.youtube_video_id, true)} 
                            alt={v.title} 
                            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105" 
                          />
                        ) : (
                          <div className="w-full h-full flex flex-col items-center justify-center text-gray-400 bg-gray-800">
                            <Film className="w-6 h-6 mb-1" />
                            <span className="text-[10px]">Preview Available</span>
                          </div>
                        )}

                        <span className="absolute top-2.5 left-2.5 px-2 py-0.5 rounded-md text-[10px] font-black uppercase tracking-wider bg-black/80 text-white backdrop-blur-sm shadow-xs">
                          {v.video_type}
                        </span>

                        <span className="absolute top-2.5 right-2.5 px-2 py-0.5 rounded-md text-[10px] font-bold bg-white/90 text-gray-900 backdrop-blur-sm shadow-xs">
                          {v.visual_mode || 'IMAGE_MOTION'}
                        </span>

                        <div className="absolute inset-0 bg-black/30 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                          <div className="w-10 h-10 rounded-full bg-white text-black flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
                            <Play className="w-4 h-4 fill-current ml-0.5" />
                          </div>
                        </div>
                      </div>

                      {/* Video Info */}
                      <div className="p-4 space-y-2">
                        <h4 className="font-bold text-xs text-gray-900 line-clamp-1 group-hover:text-pink-600 transition">
                          {v.title}
                        </h4>
                        <div className="flex items-center justify-between text-[11px] text-gray-500">
                          <span>Status: <strong className="text-emerald-700 font-semibold">{v.status}</strong></span>
                          <span>Mode: <strong className="text-amber-700 font-semibold">{v.publish_mode}</strong></span>
                        </div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="p-4 pt-0 flex items-center gap-2">
                      <button
                        onClick={() => setSelectedVideo(v)}
                        className="flex-1 py-1.5 rounded-xl bg-gray-100 hover:bg-gray-200 text-gray-900 text-xs font-bold transition flex items-center justify-center gap-1.5"
                      >
                        <PlayCircle className="w-3.5 h-3.5" /> Play Video
                      </button>

                      {v.youtube_url && (
                        <a
                          href={v.youtube_url}
                          target="_blank"
                          rel="noreferrer"
                          className="p-1.5 rounded-xl bg-red-50 hover:bg-red-100 text-red-600 border border-red-200 transition"
                          title="Watch on YouTube"
                        >
                          <Youtube className="w-4 h-4" />
                        </a>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Video Modal Player */}
      {selectedVideo && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-in fade-in">
          <div className="bg-white border border-gray-200 rounded-3xl max-w-3xl w-full p-4 sm:p-6 space-y-4 shadow-2xl relative max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between border-b border-gray-100 pb-3">
              <div>
                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-pink-100 text-pink-800">
                  {selectedVideo.video_type}
                </span>
                <h3 className="font-bold text-base text-gray-900 mt-1 line-clamp-1">{selectedVideo.title}</h3>
              </div>
              <button
                onClick={() => setSelectedVideo(null)}
                className="w-8 h-8 rounded-full bg-gray-100 hover:bg-gray-200 text-gray-600 hover:text-black flex items-center justify-center transition"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="aspect-video bg-black rounded-2xl overflow-hidden shadow-inner">
              <video
                src={getMediaUrl(selectedVideo.video_path)}
                controls
                autoPlay
                className="w-full h-full object-contain"
              />
            </div>

            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pt-1">
              <span className="text-xs text-gray-500 font-medium">Created: {selectedVideo.created_at}</span>
              <div className="flex items-center gap-2">
                {selectedVideo.video_path && (
                  <a
                    href={getMediaUrl(selectedVideo.video_path)}
                    download
                    className="px-4 py-2 rounded-xl btn-polymer-black text-xs font-bold flex items-center gap-1.5 shadow-sm"
                  >
                    <Download className="w-3.5 h-3.5" /> Download MP4
                  </a>
                )}
                {selectedVideo.youtube_url && (
                  <a
                    href={selectedVideo.youtube_url}
                    target="_blank"
                    rel="noreferrer"
                    className="px-4 py-2 rounded-xl bg-red-50 text-red-600 border border-red-200 hover:bg-red-100 text-xs font-bold flex items-center gap-1.5 transition"
                  >
                    <Youtube className="w-3.5 h-3.5" /> YouTube
                  </a>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
    </AuthGuard>
  );
}
