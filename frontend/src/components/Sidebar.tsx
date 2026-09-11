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
  { href: '/settings', label: 'API & Channel Keys', icon: Settings },
  { href: '/pricing', label: 'Pricing & Plans', icon: Zap },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-[#fbfbfc] border-r border-gray-200/80 flex flex-col justify-between p-4 min-h-screen select-none">
      <div>
        {/* Polymer Brand Header */}
        <Link href="/dashboard" className="flex items-center gap-3 px-2 py-3 mb-5 group">
          <div className="w-9 h-9 rounded-xl bg-black flex items-center justify-center text-white shadow-sm group-hover:scale-105 transition-transform">
            <Play className="w-4 h-4 fill-white ml-0.5" />
          </div>
          <div>
            <div className="flex items-center gap-1.5">
              <span className="font-extrabold text-base text-gray-900 tracking-tight">AutoTube</span>
              <span className="text-[10px] font-bold px-1.5 py-0.2 rounded bg-gray-100 text-gray-600 border border-gray-200">
                PRO
              </span>
            </div>
            <p className="text-[11px] text-gray-500 font-medium">Autonomous SaaS</p>
          </div>
        </Link>

        {/* Navigation Menu (Polymer style) */}
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center justify-between px-3 py-2.5 rounded-xl text-xs font-semibold transition-all ${
                  isActive
                    ? 'bg-black text-white shadow-sm'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100/70'
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-gray-500'}`} />
                  <span>{item.label}</span>
                </div>
                {item.badge && (
                  <span className={`text-[10px] px-1.5 py-0.5 rounded-md font-bold ${
                    isActive 
                      ? 'bg-white/20 text-white' 
                      : 'bg-gray-100 text-gray-600 border border-gray-200'
                  }`}>
                    {item.badge}
                  </span>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Polymer Engine Mode Pill */}
      <div className="p-3.5 rounded-2xl bg-white border border-gray-200/80 shadow-sm space-y-2">
        <div className="flex items-center justify-between font-bold text-gray-900 text-xs">
          <span className="flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-amber-500" />
            <span>Visual Engine</span>
          </span>
          <span className="text-[10px] text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded-md border border-emerald-200 font-semibold">
            Active
          </span>
        </div>
        <p className="text-[11px] text-gray-500 leading-normal">
          FLUX.1 motion &amp; Fal Luma 3D with Devanagari Hindi voices
        </p>
      </div>
    </aside>
  );
}
