import Link from 'next/link';
import { Layers, BarChart3, Shield, Target } from 'lucide-react';

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* Welcome Section */}
        <div className="mb-8">
          <div className="inline-block px-4 py-2 bg-blue-100 rounded-full text-blue-700 text-sm font-medium mb-4">
            🎯 Federated Learning Research
          </div>
          <h1 className="text-4xl font-bold text-gray-900 mb-3">
            Welcome back! 👋
          </h1>
          <p className="text-lg text-gray-600">
            Explore Byzantine attacks and defense mechanisms in federated learning
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-2xl p-5 border border-gray-200">
            <div className="text-blue-600 font-bold text-3xl mb-1">4</div>
            <div className="text-sm text-gray-600">Attack Types</div>
          </div>
          <div className="bg-white rounded-2xl p-5 border border-gray-200">
            <div className="text-green-600 font-bold text-3xl mb-1">5</div>
            <div className="text-sm text-gray-600">Aggregators</div>
          </div>
          <div className="bg-white rounded-2xl p-5 border border-gray-200">
            <div className="text-purple-600 font-bold text-3xl mb-1">60K</div>
            <div className="text-sm text-gray-600">Samples</div>
          </div>
          <div className="bg-white rounded-2xl p-5 border border-gray-200">
            <div className="text-orange-600 font-bold text-3xl mb-1">10</div>
            <div className="text-sm text-gray-600">Workers</div>
          </div>
        </div>

        {/* Main Features */}
        <div className="mb-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Main Features</h2>
        </div>

        <div className="grid md:grid-cols-2 gap-4 mb-8">
          <Link
            href="/topology"
            className="group bg-white rounded-2xl p-6 border border-gray-200 hover:shadow-lg transition-all"
          >
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                <Layers className="w-6 h-6 text-blue-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-gray-900 mb-1 group-hover:text-blue-600 transition-colors">
                  Topology & Training
                </h3>
                <p className="text-sm text-gray-600">
                  Network visualization with real-time metrics
                </p>
              </div>
            </div>
          </Link>

          <Link
            href="/compare"
            className="group bg-white rounded-2xl p-6 border border-gray-200 hover:shadow-lg transition-all"
          >
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-indigo-100 rounded-xl flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                <BarChart3 className="w-6 h-6 text-indigo-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-gray-900 mb-1 group-hover:text-indigo-600 transition-colors">
                  Performance Compare
                </h3>
                <p className="text-sm text-gray-600">
                  Compare metrics across configurations
                </p>
              </div>
            </div>
          </Link>

          <Link
            href="/attack-demo"
            className="group bg-white rounded-2xl p-6 border border-gray-200 hover:shadow-lg transition-all"
          >
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                <Target className="w-6 h-6 text-red-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-gray-900 mb-1 group-hover:text-red-600 transition-colors">
                  Attack Demo
                </h3>
                <p className="text-sm text-gray-600">
                  See 4 Byzantine attack types in action
                </p>
              </div>
            </div>
          </Link>

          <Link
            href="/aggregation-defense"
            className="group bg-white rounded-2xl p-6 border border-gray-200 hover:shadow-lg transition-all"
          >
            <div className="flex items-start gap-4">
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                <Shield className="w-6 h-6 text-green-600" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-gray-900 mb-1 group-hover:text-green-600 transition-colors">
                  Defense Mechanisms
                </h3>
                <p className="text-sm text-gray-600">
                  5 robust aggregators with live simulation
                </p>
              </div>
            </div>
          </Link>
        </div>

        {/* Dataset Info */}
        <div className="bg-white rounded-2xl p-6 border border-gray-200">
          <div className="flex items-center gap-2 mb-5">
            <div className="w-10 h-10 bg-purple-100 rounded-xl flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-purple-600" />
            </div>
            <h3 className="text-lg font-bold text-gray-900">Dataset Info</h3>
          </div>
          <div className="grid md:grid-cols-4 gap-6">
            <div>
              <div className="text-xs text-gray-500 mb-1">Dataset</div>
              <div className="text-base font-bold text-gray-900">SR_MNIST</div>
              <div className="text-xs text-gray-500 mt-1">60,000 samples</div>
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-1">Workers</div>
              <div className="text-base font-bold text-gray-900">10 Total</div>
              <div className="text-xs text-gray-500 mt-1">9 Honest + 1 Byzantine</div>
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-1">Partitions</div>
              <div className="text-base font-bold text-gray-900">3 Types</div>
              <div className="text-xs text-gray-500 mt-1">IID, Dirichlet, Label Sep</div>
            </div>
            <div>
              <div className="text-xs text-gray-500 mb-1">Training</div>
              <div className="text-base font-bold text-gray-900">200 Rounds</div>
              <div className="text-xs text-gray-500 mt-1">~20K iterations</div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
