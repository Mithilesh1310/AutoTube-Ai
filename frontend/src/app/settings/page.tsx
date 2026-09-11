'use client';

import { useEffect, useState } from 'react';
import { fetchSettings, updateSettings, fetchYouTubeAuthUrl, fetchYouTubeChannel, disconnectYouTubeChannel } from '@/lib/api';
import {
  Settings as SettingsIcon,
  Key,
  ShieldAlert,
  Save,
  Youtube,
  Sparkles,
  CheckCircle2,
  Lock,
  ShieldCheck,
  Globe,
  EyeOff,
  Radio,
  ExternalLink,
  Check,
  Zap,
  Info,
  AlertTriangle
} from 'lucide-react';

export default function SettingsPage() {
  const [form, setForm] = useState<Record<string, string>>({
    GEMINI_API_KEY: '',
    AGENT_ENABLED: 'true',
    PUBLISH_MODE: 'PUBLIC',
    YOUTUBE_PUBLISH_MODE: 'PUBLIC',
    VOICE_PROVIDER: 'edge_tts',
    IMAGE_PROVIDER: 'pollinations',
    VISUAL_PROVIDER: 'image_kenburns',
    YOUTUBE_CLIENT_ID: '',
    YOUTUBE_CLIENT_SECRET: '',
    YOUTUBE_REFRESH_TOKEN: '',
    WORKFLOW_GENERATE_TIME: '08:00',
    SHORTS_PUBLISH_TIME: '10:00',
    LONG_PUBLISH_TIME: '18:00',
  });
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
  const [authUrl, setAuthUrl] = useState<string | null>(null);
  const [channel, setChannel] = useState<{ connected: boolean; channel_name?: string; channel_id?: string } | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchSettings();
        setForm((prev) => {
          const merged = { ...prev, ...data };
          // Harmonize publish mode keys
          const currentMode = merged.YOUTUBE_PUBLISH_MODE || merged.PUBLISH_MODE || 'PUBLIC';
          merged.YOUTUBE_PUBLISH_MODE = currentMode;
          merged.PUBLISH_MODE = currentMode;
          return merged;
        });

        try {
          const authData = await fetchYouTubeAuthUrl();
          if (authData && authData.auth_url) setAuthUrl(authData.auth_url);
        } catch (err) {
          console.warn('Could not fetch YouTube auth url:', err);
        }

        try {
          const chanData = await fetchYouTubeChannel();
          if (chanData) setChannel(chanData);
        } catch (err) {
          console.warn('Could not fetch YouTube channel:', err);
        }

        if (typeof window !== 'undefined' && window.location.search.includes('youtube_connected=true')) {
          setMsg({
            type: 'success',
            text: '🎉 YouTube Channel connected successfully! Daily uploads are now active.'
          });
        }
      } catch (e) {
        console.error(e);
      }
    }
    load();
  }, []);

  const handleChange = (k: string, v: string) => {
    setForm((prev) => {
      const updated = { ...prev, [k]: v };
      if (k === 'PUBLISH_MODE') updated.YOUTUBE_PUBLISH_MODE = v;
      if (k === 'YOUTUBE_PUBLISH_MODE') updated.PUBLISH_MODE = v;
      return updated;
    });
  };

  const handleSetPublishMode = (mode: 'PUBLIC' | 'UNLISTED' | 'PRIVATE') => {
    handleChange('PUBLISH_MODE', mode);
    handleChange('YOUTUBE_PUBLISH_MODE', mode);
  };

  const handleSave = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    try {
      setSaving(true);
      await updateSettings(form);
      const activeMode = form.YOUTUBE_PUBLISH_MODE || form.PUBLISH_MODE || 'PUBLIC';
      setMsg({
        type: 'success',
        text: `✅ Configuration saved! YouTube Publish Mode is now set to "${activeMode}".`
      });
      setTimeout(() => setMsg(null), 5000);
    } catch (e: any) {
      setMsg({
        type: 'error',
        text: `❌ Error saving settings: ${e.message}`
      });
    } finally {
      setSaving(false);
    }
  };

  const handleDisconnectChannel = async () => {
    if (!confirm('Are you sure you want to disconnect this YouTube channel? You can reconnect anytime.')) return;
    try {
      await disconnectYouTubeChannel();
      setChannel({ connected: false });
      setMsg({
        type: 'success',
        text: '🔌 Channel disconnected. You can now connect a new YouTube Channel.'
      });
    } catch (err: any) {
      setMsg({
        type: 'error',
        text: `Failed to disconnect channel: ${err.message}`
      });
    }
  };

  const activePublishMode = (form.YOUTUBE_PUBLISH_MODE || form.PUBLISH_MODE || 'PUBLIC').toUpperCase();

  return (
    <form onSubmit={handleSave} className="space-y-8 max-w-4xl mx-auto animate-in fade-in duration-300 pb-16">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-5">
        <div>
          <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight flex items-center gap-2.5">
            <span className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-100/80 shadow-sm">
              <SettingsIcon className="w-5 h-5" />
            </span>
            Channel Settings & API Credentials
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Configure YouTube automated publishing privacy, AI keys, and pipeline safety controls.
          </p>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="px-6 py-2.5 rounded-full bg-slate-900 hover:bg-black text-white text-xs font-extrabold shadow-md shadow-slate-900/10 hover:shadow-lg transition-all flex items-center justify-center gap-2 disabled:opacity-50"
        >
          {saving ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Saving Changes...
            </>
          ) : (
            <>
              <Save className="w-4 h-4 text-blue-400" /> Save Configuration
            </>
          )}
        </button>
      </div>

      {/* Status Feedback Toast */}
      {msg && (
        <div
          className={`p-4 rounded-2xl text-xs font-bold flex items-center justify-between gap-3 shadow-sm animate-in fade-in ${
            msg.type === 'success'
              ? 'bg-emerald-50/90 border border-emerald-200 text-emerald-800'
              : 'bg-red-50/90 border border-red-200 text-red-800'
          }`}
        >
          <span>{msg.text}</span>
          <button
            type="button"
            onClick={() => setMsg(null)}
            className="text-xs opacity-60 hover:opacity-100"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Production Truth Status Bar */}
      <div className="p-5 rounded-3xl bg-white border border-slate-200/80 shadow-[0_2px_16px_rgba(0,0,0,0.03)] space-y-3.5">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-extrabold text-slate-800 flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-600" /> Production Truth Architecture Status
          </h3>
          <span className="text-[11px] font-medium text-slate-400">Click Publish Mode card below to switch</span>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          {/* Card 1: Implemented */}
          <div className="p-3.5 rounded-2xl bg-slate-50/80 border border-slate-100">
            <div className="font-extrabold text-slate-800">14-Agent Graph</div>
            <div className="flex items-center gap-1.5 mt-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <p className="text-[11px] text-slate-500 font-medium">Ready & Active</p>
            </div>
          </div>

          {/* Card 2: Interactive Publish Mode Card */}
          <div
            onClick={() => handleSetPublishMode(activePublishMode === 'PUBLIC' ? 'UNLISTED' : 'PUBLIC')}
            className={`p-3.5 rounded-2xl border transition-all cursor-pointer select-none ${
              activePublishMode === 'PUBLIC'
                ? 'bg-emerald-50/60 border-emerald-300 shadow-sm shadow-emerald-500/10'
                : activePublishMode === 'UNLISTED'
                ? 'bg-amber-50/60 border-amber-300 shadow-sm shadow-amber-500/10'
                : 'bg-purple-50/60 border-purple-300 shadow-sm shadow-purple-500/10'
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-extrabold text-slate-500 tracking-wider">PUBLISH MODE</span>
              <span className="text-[9px] font-extrabold uppercase px-1.5 py-0.5 rounded bg-white/80 text-slate-600 border border-slate-200">
                Click to switch
              </span>
            </div>
            <div className="flex items-center gap-1.5 mt-1">
              <span
                className={`w-2.5 h-2.5 rounded-full ${
                  activePublishMode === 'PUBLIC'
                    ? 'bg-emerald-500 shadow-[0_0_8px_#10B981]'
                    : activePublishMode === 'UNLISTED'
                    ? 'bg-amber-500'
                    : 'bg-purple-500'
                }`}
              />
              <span
                className={`font-black text-xs ${
                  activePublishMode === 'PUBLIC'
                    ? 'text-emerald-700'
                    : activePublishMode === 'UNLISTED'
                    ? 'text-amber-700'
                    : 'text-purple-700'
                }`}
              >
                {activePublishMode} (AUTO)
              </span>
            </div>
          </div>

          {/* Card 3: Gemini Intelligence */}
          <div className="p-3.5 rounded-2xl bg-slate-50/80 border border-slate-100">
            <div className="font-extrabold text-slate-800">GEMINI LIVE</div>
            <div className="flex items-center gap-1.5 mt-1">
              <span className="w-2 h-2 rounded-full bg-blue-500" />
              <p className="text-[11px] text-blue-600 font-medium">Flash Lite Active</p>
            </div>
          </div>

          {/* Card 4: Hard Gates */}
          <div className="p-3.5 rounded-2xl bg-slate-50/80 border border-slate-100">
            <div className="font-extrabold text-slate-800">QA GATES</div>
            <div className="flex items-center gap-1.5 mt-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500" />
              <p className="text-[11px] text-emerald-600 font-medium">Strict Enforced</p>
            </div>
          </div>
        </div>
      </div>

      {/* DEDICATED YOUTUBE PUBLISH MODE CONTROLLER */}
      <div className="p-6 rounded-3xl bg-white border border-slate-200/80 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.05)] space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
          <div>
            <h2 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
              <Globe className="w-5 h-5 text-indigo-600" />
              YouTube Publish & Privacy Mode
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Choose how newly created videos should be published to your YouTube Channel.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-[11px] text-slate-400 font-medium">Current setting:</span>
            <span
              className={`px-3 py-1 rounded-full text-xs font-black uppercase border ${
                activePublishMode === 'PUBLIC'
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : activePublishMode === 'UNLISTED'
                  ? 'bg-amber-50 text-amber-700 border-amber-200'
                  : 'bg-purple-50 text-purple-700 border-purple-200'
              }`}
            >
              {activePublishMode}
            </span>
          </div>
        </div>

        {/* 3 Selectable Privacy Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Option 1: PUBLIC */}
          <div
            onClick={() => handleSetPublishMode('PUBLIC')}
            className={`relative p-5 rounded-2xl border-2 transition-all cursor-pointer text-left flex flex-col justify-between group ${
              activePublishMode === 'PUBLIC'
                ? 'border-emerald-500 bg-emerald-50/30 shadow-md shadow-emerald-500/10'
                : 'border-slate-200 hover:border-slate-300 bg-white'
            }`}
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${activePublishMode === 'PUBLIC' ? 'bg-emerald-500 text-white' : 'bg-slate-100 text-slate-600'}`}>
                  <Globe className="w-5 h-5" />
                </div>
                {activePublishMode === 'PUBLIC' ? (
                  <span className="w-6 h-6 rounded-full bg-emerald-500 text-white flex items-center justify-center">
                    <Check className="w-3.5 h-3.5 stroke-[3]" />
                  </span>
                ) : (
                  <span className="w-5 h-5 rounded-full border-2 border-slate-300" />
                )}
              </div>

              <div className="inline-block px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800 text-[10px] font-extrabold uppercase mb-2">
                Recommended for Growth
              </div>

              <h3 className="font-extrabold text-sm text-slate-900">PUBLIC</h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                Videos upload <strong>directly live</strong> to YouTube search, subscriber notifications, and recommendations without manual approval.
              </p>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] font-bold text-emerald-700 flex items-center gap-1.5">
              <Zap className="w-3.5 h-3.5" /> 100% Fully Autonomous
            </div>
          </div>

          {/* Option 2: UNLISTED */}
          <div
            onClick={() => handleSetPublishMode('UNLISTED')}
            className={`relative p-5 rounded-2xl border-2 transition-all cursor-pointer text-left flex flex-col justify-between group ${
              activePublishMode === 'UNLISTED'
                ? 'border-amber-500 bg-amber-50/30 shadow-md shadow-amber-500/10'
                : 'border-slate-200 hover:border-slate-300 bg-white'
            }`}
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${activePublishMode === 'UNLISTED' ? 'bg-amber-500 text-white' : 'bg-slate-100 text-slate-600'}`}>
                  <EyeOff className="w-5 h-5" />
                </div>
                {activePublishMode === 'UNLISTED' ? (
                  <span className="w-6 h-6 rounded-full bg-amber-500 text-white flex items-center justify-center">
                    <Check className="w-3.5 h-3.5 stroke-[3]" />
                  </span>
                ) : (
                  <span className="w-5 h-5 rounded-full border-2 border-slate-300" />
                )}
              </div>

              <div className="inline-block px-2 py-0.5 rounded-md bg-amber-100 text-amber-800 text-[10px] font-extrabold uppercase mb-2">
                Safe Review Mode
              </div>

              <h3 className="font-extrabold text-sm text-slate-900">UNLISTED</h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                Uploaded to your channel, but <strong>only people with the link</strong> can watch. Not visible in YouTube search or feeds.
              </p>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] font-bold text-amber-700 flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5" /> Link-Only Visibility
            </div>
          </div>

          {/* Option 3: PRIVATE */}
          <div
            onClick={() => handleSetPublishMode('PRIVATE')}
            className={`relative p-5 rounded-2xl border-2 transition-all cursor-pointer text-left flex flex-col justify-between group ${
              activePublishMode === 'PRIVATE'
                ? 'border-purple-500 bg-purple-50/30 shadow-md shadow-purple-500/10'
                : 'border-slate-200 hover:border-slate-300 bg-white'
            }`}
          >
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${activePublishMode === 'PRIVATE' ? 'bg-purple-500 text-white' : 'bg-slate-100 text-slate-600'}`}>
                  <Lock className="w-5 h-5" />
                </div>
                {activePublishMode === 'PRIVATE' ? (
                  <span className="w-6 h-6 rounded-full bg-purple-500 text-white flex items-center justify-center">
                    <Check className="w-3.5 h-3.5 stroke-[3]" />
                  </span>
                ) : (
                  <span className="w-5 h-5 rounded-full border-2 border-slate-300" />
                )}
              </div>

              <div className="inline-block px-2 py-0.5 rounded-md bg-purple-100 text-purple-800 text-[10px] font-extrabold uppercase mb-2">
                Draft / Hidden
              </div>

              <h3 className="font-extrabold text-sm text-slate-900">PRIVATE</h3>
              <p className="text-xs text-slate-500 mt-1 leading-relaxed">
                Strictly hidden from all viewers. Only the signed-in YouTube channel account can see and edit the video in YouTube Studio.
              </p>
            </div>

            <div className="mt-4 pt-3 border-t border-slate-100 text-[11px] font-bold text-purple-700 flex items-center gap-1.5">
              <Lock className="w-3.5 h-3.5" /> Channel Owner Only
            </div>
          </div>
        </div>

        {/* Quick action bar inside publish mode */}
        <div className="p-4 rounded-2xl bg-indigo-50/60 border border-indigo-100/80 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2.5 text-xs text-slate-700 font-medium">
            <Info className="w-4 h-4 text-indigo-600 shrink-0" />
            <span>
              Selected mode: <strong className="text-slate-900 uppercase font-extrabold">{activePublishMode}</strong>. Click "Save Configuration" to persist across all autonomous runs.
            </span>
          </div>

          <button
            type="button"
            disabled={saving}
            onClick={() => handleSave()}
            className="px-5 py-2 rounded-full bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-extrabold shadow-sm hover:shadow transition-all shrink-0"
          >
            {saving ? 'Saving...' : 'Apply & Save Publish Mode'}
          </button>
        </div>
      </div>

      {/* Global Emergency Kill-Switch */}
      <div className="p-6 rounded-3xl bg-amber-50/70 border border-amber-200/80 space-y-4 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-700 flex items-center justify-center shrink-0 border border-amber-200">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-extrabold text-sm text-slate-900">Global Emergency Kill-Switch (AGENT_ENABLED)</h3>
              <p className="text-xs text-slate-600 mt-1 max-w-xl leading-relaxed">
                When set to OFF, autonomous daily workflow scheduling is suspended and video publishing is completely blocked.
              </p>
            </div>
          </div>

          <select
            value={form.AGENT_ENABLED}
            onChange={(e) => handleChange('AGENT_ENABLED', e.target.value)}
            className="px-4 py-2.5 rounded-xl bg-white border border-amber-300 text-xs font-extrabold text-slate-900 shadow-sm focus:outline-none focus:ring-2 focus:ring-amber-400 cursor-pointer shrink-0"
          >
            <option value="true">🟢 ENABLED (ON) — Autonomous Production Active</option>
            <option value="false">🔴 DISABLED (OFF) — Block All Uploads</option>
          </select>
        </div>
      </div>

      {/* Gemini API Key */}
      <div className="p-6 rounded-3xl bg-white border border-slate-200/80 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.05)] space-y-4">
        <h3 className="font-extrabold text-sm text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-3">
          <Key className="w-4 h-4 text-blue-600" /> AI Intelligence Provider (Google Gemini API)
        </h3>
        <div className="space-y-2">
          <label className="block text-xs font-bold text-slate-700">GEMINI_API_KEY</label>
          <input
            type="password"
            value={form.GEMINI_API_KEY}
            onChange={(e) => handleChange('GEMINI_API_KEY', e.target.value)}
            placeholder="AIzaSy..."
            className="w-full px-4 py-2.5 rounded-xl bg-slate-50/80 border border-slate-200 text-xs text-slate-900 font-mono placeholder-slate-400 focus:outline-none focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 transition-all"
          />
          <p className="text-[11px] text-slate-500">
            Active high-speed model: <code className="text-indigo-600 font-mono font-bold bg-indigo-50 px-1.5 py-0.5 rounded">gemini-flash-lite-latest</code> / fallback <code className="text-indigo-600 font-mono font-bold bg-indigo-50 px-1.5 py-0.5 rounded">gemini-flash-latest</code>
          </p>
        </div>
      </div>

      {/* YouTube OAuth Connection */}
      <div className="p-6 rounded-3xl bg-white border border-slate-200/80 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.05)] space-y-5">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-3">
          <div>
            <h3 className="font-extrabold text-sm text-slate-900 flex items-center gap-2">
              <Youtube className="w-4 h-4 text-red-600" /> YouTube Data API v3 & OAuth Connection
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">Manage channel authorization and Google API credentials.</p>
          </div>

          {channel?.connected ? (
            <div className="flex items-center gap-2">
              <span className="px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-extrabold flex items-center gap-1.5 shadow-sm">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" /> Channel Connected
              </span>
              {authUrl && (
                <a
                  href={authUrl}
                  className="px-3 py-1 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold transition-all"
                >
                  Reconnect
                </a>
              )}
              <button
                type="button"
                onClick={handleDisconnectChannel}
                className="px-3 py-1 rounded-full bg-rose-50 hover:bg-rose-100 text-rose-600 border border-rose-200 text-xs font-semibold transition-all"
              >
                Disconnect
              </button>
            </div>
          ) : authUrl ? (
            <a
              href={authUrl}
              className="px-4 py-2 rounded-full bg-red-600 hover:bg-red-700 text-white text-xs font-extrabold shadow-md shadow-red-600/20 transition-all flex items-center justify-center gap-2"
            >
              <Lock className="w-3.5 h-3.5" /> Connect Google Account
            </a>
          ) : null}
        </div>

        {channel?.connected ? (
          <div className="p-4 rounded-2xl bg-emerald-50/80 border border-emerald-200/80 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 animate-in fade-in">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-red-600 text-white flex items-center justify-center shadow-sm shrink-0">
                <Youtube className="w-5 h-5" />
              </div>
              <div>
                <p className="text-sm font-black text-slate-900">{channel.channel_name}</p>
                <p className="text-[11px] text-slate-500 font-mono">Channel ID: {channel.channel_id}</p>
              </div>
            </div>
            <div className="text-right">
              <span className="px-3 py-1 rounded-full text-[10px] font-black tracking-wider bg-emerald-600 text-white shadow-sm">
                READY FOR DAILY UPLOAD
              </span>
            </div>
          </div>
        ) : (
          <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200/80 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 animate-in fade-in">
            <div className="flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <p className="text-xs font-bold text-amber-900">YouTube Channel Not Authorized</p>
                <p className="text-[11px] text-amber-700 mt-0.5 max-w-xl">
                  AutoTube cannot upload to your YouTube channel until you grant permission. Click <strong>Connect Google Account</strong> or enter an offline <strong>YOUTUBE_REFRESH_TOKEN</strong> below.
                </p>
              </div>
            </div>
            {authUrl && (
              <a
                href={authUrl}
                className="px-4 py-2 rounded-xl bg-red-600 hover:bg-red-700 text-white text-xs font-extrabold shadow-sm transition-all shrink-0 flex items-center gap-1.5"
              >
                <Youtube className="w-4 h-4" /> Connect Now
              </a>
            )}
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <label className="block text-xs font-bold text-slate-700">YOUTUBE_CLIENT_ID</label>
            <input
              type="text"
              value={form.YOUTUBE_CLIENT_ID}
              onChange={(e) => handleChange('YOUTUBE_CLIENT_ID', e.target.value)}
              placeholder="123456789-xyz.apps.googleusercontent.com"
              className="w-full px-4 py-2.5 rounded-xl bg-slate-50/80 border border-slate-200 text-xs text-slate-900 font-mono placeholder-slate-400 focus:outline-none focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 transition-all"
            />
          </div>
          <div className="space-y-2">
            <label className="block text-xs font-bold text-slate-700">YOUTUBE_CLIENT_SECRET</label>
            <input
              type="password"
              value={form.YOUTUBE_CLIENT_SECRET}
              onChange={(e) => handleChange('YOUTUBE_CLIENT_SECRET', e.target.value)}
              placeholder="GOCSPX-..."
              className="w-full px-4 py-2.5 rounded-xl bg-slate-50/80 border border-slate-200 text-xs text-slate-900 font-mono placeholder-slate-400 focus:outline-none focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 transition-all"
            />
          </div>
          <div className="space-y-2 md:col-span-2">
            <div className="flex items-center justify-between">
              <label className="block text-xs font-bold text-slate-700">YOUTUBE_REFRESH_TOKEN (Direct Token Override)</label>
              <span className="text-[10px] text-slate-400 font-medium">Optional for offline/headless server setup</span>
            </div>
            <input
              type="password"
              value={form.YOUTUBE_REFRESH_TOKEN || ''}
              onChange={(e) => handleChange('YOUTUBE_REFRESH_TOKEN', e.target.value)}
              placeholder="1//04..."
              className="w-full px-4 py-2.5 rounded-xl bg-slate-50/80 border border-slate-200 text-xs text-slate-900 font-mono placeholder-slate-400 focus:outline-none focus:bg-white focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100 transition-all"
            />
            <p className="text-[11px] text-slate-500">
              Entering a valid Google OAuth refresh token here directly authorizes AutoTube to upload videos to your YouTube channel without requiring browser redirect callbacks.
            </p>
          </div>
        </div>
      </div>

      {/* Floating Bottom Action Bar */}
      <div className="sticky bottom-6 p-4 rounded-2xl bg-white/90 backdrop-blur-md border border-slate-200 shadow-xl flex items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-xs font-bold text-slate-600">
          <span>Active Mode:</span>
          <span className="px-2.5 py-0.5 rounded-full bg-slate-900 text-white text-[11px] font-black uppercase">
            {activePublishMode}
          </span>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="px-6 py-2.5 rounded-full bg-blue-600 hover:bg-blue-700 text-white text-xs font-extrabold shadow-md shadow-blue-600/20 hover:shadow-lg transition-all flex items-center gap-2 disabled:opacity-50"
        >
          {saving ? (
            <>
              <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Saving...
            </>
          ) : (
            <>
              <Save className="w-4 h-4" /> Save Configuration
            </>
          )}
        </button>
      </div>
    </form>
  );
}
