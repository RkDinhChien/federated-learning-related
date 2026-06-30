'use client';

import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';
import { ExternalLink } from 'lucide-react';

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
    <Link
      href={href}
      target="_blank"
      rel="noreferrer"
      className="inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-4 py-2 text-sm font-semibold text-indigo-700 transition hover:bg-indigo-100"
    >
      <ExternalLink className="h-4 w-4" />
      Live Demo
    </Link>
  );
}