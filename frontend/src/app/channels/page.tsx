'use client';

import React, { useState, useEffect } from 'react';
import { 
  Tv, 
  Plus, 
  Play, 
  Pause, 
  Settings2, 
  Sparkles, 
  Clock, 
  Video, 
  CheckCircle2, 
  AlertCircle, 
  RefreshCw,
  Film,
  Zap,
  Globe,
  Trash2
} from 'lucide-react';
import { YouTubeChannelItem, VisualMode } from '@/lib/types';

export default function ChannelsPage() {
  const [channels, setChannels] = useState<YouTubeChannelItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [editingChannel, setEditingChannel] = useState<YouTubeChannelItem | null>(null);

  // Form state for adding/editing
  const [formName, setFormName] = useState('');
  const [formNiche, setFormNiche] = useState('Kids Cartoon Stories');
  const [formVisualMode, setFormVisualMode] = useState<VisualMode>('FULL_ANIMATION');
  const [formVideoFormat, setFormVideoFormat] = useState<'SHORT' | 'LONG' | 'BOTH'>('BOTH');
  const [formVideosPerDay, setFormVideosPerDay] = useState(2);
  const [formPublishTimes, setFormPublishTimes] = useState('10:00, 18:00');

  const fetchChannels = async () => {
    try {
      setLoading(true);
      const res = await fetch('http://localhost:8000/api/v1/channels');
      if (res.ok) {
        const data = await res.json();
        setChannels(data);
      }
    } catch (err) {
      console.error('Failed to load channels:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchChannels();
  }, []);

  const handleToggleAutomation = async (channel: YouTubeChannelItem) => {
    const isCurrentlyEnabled = channel.profile?.automation_enabled ?? true;
    const endpoint = isCurrentlyEnabled ? 'pause' : 'resume';
    try {
      setActionLoading(channel.id);
      const res = await fetch(`http://localhost:8000/api/v1/channels/${channel.id}/${endpoint}`, {
        method: 'POST'
      });
      if (res.ok) {
        await fetchChannels();
      }
    } catch (err) {
      console.error(`Failed to ${endpoint} channel:`, err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleCreateChannel = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const times = formPublishTimes.split(',').map(t => t.trim()).filter(Boolean);
      const res = await fetch('http://localhost:8000/api/v1/channels', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          channel_name: formName,
          niche: formNiche,
          visual_mode: formVisualMode,
          video_format: formVideoFormat,
          videos_per_day: formVideosPerDay,
          publish_times: times
        })
      });
      if (res.ok) {
        setShowAddModal(false);
        setFormName('');
        await fetchChannels();
      }
    } catch (err) {
      console.error('Failed to create channel:', err);
    }
  };

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingChannel) return;
    try {
      const times = formPublishTimes.split(',').map(t => t.trim()).filter(Boolean);
      const res = await fetch(`http://localhost:8000/api/v1/channels/${editingChannel.id}/automation`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          niche: formNiche,
          visual_mode: formVisualMode,
          video_format: formVideoFormat,
          videos_per_day: formVideosPerDay,
          publish_times: times
        })
      });
      if (res.ok) {
        setEditingChannel(null);
        await fetchChannels();
      }
    } catch (err) {
      console.error('Failed to update automation:', err);
    }
  };

  const openEditModal = (ch: YouTubeChannelItem) => {
    setEditingChannel(ch);
    setFormNiche(ch.profile?.niche || 'Kids Cartoon Stories');
    setFormVisualMode(ch.profile?.visual_mode || 'FULL_ANIMATION');
    setFormVideoFormat(ch.profile?.video_format || 'BOTH');
    setFormVideosPerDay(ch.profile?.videos_per_day || 2);
    setFormPublishTimes((ch.profile?.publish_times || ['10:00', '18:00']).join(', '));
  };

  return (
    <div className="space-y-8 max-w-7xl mx-auto px-4 py-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800/80 pb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="p-2 rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <Tv className="w-5 h-5" />
            </span>
            <h1 className="text-2xl font-black text-white tracking-tight">Multi-Channel Studio</h1>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Manage autonomous publishing profiles, animation modes, and daily schedules per YouTube channel.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={fetchChannels}
            className="p-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            title="Refresh channels"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-blue-400' : ''}`} />
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-sm shadow-lg shadow-blue-600/20 transition"
          >
            <Plus className="w-4 h-4" /> Connect Channel
          </button>
        </div>
      </div>

      {/* Channel Cards Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2].map((i) => (
            <div key={i} className="h-64 rounded-2xl bg-slate-900/50 border border-slate-800 animate-pulse"></div>
          ))}
        </div>
      ) : channels.length === 0 ? (
        <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800/80">
          <Tv className="w-12 h-12 text-slate-600 mx-auto mb-3" />
          <h3 className="text-lg font-bold text-white">No Connected Channels</h3>
          <p className="text-sm text-slate-400 mt-1 mb-4">Connect your first YouTube channel to start autonomous AI video generation.</p>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 rounded-xl bg-blue-600 text-white text-sm font-semibold hover:bg-blue-500 transition"
          >
            Connect Channel Now
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {channels.map((ch) => {
            const isAuto = ch.profile?.automation_enabled ?? true;
            const mode = ch.profile?.visual_mode || 'FULL_ANIMATION';

            return (
              <div 
                key={ch.id}
                className="relative rounded-2xl bg-slate-900/80 border border-slate-800/80 p-6 shadow-xl backdrop-blur-xl hover:border-slate-700/80 transition-all duration-300"
              >
                {/* Top Status & Controls */}
                <div className="flex items-start justify-between gap-4 mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-purple-600 to-indigo-500 flex items-center justify-center text-white font-black text-lg shadow-lg">
                      {ch.channel_name ? ch.channel_name.charAt(0).toUpperCase() : 'C'}
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-white flex items-center gap-2">
                        {ch.channel_name}
                        {ch.is_connected && (
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                            Connected
                          </span>
                        )}
                      </h3>
                      <p className="text-xs text-slate-400 flex items-center gap-1 mt-0.5">
                        <Globe className="w-3 h-3 text-slate-500" />
                        {ch.youtube_channel_id || 'ID: Pending Auth'}
                      </p>
                    </div>
                  </div>

                  {/* Mode Badge */}
                  <div className="flex flex-col items-end gap-1.5">
                    <span className={`text-xs font-bold px-2.5 py-1 rounded-lg border flex items-center gap-1.5 ${
                      mode === 'FULL_ANIMATION'
                        ? 'bg-purple-500/10 text-purple-300 border-purple-500/30'
                        : mode === 'IMAGE_MOTION'
                        ? 'bg-blue-500/10 text-blue-300 border-blue-500/30'
                        : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30'
                    }`}>
                      <Zap className="w-3 h-3" />
                      {mode}
                    </span>
                    <span className="text-[11px] text-slate-400">
                      {ch.profile?.niche || 'Kids Cartoon Stories'}
                    </span>
                  </div>
                </div>

                {/* Details Grid */}
                <div className="grid grid-cols-3 gap-3 my-5 p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/60 text-xs">
                  <div>
                    <span className="text-slate-500 block mb-0.5">Format</span>
                    <span className="font-semibold text-slate-200">{ch.profile?.video_format || 'BOTH'}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block mb-0.5">Videos/Day</span>
                    <span className="font-semibold text-slate-200">{ch.profile?.videos_per_day || 2} Videos</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block mb-0.5">Schedule</span>
                    <span className="font-semibold text-slate-200">
                      {ch.profile?.publish_times?.join(', ') || '10:00, 18:00'}
                    </span>
                  </div>
                </div>

                {/* Footer Controls */}
                <div className="flex items-center justify-between pt-4 border-t border-slate-800/80">
                  <div className="flex items-center gap-2">
                    <button
                      disabled={actionLoading === ch.id}
                      onClick={() => handleToggleAutomation(ch)}
                      className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold border transition ${
                        isAuto
                          ? 'bg-amber-500/10 text-amber-300 border-amber-500/30 hover:bg-amber-500/20'
                          : 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30 hover:bg-emerald-500/20'
                      }`}
                    >
                      {isAuto ? (
                        <>
                          <Pause className="w-3.5 h-3.5" /> Pause Automation
                        </>
                      ) : (
                        <>
                          <Play className="w-3.5 h-3.5" /> Resume Automation
                        </>
                      )}
                    </button>
                    <span className={`text-[11px] font-medium ${isAuto ? 'text-emerald-400' : 'text-slate-500'}`}>
                      {isAuto ? '● Active Daily Auto-Pilot' : '○ Paused'}
                    </span>
                  </div>

                  <button
                    onClick={() => openEditModal(ch)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold transition"
                  >
                    <Settings2 className="w-3.5 h-3.5" /> Configure
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Add Channel Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 p-6 shadow-2xl">
            <h2 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
              <Plus className="w-5 h-5 text-blue-400" /> Connect YouTube Channel
            </h2>
            <p className="text-xs text-slate-400 mb-5">
              Configure automation profile and engine mode for your autonomous channel.
            </p>

            <form onSubmit={handleCreateChannel} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Channel Name</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Chintu Animated Kids TV"
                  value={formName}
                  onChange={(e) => setFormName(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Niche Category</label>
                <select
                  value={formNiche}
                  onChange={(e) => setFormNiche(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-blue-500"
                >
                  <option value="Kids Cartoon Stories">Kids Cartoon Stories (3D Animation)</option>
                  <option value="Hindi Moral Tales">Hindi Moral Tales & Panchatantra</option>
                  <option value="Animal Adventures">Animal Adventures Universe</option>
                  <option value="Kids Fun Rhymes">Kids Fun Rhymes & Learning</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Visual Generation Engine</label>
                <div className="grid grid-cols-2 gap-3">
                  <div
                    onClick={() => setFormVisualMode('FULL_ANIMATION')}
                    className={`cursor-pointer p-3 rounded-xl border transition ${
                      formVisualMode === 'FULL_ANIMATION'
                        ? 'bg-purple-600/20 border-purple-500 text-purple-300'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <div className="font-bold text-xs">FULL ANIMATION</div>
                    <div className="text-[10px] text-slate-400 mt-0.5">Fal AI / Luma temporal motion clips</div>
                  </div>
                  <div
                    onClick={() => setFormVisualMode('IMAGE_MOTION')}
                    className={`cursor-pointer p-3 rounded-xl border transition ${
                      formVisualMode === 'IMAGE_MOTION'
                        ? 'bg-blue-600/20 border-blue-500 text-blue-300'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <div className="font-bold text-xs">IMAGE MOTION</div>
                    <div className="text-[10px] text-slate-400 mt-0.5">FLUX Ken Burns dynamic motion</div>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Format</label>
                  <select
                    value={formVideoFormat}
                    onChange={(e: any) => setFormVideoFormat(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm"
                  >
                    <option value="BOTH">Shorts + Long (Both)</option>
                    <option value="SHORT">Shorts Only (9:16)</option>
                    <option value="LONG">Long Story Only (16:9)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Videos Per Day</label>
                  <input
                    type="number"
                    min={1}
                    max={5}
                    value={formVideosPerDay}
                    onChange={(e) => setFormVideosPerDay(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Publish Times (HH:MM IST)</label>
                <input
                  type="text"
                  placeholder="10:00, 18:00"
                  value={formPublishTimes}
                  onChange={(e) => setFormPublishTimes(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-blue-600 text-white text-xs font-semibold hover:bg-blue-500"
                >
                  Create Channel Profile
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Profile Modal */}
      {editingChannel && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl bg-slate-900 border border-slate-800 p-6 shadow-2xl">
            <h2 className="text-lg font-bold text-white mb-1 flex items-center gap-2">
              <Settings2 className="w-5 h-5 text-indigo-400" /> Configure {editingChannel.channel_name}
            </h2>
            <p className="text-xs text-slate-400 mb-5">
              Update automation preferences and visual rendering engine.
            </p>

            <form onSubmit={handleUpdateProfile} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Visual Mode</label>
                <div className="grid grid-cols-2 gap-3">
                  <div
                    onClick={() => setFormVisualMode('FULL_ANIMATION')}
                    className={`cursor-pointer p-3 rounded-xl border transition ${
                      formVisualMode === 'FULL_ANIMATION'
                        ? 'bg-purple-600/20 border-purple-500 text-purple-300'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <div className="font-bold text-xs">FULL ANIMATION</div>
                    <div className="text-[10px] text-slate-400 mt-0.5">Real AI temporal motion clips</div>
                  </div>
                  <div
                    onClick={() => setFormVisualMode('IMAGE_MOTION')}
                    className={`cursor-pointer p-3 rounded-xl border transition ${
                      formVisualMode === 'IMAGE_MOTION'
                        ? 'bg-blue-600/20 border-blue-500 text-blue-300'
                        : 'bg-slate-950 border-slate-800 text-slate-400 hover:border-slate-700'
                    }`}
                  >
                    <div className="font-bold text-xs">IMAGE MOTION</div>
                    <div className="text-[10px] text-slate-400 mt-0.5">FLUX + Ken Burns motion</div>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Niche Category</label>
                <input
                  type="text"
                  value={formNiche}
                  onChange={(e) => setFormNiche(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Format</label>
                  <select
                    value={formVideoFormat}
                    onChange={(e: any) => setFormVideoFormat(e.target.value)}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm"
                  >
                    <option value="BOTH">Shorts + Long (Both)</option>
                    <option value="SHORT">Shorts Only (9:16)</option>
                    <option value="LONG">Long Story Only (16:9)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-slate-300 mb-1">Videos Per Day</label>
                  <input
                    type="number"
                    min={1}
                    max={5}
                    value={formVideosPerDay}
                    onChange={(e) => setFormVideosPerDay(Number(e.target.value))}
                    className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Publish Times (HH:MM IST)</label>
                <input
                  type="text"
                  value={formPublishTimes}
                  onChange={(e) => setFormPublishTimes(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-slate-950 border border-slate-800 text-white text-sm"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                <button
                  type="button"
                  onClick={() => setEditingChannel(null)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-500"
                >
                  Save Profile
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
