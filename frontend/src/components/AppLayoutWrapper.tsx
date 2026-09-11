'use client';

import React from 'react';
import { usePathname } from 'next/navigation';
import Sidebar from '@/components/Sidebar';
import Navbar from '@/components/Navbar';

export default function AppLayoutWrapper({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const publicPages = ['/', '/login', '/signup', '/privacy', '/terms', '/refund', '/contact'];
  const isPublicPage = publicPages.includes(pathname);

  if (isPublicPage) {
    return (
      <div className="min-h-screen flex flex-col w-full">
        {children}
      </div>
    );
  }

  return (
    <div className="flex min-h-screen w-full bg-[#fbfbfc] text-zinc-900">
      <Sidebar />
      <div className="flex-1 flex flex-col min-w-0">
        <Navbar />
        <main className="p-4 md:p-6 flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
