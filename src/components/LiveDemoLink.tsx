'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { ExternalLink, Link2 } from 'lucide-react';

function resolveInitialDemoUrl() {
  if (process.env.NEXT_PUBLIC_DEMO_URL) {
    return process.env.NEXT_PUBLIC_DEMO_URL;
  }

  if (typeof window !== 'undefined') {
    return window.location.origin;
  }

  return 'http://localhost:3000';
}

export function useLiveDemoUrl() {
  const [demoUrl, setDemoUrl] = useState(resolveInitialDemoUrl());

  useEffect(() => {
    const configuredUrl = process.env.NEXT_PUBLIC_DEMO_URL;
    if (configuredUrl) {
      setDemoUrl(configuredUrl);
      return;
    }

    if (typeof window !== 'undefined') {
      setDemoUrl(window.location.origin);
    }
  }, []);

  return demoUrl;
}

export default function LiveDemoLink() {
  const demoUrl = useLiveDemoUrl();
  const href = useMemo(() => demoUrl.replace(/\/$/, ''), [demoUrl]);

  return (
    <div className="inline-flex items-center gap-3 rounded-2xl border border-indigo-200 bg-indigo-50 px-4 py-3">
      <div className="flex h-9 w-9 items-center justify-center rounded-full bg-indigo-100 text-indigo-700">
        <Link2 className="h-4 w-4" />
      </div>
      <div className="min-w-0">
        <div className="text-xs font-medium uppercase tracking-wide text-indigo-600">Vercel Demo</div>
        <Link
          href={href}
          target="_blank"
          rel="noreferrer"
          className="block max-w-[18rem] truncate text-sm font-semibold text-indigo-800 underline decoration-indigo-300 underline-offset-2 hover:text-indigo-900"
          title={href}
        >
          {href}
        </Link>
      </div>
      <Link
        href={href}
        target="_blank"
        rel="noreferrer"
        className="inline-flex items-center gap-2 rounded-full bg-indigo-700 px-3 py-2 text-xs font-semibold text-white transition hover:bg-indigo-800"
      >
        <ExternalLink className="h-3.5 w-3.5" />
        Open
      </Link>
    </div>
  );
}