import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'AI Forex Trading Bot Configurator',
  description: 'Configure strategy and generate MT5 connector command',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-900 text-slate-100 antialiased">
        <div className="mx-auto max-w-5xl p-6">
          {children}
        </div>
      </body>
    </html>
  );
}
