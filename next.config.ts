import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  output: 'standalone', // Optimize for Vercel deployment
  images: {
    unoptimized: true, // Disable image optimization for static files
  },
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
    };
    // Optimize for production
    config.optimization = {
      ...config.optimization,
      minimize: true,
    };
    return config;
  },
};

export default nextConfig;
