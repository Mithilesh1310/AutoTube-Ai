'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { 
  Play, Clock, ChevronDown, Zap, Globe, RefreshCw, Sparkles, 
  User, LogOut, Settings, ShieldCheck, Crown 
} from 'lucide-react';
import { triggerWorkflow, getStoredUser, fetchMyProfile, logoutUser, getAuthToken } from '@/lib/api';
import { UserProfile } from '@/lib/types';

interface NavbarProps {
  agentStatus?: string;
  agentEnabled?: boolean;
}

export default function Navbar({ agentStatus = 'ACTIVE', agentEnabled = true }: NavbarProps) {
  const [isRunning, setIsRunning] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [user, setUser] = useState<UserProfile | null>(null);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' | 'info' } | null>(null);

  useEffect(() => {
    // Check stored user or fetch profile
    const stored = getStoredUser();
    if (stored) {
      setUser(stored);
    }
    const token = getAuthToken();
    if (token) {
      fetchMyProfile().then(setUser).catch(() => {});
    }
  }, []);

  const handleRunWorkflow = async (type: 'DAILY_WORKFLOW' | 'SHORT' | 'LONG') => {
    setShowDropdown(false);
    try {
      setIsRunning(true);
      setToast({ message: `Triggering ${type}...`, type: 'info' });
      const res = await triggerWorkflow(type);
      setToast({ message: `Mission Started: ${res.job_id || 'Queued'}`, type: 'success' });
      setTimeout(() => setToast(null), 4000);
    } catch (err: any) {
      setToast({ message: `Error: ${err.message}`, type: 'error' });
      setTimeout(() => setToast(null), 5000);
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <header className="h-16 bg-white/80 backdrop-blur-md border-b border-gray-200/80 px-4 sm:px-6 flex items-center justify-between sticky top-0 z-40 transition-all">
      {/* Polymer-style Status Beacon */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200/80 text-emerald-800 text-xs font-semibold">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>AutoTube Engine</span>
          <span className="text-emerald-400">&bull;</span>
          <span className="font-mono text-[11px]">{agentStatus}</span>
        </div>

        <div className="hidden lg:flex items-center gap-1.5 text-gray-500 text-xs font-medium">
          <Clock className="w-3.5 h-3.5 text-gray-400" />
          <span>Asia/Kolkata (Daily 09:00 AM IST)</span>
        </div>
      </div>

      {/* Action Controls */}
      <div className="flex items-center gap-2.5">
        <Link
          href="/"
          className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition"
        >
          <Globe className="w-3.5 h-3.5 text-gray-500" />
          <span>Public Site</span>
        </Link>

        <Link
          href="/#pricing"
          className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition"
        >
          <Zap className="w-3.5 h-3.5 text-amber-500" />
          <span>Pricing</span>
        </Link>

        {toast && (
          <div className="px-3 py-1.5 rounded-xl text-xs bg-gray-900 text-white shadow-md animate-fade-in">
            {toast.message}
          </div>
        )}

        {/* Workflow Run Button */}
        <div className="relative">
          <div className="flex items-center rounded-xl btn-polymer-black shadow-sm">
            <button
              onClick={() => handleRunWorkflow('DAILY_WORKFLOW')}
              disabled={isRunning}
              className="flex items-center gap-2 px-4 py-2 text-xs font-bold text-white transition-all disabled:opacity-50"
            >
              {isRunning ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5 fill-current" />}
              <span>Run Daily Pipeline</span>
            </button>

            <button
              onClick={() => setShowDropdown(!showDropdown)}
              disabled={isRunning}
              className="px-2 py-2 border-l border-white/20 text-white hover:bg-white/10 transition-all rounded-r-xl"
              title="Pipeline Options"
            >
              <ChevronDown className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Workflow Selector Dropdown */}
          {showDropdown && (
            <div className="absolute right-0 mt-2 w-56 rounded-2xl bg-white border border-gray-200 shadow-xl p-1.5 z-50 animate-in fade-in slide-in-from-top-2">
              <button
                onClick={() => handleRunWorkflow('DAILY_WORKFLOW')}
                className="w-full text-left px-3 py-2 rounded-xl text-xs font-semibold text-gray-800 hover:bg-gray-50 flex items-center justify-between"
              >
                <span>Full Daily Workflow</span>
                <span className="text-[10px] text-gray-400">Short + Long</span>
              </button>
              
              <button
                onClick={() => handleRunWorkflow('SHORT')}
                className="w-full text-left px-3 py-2 rounded-xl text-xs font-semibold text-gray-800 hover:bg-gray-50 flex items-center justify-between"
              >
                <span>Short Only (9:16)</span>
                <span className="text-[10px] text-purple-700 font-bold bg-purple-50 px-1.5 py-0.5 rounded">30–60s</span>
              </button>

              <button
                onClick={() => handleRunWorkflow('LONG')}
                className="w-full text-left px-3 py-2 rounded-xl text-xs font-semibold text-gray-800 hover:bg-gray-50 flex items-center justify-between"
              >
                <span>Story Only (16:9)</span>
                <span className="text-[10px] text-indigo-700 font-bold bg-indigo-50 px-1.5 py-0.5 rounded">~2 Min</span>
              </button>
            </div>
          )}
        </div>

        {/* User Account / Profile Button */}
        <div className="relative pl-1 border-l border-gray-200 ml-1">
          {user ? (
            <div>
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="flex items-center gap-2 px-2.5 py-1.5 rounded-xl hover:bg-gray-100 transition text-left"
              >
                <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-indigo-600 to-purple-600 text-white flex items-center justify-center text-xs font-bold shadow-sm">
                  {user.username.charAt(0).toUpperCase()}
                </div>
                <div className="hidden md:block">
                  <div className="text-xs font-semibold text-gray-900 leading-tight flex items-center gap-1">
                    <span>{user.username}</span>
                    <Crown className="w-3 h-3 text-amber-500 fill-amber-500" />
                  </div>
                  <div className="text-[10px] text-gray-500">
                    {user.credits_balance} cr
                  </div>
                </div>
              </button>

              {showUserMenu && (
                <div className="absolute right-0 mt-2 w-64 rounded-2xl bg-white border border-gray-200 shadow-xl p-3 z-50 animate-in fade-in slide-in-from-top-2">
                  <div className="pb-3 border-b border-gray-100">
                    <p className="text-xs font-bold text-gray-900">{user.username}</p>
                    <p className="text-[11px] text-gray-500 truncate">{user.email}</p>
                    <div className="mt-2 flex items-center justify-between">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100">
                        {user.plan_tier || 'STARTER'} PLAN
                      </span>
                      <span className="text-xs font-bold text-emerald-600">
                        {user.credits_balance} Credits
                      </span>
                    </div>
                  </div>

                  <div className="py-2 space-y-1">
                    <Link
                      href="/settings"
                      onClick={() => setShowUserMenu(false)}
                      className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-xs font-medium text-gray-700 hover:bg-gray-50 transition"
                    >
                      <Settings className="w-4 h-4 text-gray-400" />
                      <span>Studio Settings</span>
                    </Link>
                    <Link
                      href="/#pricing"
                      onClick={() => setShowUserMenu(false)}
                      className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-xs font-medium text-amber-700 hover:bg-amber-50 transition"
                    >
                      <Zap className="w-4 h-4 text-amber-500" />
                      <span>Upgrade Plan / Add Credits</span>
                    </Link>
                  </div>

                  <div className="pt-2 border-t border-gray-100">
                    <button
                      onClick={logoutUser}
                      className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-xl text-xs font-medium text-rose-600 hover:bg-rose-50 transition"
                    >
                      <LogOut className="w-4 h-4" />
                      <span>Sign Out</span>
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <Link
              href="/login"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold text-neutral-800 bg-neutral-100 hover:bg-neutral-200 transition"
            >
              <User className="w-3.5 h-3.5" />
              <span>Sign In</span>
            </Link>
          )}
        </div>
      </div>
    </header>
  );
}
