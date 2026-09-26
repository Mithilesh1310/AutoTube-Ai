'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  LayoutDashboard, 
  Tv, 
  Sliders, 
  GitMerge, 
  Video, 
  Users, 
  BarChart3, 
  ShieldAlert, 
  Terminal, 
  Settings, 
  Zap,
  Play
} from 'lucide-react';

import { useEffect, useState } from 'react';

const navItems = [
  { href: '/dashboard', label: 'Studio Overview', icon: LayoutDashboard },
  { href: '/channels', label: 'Multi-Channel', icon: Tv },
  { href: '/automation/setup', label: 'Automation', icon: Sliders, badge: 'New' },
  { href: '/pipeline', label: 'AI Pipeline', icon: GitMerge },
  { href: '/videos', label: 'Video Library', icon: Video },
  { href: '/characters', label: 'Characters', icon: Users },
  { href: '/analytics', label: 'Analytics', icon: BarChart3 },
  { href: '/emergency', label: 'Safety Controls', icon: ShieldAlert },
  { href: '/logs', label: 'System Logs', icon: Terminal },
  { href: '/settings', label: 'Admin Settings', icon: Settings, adminOnly: true },
  { href: '/pricing', label: 'Pricing & Plans', icon: Zap },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const userStr = localStorage.getItem('autotube_user');
      if (userStr) {
        try {
          const user = JSON.parse(userStr);
          if (
            user.id === 1 || 
            user.is_admin || 
            user.email === 'monusahani0044@gmail.com' || 
            user.email === '2k24.csai1b.2412184@gmail.com'
          ) {
            setIsAdmin(true);
          }
        } catch (e) {}
      }
    }
  }, []);

  return (
    <aside className="w-64 bg-[#0F172A]/90 backdrop-blur-xl border-r border-slate-800/80 flex flex-col justify-between p-4 min-h-screen select-none">
      <div>
        {/* Brand Header */}
        <Link href="/dashboard" className="flex items-center gap-3 px-2 py-3 mb-5 group">
          <div className="w-10 h-10 rounded-xl overflow-hidden shadow-lg shadow-red-600/30 group-hover:scale-105 transition-transform bg-slate-900 border border-slate-800 flex items-center justify-center">
            <img src="/logo.png" alt="AutoTube AI Logo" className="w-full h-full object-cover" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-base text-white tracking-tight">AutoTube</span>
              <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-red-500/20 text-red-400 border border-red-500/30">
                PRO
              </span>
            </div>
            <p className="text-[11px] text-slate-400 font-medium">Autonomous SaaS</p>
          </div>
        </Link>

        {/* Navigation Menu */}
        <nav className="space-y-1">
          {navItems.filter((item) => !(item as any).adminOnly || isAdmin).map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-red-500/10 text-red-400 border border-red-500/20 shadow-md shadow-red-500/5'
                    : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-red-400' : 'text-slate-400'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-md font-bold ${
                    isActive 
                      ? 'bg-red-500/20 text-red-300 border border-red-500/30' 
                      : 'bg-slate-800 text-slate-400 border border-slate-700'
                  }`}>
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Engine Status Pill */}
      <div className="p-3.5 rounded-2xl bg-slate-900/90 border border-slate-800 shadow-sm space-y-2">
        <div className="flex items-center justify-between font-bold text-white text-xs">
          <span className="flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-amber-400" />
            <span>Visual Engine</span>
          </span>
          <span className="text-[10px] text-emerald-400 bg-emerald-500/10 px-1.5 py-0.5 rounded-md border border-emerald-500/20 font-semibold">
            Active
          </span>
        </div>
        <p className="text-[11px] text-slate-400 leading-normal">
          FLUX.1 motion &amp; Fal Luma 3D with Devanagari Hindi voices
        </p>
      </div>
    </aside>
  );
}
