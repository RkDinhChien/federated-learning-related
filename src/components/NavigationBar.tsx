'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Home, ChevronRight, SplitSquareHorizontal } from 'lucide-react';
import LiveDemoLink from '@/components/LiveDemoLink';

interface NavItem {
  label: string;
  href: string;
}

const routes: Record<string, NavItem[]> = {
  '/': [{ label: 'Home', href: '/' }],
  '/topology': [
    { label: 'Home', href: '/' },
    { label: 'Topology', href: '/topology' }
  ],
  '/compare': [
    { label: 'Home', href: '/' },
    { label: 'Compare', href: '/compare' }
  ],
  '/attack-demo': [
    { label: 'Home', href: '/' },
    { label: 'Attack Demo', href: '/attack-demo' }
  ],
  '/vfl-security': [
    { label: 'Home', href: '/' },
    { label: 'VFL Security', href: '/vfl-security' }
  ],
  '/aggregation-defense': [
    { label: 'Home', href: '/' },
    { label: 'Defense', href: '/aggregation-defense' }
  ],
};

export default function NavigationBar() {
  const pathname = usePathname();
  const breadcrumbs = routes[pathname] || routes['/'];

  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-3">
      <div className="flex items-center justify-between max-w-7xl mx-auto">
        {/* Logo & Title */}
        <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
          <div className="w-10 h-10 border border-gray-300 bg-white flex items-center justify-center">
            <SplitSquareHorizontal className="w-5 h-5 text-gray-800" />
          </div>
          <div>
            <h1 className="text-base font-semibold text-gray-950">VFL Security Lab</h1>
            <p className="text-xs text-gray-500">Label inference and gradient defense</p>
          </div>
        </Link>

        {/* Breadcrumb */}
        <div className="flex items-center gap-3 text-sm">
          <div className="flex items-center gap-2">
            {breadcrumbs.map((item, index) => (
              <div key={item.href} className="flex items-center gap-2">
                {index > 0 && <ChevronRight className="w-4 h-4 text-gray-400" />}
                {index === breadcrumbs.length - 1 ? (
                  <span className="border-b border-gray-900 px-1 py-1 font-medium text-gray-950">{item.label}</span>
                ) : (
                  <Link 
                    href={item.href} 
                    className="text-gray-600 hover:text-gray-950 transition-colors flex items-center gap-1 px-1 py-1"
                  >
                    {index === 0 && <Home className="w-4 h-4" />}
                    <span>{item.label}</span>
                  </Link>
                )}
              </div>
            ))}
          </div>

          <LiveDemoLink />
        </div>
      </div>
    </nav>
  );
}
