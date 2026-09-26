'use client';

export const dynamic = 'force-dynamic';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { 
  Sliders, 
  CheckCircle2, 
  ArrowRight, 
  ArrowLeft, 
  Tv, 
  Sparkles, 
  Zap, 
  Film, 
  Clock, 
  Mic, 
  Layers, 
  Flame,
  Check
} from 'lucide-react';
import { YouTubeChannelItem, VisualMode } from '@/lib/types';
import AuthGuard from '@/components/AuthGuard';
import { fetchChannels as apiFetchChannels, updateChannelAutomation as apiUpdateAutomation } from '@/lib/api';

export default function AutomationSetupWizard() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState<number>(1);
  const [channels, setChannels] = useState<YouTubeChannelItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);

  // Wizard state
  const [selectedChannelId, setSelectedChannelId] = useState<number | null>(null);
  const [niche, setNiche] = useState<string>('Kids Cartoon Stories');
  const [visualMode, setVisualMode] = useState<VisualMode>('FULL_ANIMATION');
  const [videosPerDay, setVideosPerDay] = useState<number>(2);
  const [videoFormat, setVideoFormat] = useState<'SHORT' | 'LONG' | 'BOTH'>('BOTH');
  const [publishTimes, setPublishTimes] = useState<string[]>(['10:00', '18:00']);
  const [voiceStyle, setVoiceStyle] = useState<string>('hi-IN-SwaraNeural');
  const [characterUniverse, setCharacterUniverse] = useState<string>('Chintu Universe');

  useEffect(() => {
    async function load() {
      try {
        const data = await apiFetchChannels();
        setChannels(data);
        if (data && data.length > 0) {
          const selected = data[0];
          setSelectedChannelId(selected.id);
          if (selected.profile) {
            if (selected.profile.niche) setNiche(selected.profile.niche);
            if (selected.profile.visual_mode) setVisualMode(selected.profile.visual_mode);
            if (selected.profile.video_format) setVideoFormat(selected.profile.video_format);
            if (selected.profile.videos_per_day) setVideosPerDay(selected.profile.videos_per_day);
            if (selected.profile.publish_times) setPublishTimes(selected.profile.publish_times);
          }
        }
      } catch (err) {
        console.error('Failed to load channels:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleFinish = async () => {
    if (!selectedChannelId) {
      alert('Please select or create a YouTube channel first.');
      return;
    }
    setSubmitting(true);
    try {
      await apiUpdateAutomation(selectedChannelId, {
        niche,
        visual_mode: visualMode,
        video_format: videoFormat,
        videos_per_day: videosPerDay,
        publish_times: publishTimes,
        automation_enabled: true,
        auto_publish: true,
        voice_style: voiceStyle,
        character_universe: characterUniverse
      });
      router.push('/channels');
    } catch (err: any) {
      alert(`Failed to save automation profile: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  const steps = [
    { num: 1, title: 'Target Channel' },
    { num: 2, title: 'Content Niche' },
    { num: 3, title: 'Visual Engine' },
    { num: 4, title: 'Frequency' },
    { num: 5, title: 'Schedule' },
    { num: 6, title: 'Voice & Characters' },
    { num: 7, title: 'Launch' }
  ];

  return (
    <AuthGuard>
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="text-center mb-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-bold mb-3">
          <Sparkles className="w-3.5 h-3.5" /> 7-Step Autonomous Setup
        </div>
        <h1 className="text-3xl font-black text-white tracking-tight">Channel Automation Wizard</h1>
        <p className="text-sm text-slate-400 mt-2 max-w-lg mx-auto">
          Configure end-to-end autonomous video creation, visual rendering modes, and automated YouTube scheduling.
        </p>
      </div>

      {/* Progress Stepper */}
      <div className="flex items-center justify-between mb-8 overflow-x-auto pb-4">
        {steps.map((s, idx) => {
          const isDone = currentStep > s.num;
          const isCurr = currentStep === s.num;
          return (
            <div key={s.num} className="flex items-center flex-1 last:flex-none">
              <div className="flex flex-col items-center min-w-[70px]">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs transition-all ${
                  isDone 
                    ? 'bg-emerald-500 text-white' 
                    : isCurr 
                    ? 'bg-blue-600 text-white ring-4 ring-blue-500/20' 
                    : 'bg-slate-800 text-slate-400'
                }`}>
                  {isDone ? <Check className="w-4 h-4" /> : s.num}
                </div>
                <span className={`text-[10px] mt-1.5 font-medium whitespace-nowrap ${isCurr ? 'text-blue-400 font-bold' : 'text-slate-400'}`}>
                  {s.title}
                </span>
              </div>
              {idx < steps.length - 1 && (
                <div className={`h-0.5 flex-1 mx-2 ${isDone ? 'bg-emerald-500' : 'bg-slate-800'}`}></div>
              )}
            </div>
          );
        })}
      </div>

      {/* Step Container Card */}
      <div className="rounded-2xl bg-slate-900/90 border border-slate-800/80 p-8 shadow-2xl backdrop-blur-xl">
        {/* Step 1: Select Channel */}
        {currentStep === 1 && (
          <div className="space-y-6">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Tv className="w-5 h-5 text-blue-400" /> Step 1: Select Target YouTube Channel
            </h3>
            <p className="text-xs text-slate-400">Choose which channel AutoTube should manage autonomously.</p>

            {/* Active Automation Card for configured channels */}
            {channels.find(c => c.id === selectedChannelId)?.profile?.automation_enabled && (
              <div className="p-5 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2 text-emerald-400 font-extrabold text-xs uppercase tracking-wide">
                    <CheckCircle2 className="w-4 h-4" /> Active Auto-Pilot Configured
                  </div>
                  <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300">
                    Live Status: Ready
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs bg-slate-950/60 p-3 rounded-xl border border-slate-800">
                  <div>
                    <span className="text-slate-500 block text-[10px]">Niche Category</span>
                    <span className="font-bold text-white">{niche}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">Visual Engine</span>
                    <span className="font-bold text-purple-300">{visualMode}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">Format</span>
                    <span className="font-bold text-blue-300">{videoFormat}</span>
                  </div>
                  <div>
                    <span className="text-slate-500 block text-[10px]">Daily Schedule</span>
                    <span className="font-bold text-emerald-300">{videosPerDay} Videos ({publishTimes.join(', ')})</span>
                  </div>
                </div>

                <p className="text-xs text-slate-300 italic">
                  Aapka automation already ACTIVE aur configured hai. Click "Next Step" below to modify or update any setting step-by-step.
                </p>
              </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              {channels.map((ch) => (
                <div
                  key={ch.id}
                  onClick={() => setSelectedChannelId(ch.id)}
                  className={`cursor-pointer p-4 rounded-xl border transition ${
                    selectedChannelId === ch.id
                      ? 'bg-blue-600/15 border-blue-500 text-white ring-2 ring-blue-500/20'
                      : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <div className="font-bold text-sm">{ch.channel_name}</div>
                  <div className="text-xs text-slate-400 mt-1">{ch.profile?.niche || 'Kids Cartoon Stories'}</div>
                  <div className="text-[10px] text-emerald-400 mt-2 font-medium flex items-center gap-1">
                    ● Connected Account {ch.profile?.automation_enabled && '(Auto-Pilot Active)'}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 2: Content Niche */}
        {currentStep === 2 && (
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Flame className="w-5 h-5 text-amber-400" /> Step 2: Choose Content Niche
            </h3>
            <p className="text-xs text-slate-400">Select story tone and thematic category for AI script writing.</p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2">
              {[
                { name: 'Kids Cartoon Stories', desc: 'Engaging 3D animated tales with morals for kids 3-10' },
                { name: 'Hindi Panchatantra & Animal Tales', desc: 'Classic ancient moral wisdom reimagined in 3D' },
                { name: 'Fun Science & Space Adventures', desc: 'Curiosity-sparking planetary & animal discoveries' },
                { name: 'Bedtime Calming Stories', desc: 'Soothing bedtime tales with gentle music and visuals' }
              ].map((item) => (
                <div
                  key={item.name}
                  onClick={() => setNiche(item.name)}
                  className={`cursor-pointer p-4 rounded-xl border transition ${
                    niche === item.name
                      ? 'bg-amber-500/15 border-amber-500 text-white ring-2 ring-amber-500/20'
                      : 'bg-slate-950/60 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <div className="font-bold text-sm">{item.name}</div>
                  <div className="text-xs text-slate-400 mt-1">{item.desc}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 3: Visual Generation Engine */}
        {currentStep === 3 && (
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Zap className="w-5 h-5 text-purple-400" /> Step 3: Visual Rendering Engine
            </h3>
            <p className="text-xs text-slate-400">Select between AI video animation and dynamic motion image rendering.</p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
              <div
                onClick={() => setVisualMode('FULL_ANIMATION')}
                className={`cursor-pointer p-5 rounded-2xl border transition ${
                  visualMode === 'FULL_ANIMATION'
                    ? 'bg-purple-600/20 border-purple-500 ring-2 ring-purple-500/30'
                    : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-black text-purple-400 uppercase tracking-wide">Professional 3D</span>
                  <span className="text-[10px] bg-purple-500/20 text-purple-300 px-2 py-0.5 rounded-full font-bold">New</span>
                </div>
                <h4 className="font-bold text-white text-base">FULL_ANIMATION</h4>
                <p className="text-xs text-slate-400 mt-1.5">
                  Generates real AI temporal motion video clips using Fal AI (Luma Dream Machine / Kling API) with optical-flow motion QA.
                </p>
              </div>

              <div
                onClick={() => setVisualMode('IMAGE_MOTION')}
                className={`cursor-pointer p-5 rounded-2xl border transition ${
                  visualMode === 'IMAGE_MOTION'
                    ? 'bg-blue-600/20 border-blue-500 ring-2 ring-blue-500/30'
                    : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-black text-blue-400 uppercase tracking-wide">Verified Pipeline</span>
                  <span className="text-[10px] bg-blue-500/20 text-blue-300 px-2 py-0.5 rounded-full font-bold">100% Stable</span>
                </div>
                <h4 className="font-bold text-white text-base">IMAGE_MOTION</h4>
                <p className="text-xs text-slate-400 mt-1.5">
                  FLUX.1-schnell primary with Pollinations fallback, Character Bible injection, dynamic Ken Burns camera zoom, and FFmpeg assembly.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Step 4: Video Format & Daily Frequency */}
        {currentStep === 4 && (
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Film className="w-5 h-5 text-indigo-400" /> Step 4: Publishing Frequency & Video Format
            </h3>
            <p className="text-xs text-slate-400">Determine how many videos AutoTube produces each day.</p>

            <div className="space-y-4 pt-2">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-2">Video Format</label>
                <div className="grid grid-cols-3 gap-3">
                  {[
                    { id: 'BOTH', label: 'Shorts + Long Story' },
                    { id: 'SHORT', label: 'Shorts (9:16 Only)' },
                    { id: 'LONG', label: 'Long Story (16:9 Only)' }
                  ].map((fmt) => (
                    <button
                      key={fmt.id}
                      type="button"
                      onClick={() => setVideoFormat(fmt.id as any)}
                      className={`p-3 rounded-xl border text-xs font-bold transition ${
                        videoFormat === fmt.id
                          ? 'bg-indigo-600/20 border-indigo-500 text-indigo-300'
                          : 'bg-slate-950/60 border-slate-800 text-slate-400'
                      }`}
                    >
                      {fmt.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-2">Daily Videos: {videosPerDay}</label>
                <input
                  type="range"
                  min={1}
                  max={4}
                  value={videosPerDay}
                  onChange={(e) => setVideosPerDay(Number(e.target.value))}
                  className="w-full accent-blue-600"
                />
                <div className="flex justify-between text-[11px] text-slate-500 mt-1">
                  <span>1 Video/day</span>
                  <span>2 Videos/day (Recommended)</span>
                  <span>3 Videos/day</span>
                  <span>4 Videos/day</span>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 5: Publishing Schedule */}
        {currentStep === 5 && (
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Clock className="w-5 h-5 text-emerald-400" /> Step 5: Automated Publishing Schedule
            </h3>
            <p className="text-xs text-slate-400">Set daily target release times (IST). AutoTube will automatically produce and queue videos ahead of schedule.</p>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-300 font-semibold">Morning Shorts Slot</span>
                <span className="px-2 py-1 rounded bg-slate-800 font-mono text-purple-400">10:00 AM IST</span>
              </div>
              <div className="flex items-center justify-between text-xs">
                <span className="text-slate-300 font-semibold">Evening Long Story Slot</span>
                <span className="px-2 py-1 rounded bg-slate-800 font-mono text-indigo-400">06:00 PM IST</span>
              </div>
            </div>
          </div>
        )}

        {/* Step 6: Voice & Character Universe */}
        {currentStep === 6 && (
          <div className="space-y-4">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <Mic className="w-5 h-5 text-pink-400" /> Step 6: Voice & Character Universe
            </h3>
            <p className="text-xs text-slate-400">Configure default narrator voice and character bible profile.</p>

            <div className="grid grid-cols-2 gap-4 pt-2">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Narrator Voice</label>
                <select
                  value={voiceStyle}
                  onChange={(e) => setVoiceStyle(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs"
                >
                  <option value="hi-IN-SwaraNeural">Swara (Female, Warm Storyteller)</option>
                  <option value="hi-IN-MadhurNeural">Madhur (Male, Energetic Narrator)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1.5">Character Universe</label>
                <select
                  value={characterUniverse}
                  onChange={(e) => setCharacterUniverse(e.target.value)}
                  className="w-full px-3 py-2.5 rounded-xl bg-slate-950 border border-slate-800 text-white text-xs"
                >
                  <option value="Chintu Universe">Chintu & Jungle Friends (5 Characters)</option>
                  <option value="Custom">Custom Universe</option>
                </select>
              </div>
            </div>
          </div>
        )}

        {/* Step 7: Review & Launch */}
        {currentStep === 7 && (
          <div className="space-y-5">
            <h3 className="text-lg font-bold text-white flex items-center gap-2">
              <CheckCircle2 className="w-5 h-5 text-emerald-400" /> Step 7: Review & Launch Autonomous Schedule
            </h3>
            <p className="text-xs text-slate-400">Confirm setup. Clicking start will activate autonomous multi-channel generation.</p>

            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-900">
                <span className="text-slate-500">Channel ID:</span>
                <span className="text-white font-bold">{selectedChannelId}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-900">
                <span className="text-slate-500">Visual Engine:</span>
                <span className="text-purple-400 font-bold">{visualMode}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-900">
                <span className="text-slate-500">Content Niche:</span>
                <span className="text-white font-medium">{niche}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-900">
                <span className="text-slate-500">Format & Frequency:</span>
                <span className="text-white font-medium">{videoFormat} ({videosPerDay} videos/day)</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Schedule Slots:</span>
                <span className="text-emerald-400 font-mono">{publishTimes.join(', ')} IST</span>
              </div>
            </div>
          </div>
        )}

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between pt-8 mt-6 border-t border-slate-800">
          <button
            type="button"
            disabled={currentStep === 1}
            onClick={() => setCurrentStep(prev => prev - 1)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold transition ${
              currentStep === 1 
                ? 'opacity-30 cursor-not-allowed text-slate-600' 
                : 'bg-slate-800 hover:bg-slate-700 text-slate-300'
            }`}
          >
            <ArrowLeft className="w-4 h-4" /> Previous
          </button>

          {currentStep < 7 ? (
            <button
              type="button"
              onClick={() => setCurrentStep(prev => prev + 1)}
              className="flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold shadow-lg shadow-blue-600/20 transition"
            >
              Next Step <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              type="button"
              disabled={submitting}
              onClick={handleFinish}
              className="flex items-center gap-2 px-6 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-xs font-black shadow-lg shadow-emerald-600/30 transition"
            >
              <Sparkles className="w-4 h-4" /> {submitting ? 'Activating...' : 'START AUTONOMOUS SYSTEM'}
            </button>
          )}
        </div>
      </div>
    </div>
    </AuthGuard>
  );
}
