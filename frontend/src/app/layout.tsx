import type { Metadata } from 'next';
import './globals.css';
import AppLayoutWrapper from '@/components/AppLayoutWrapper';

export const metadata: Metadata = {
  title: 'AutoTube AI — Autonomous AI YouTube Channel Production & Scaling SaaS',
  description: 'Turn YouTube into an automated money machine. Autonomous AI agents generate scripts, 3D animation, voice acting, and auto-publish daily.',
  icons: {
    icon: [
      { url: '/favicon.ico?v=3' },
      { url: '/icon.png?v=3', type: 'image/png' },
      { url: '/logo.png?v=3', type: 'image/png' },
    ],
    shortcut: '/favicon.ico?v=3',
    apple: '/apple-icon.png?v=3',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon.ico?v=3" sizes="any" />
        <link rel="icon" href="/icon.png?v=3" type="image/png" />
        <link rel="apple-touch-icon" href="/apple-icon.png?v=3" />
      </head>
      <body className="bg-background text-zinc-900 min-h-screen antialiased">
        <AppLayoutWrapper>{children}</AppLayoutWrapper>
      </body>
    </html>
  );
}
