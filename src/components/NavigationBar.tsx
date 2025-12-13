'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Layers, Home, ChevronRight } from 'lucide-react';

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
  '/aggregation-defense': [
    { label: 'Home', href: '/' },
    { label: 'Defense', href: '/aggregation-defense' }
  ],
};

export default function NavigationBar() {
  const pathname = usePathname();
  const breadcrumbs = routes[pathname] || routes['/'];

  return (
    <nav className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between max-w-7xl mx-auto">
        {/* Logo & Title */}
        <Link href="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
          <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-purple-600 rounded-xl flex items-center justify-center shadow-md">
            <Layers className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">FL Visualizer</h1>
            <p className="text-xs text-gray-500">Byzantine Attack Analysis</p>
          </div>
        </Link>

        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-sm">
          {breadcrumbs.map((item, index) => (
            <div key={item.href} className="flex items-center gap-2">
              {index > 0 && <ChevronRight className="w-4 h-4 text-gray-400" />}
              {index === breadcrumbs.length - 1 ? (
                <span className="text-gray-900 font-semibold bg-blue-50 px-3 py-1 rounded-lg">{item.label}</span>
              ) : (
                <Link 
                  href={item.href} 
                  className="text-gray-600 hover:text-blue-600 transition-colors flex items-center gap-1 px-2 py-1 rounded-lg hover:bg-gray-50"
                >
                  {index === 0 && <Home className="w-4 h-4" />}
                  <span>{item.label}</span>
                </Link>
              )}
            </div>
          ))}
        </div>
      </div>
    </nav>
  );
}
