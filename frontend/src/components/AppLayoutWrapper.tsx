'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import Navbar from '@/components/Navbar';
import { LayoutDashboard, Tv, Sliders, GitMerge, Video, Menu, X } from 'lucide-react';

export default function AppLayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const publicPages = ['/', '/login', '/signup', '/privacy', '/terms', '/refund', '/contact'];
  const isPublicPage = publicPages.includes(pathname);

  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);

  if (isPublicPage) {
    return (
      <div className="min-h-screen flex flex-col w-full">
        {children}
      </div>
    );
  }

  return (
    <div className="flex min-h-screen w-full bg-[#0B0F17] text-slate-100 relative">
      {/* Desktop Sidebar */}
      <div className="hidden md:flex shrink-0">
        <Sidebar />
      </div>

      {/* Mobile Drawer Overlay */}
      {isMobileSidebarOpen && (
        <div className="fixed inset-0 z-50 flex md:hidden">
          <div 
            className="fixed inset-0 bg-black/80 backdrop-blur-sm animate-in fade-in"
            onClick={() => setIsMobileSidebarOpen(false)}
          />
          <div className="relative z-10 w-72 max-w-[85vw] bg-[#0F172A] border-r border-slate-800 flex flex-col justify-between p-4 min-h-screen animate-in slide-in-from-left">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-2">
              <span className="font-extrabold text-sm text-white">Menu</span>
              <button 
                onClick={() => setIsMobileSidebarOpen(false)}
                className="p-1 rounded-lg text-slate-400 hover:text-white bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <Sidebar onNavigate={() => setIsMobileSidebarOpen(false)} />
          </div>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 pb-16 md:pb-0">
        <Navbar onToggleMobileMenu={() => setIsMobileSidebarOpen(true)} />
        <main className="p-3 sm:p-4 md:p-6 flex-1 overflow-y-auto">{children}</main>
      </div>

      {/* Mobile Bottom Navigation Bar */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 z-40 bg-[#0F172A]/95 border-t border-slate-800/80 backdrop-blur-xl flex items-center justify-around py-2 px-1 text-[10px] font-semibold text-slate-400 select-none">
        <Link 
          href="/dashboard" 
          className={`flex flex-col items-center gap-1 px-2 py-1 rounded-lg transition ${
            pathname === '/dashboard' ? 'text-red-400 font-bold' : 'hover:text-slate-200'
          }`}
        >
          <LayoutDashboard className="w-4 h-4" />
          <span>Studio</span>
        </Link>
        <Link 
          href="/channels" 
          className={`flex flex-col items-center gap-1 px-2 py-1 rounded-lg transition ${
            pathname === '/channels' ? 'text-red-400 font-bold' : 'hover:text-slate-200'
          }`}
        >
          <Tv className="w-4 h-4" />
          <span>Channels</span>
        </Link>
        <Link 
          href="/automation/setup" 
          className={`flex flex-col items-center gap-1 px-2 py-1 rounded-lg transition ${
            pathname === '/automation/setup' ? 'text-red-400 font-bold' : 'hover:text-slate-200'
          }`}
        >
          <Sliders className="w-4 h-4" />
          <span>Auto-Pilot</span>
        </Link>
        <Link 
          href="/pipeline" 
          className={`flex flex-col items-center gap-1 px-2 py-1 rounded-lg transition ${
            pathname === '/pipeline' ? 'text-red-400 font-bold' : 'hover:text-slate-200'
          }`}
        >
          <GitMerge className="w-4 h-4" />
          <span>Pipeline</span>
        </Link>
        <Link 
          href="/videos" 
          className={`flex flex-col items-center gap-1 px-2 py-1 rounded-lg transition ${
            pathname === '/videos' ? 'text-red-400 font-bold' : 'hover:text-slate-200'
          }`}
        >
          <Video className="w-4 h-4" />
          <span>Videos</span>
        </Link>
        <button 
          onClick={() => setIsMobileSidebarOpen(true)}
          className="flex flex-col items-center gap-1 px-2 py-1 rounded-lg hover:text-slate-200 text-slate-400"
        >
          <Menu className="w-4 h-4" />
          <span>More</span>
        </button>
      </div>
    </div>
  );
}
