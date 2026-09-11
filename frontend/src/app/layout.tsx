import type { Metadata } from 'next';
import './globals.css';
import AppLayoutWrapper from '@/components/AppLayoutWrapper';

export const metadata: Metadata = {
  title: 'AutoTube AI — Autonomous AI YouTube Channel Production & Scaling SaaS',
  description: 'Turn YouTube into an automated money machine. Autonomous AI agents generate scripts, 3D animation, voice acting, and auto-publish daily.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-background text-zinc-900 min-h-screen antialiased">
        <AppLayoutWrapper>{children}</AppLayoutWrapper>
      </body>
    </html>
  );
}

