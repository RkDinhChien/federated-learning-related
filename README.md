# Federated Learning Visualizer - Next.js 15

A modern, interactive web application for visualizing federated learning experiments built with **Next.js 15**, **React 18**, and **TypeScript**.

## 🚀 Features

- **Next.js 15** with App Router and React Server Components
- **TypeScript** with strict mode for enhanced type safety
- **Real SR_MNIST Data Integration** - Load and visualize actual experimental results
- **Interactive Visualizations** - Dynamic charts powered by Recharts
- **Modern UI** - Built with Tailwind CSS and Radix UI components
- **Comparative Analysis** - Compare multiple experimental runs side-by-side
- **Server-Side Data Loading** - Efficient data fetching with async/await

## 📦 Tech Stack

- **Framework:** Next.js 15.5.7 (Latest)
- **UI Library:** React 18.3.1
- **Language:** TypeScript 5.7.2
- **Styling:** Tailwind CSS 3.4.17
- **Charts:** Recharts 2.15.2
- **UI Components:** Radix UI
- **Icons:** Lucide React

## 🛠️ Installation

```bash
npm install
```

## 🚀 Development

Start the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

## 📊 Data Structure

The application loads data from `data/SR_MNIST/Centralized_n=10_b=1/`:

- **index.json** - Main index mapping all experiments
- **Partition folders** - Contains experimental runs organized by data partition strategy:
  - DirichletPartition_alpha=1
  - iidPartition  
  - LabelSeperation
- **Run files** - Each run has metadata and iteration data in JSON format

### Data Format

Each experiment run includes:
- **Metadata**: Optimizer, attack type, aggregator, worker configuration
- **Iterations**: Training metrics (accuracy, loss, learning rate) at each iteration
- **Statistics**: Aggregated statistics across the entire run

## 🏗️ Project Structure

```
├── src/
│   ├── app/              # Next.js app router pages
│   │   ├── layout.tsx    # Root layout
│   │   ├── page.tsx      # Home page
│   │   ├── globals.css   # Global styles
│   │   ├── topology/     # Topology visualization page
│   │   │   ├── page.tsx  # Server component
│   │   │   └── TopologyPageClient.tsx  # Client component
│   │   └── compare/      # Comparison page
│   │       ├── page.tsx  # Server component
│   │       └── ComparePageClient.tsx  # Client component
│   ├── components/       # React components
│   │   ├── ControlPanel.tsx     # Experiment controls
│   │   ├── MetaCard.tsx         # Experiment metadata display
│   │   ├── NetworkViz.tsx       # Network topology visualization
│   │   ├── RunCharts.tsx        # Single run charts
│   │   ├── ComparisonCharts.tsx # Multi-run comparison
│   │   └── MetricsTable.tsx     # Detailed metrics table
│   ├── lib/             # Utility libraries
│   │   └── dataLoader.ts # Data loading service
│   └── types.ts         # TypeScript type definitions
├── data/                # Experimental data (SR_MNIST)
├── public/              # Static assets
├── next.config.ts       # Next.js configuration
├── tailwind.config.ts   # Tailwind CSS configuration
└── tsconfig.json        # TypeScript configuration
```

## 🔄 Migration from Vite

This application has been modernized from a Vite + React setup to Next.js 15:

### Key Improvements:

1. **Server Components** - Better performance with server-side rendering
2. **Automatic Code Splitting** - Optimized bundle sizes
3. **Built-in API Routes** - Server-side data loading without separate backend
4. **File-based Routing** - Intuitive App Router structure
5. **Optimized Bundling** - Advanced tree-shaking and compression
6. **TypeScript Strict Mode** - Enhanced type safety across the codebase

### Architecture Changes:

- **Routing:** React Router → Next.js App Router
- **Data Loading:** Client-side fetch → Server Components with async/await
- **Components:** Monolithic → Separated client/server components
- **Styling:** Maintained Tailwind CSS with updated v3.4 configuration
- **Build Tool:** Vite → Next.js (Turbopack-ready)

## 🎯 Usage

### Home Page

- Overview of the application
- Quick access to visualization pages
- Feature highlights

### Topology & Dataflow Page (`/topology`)

- **Experiment Selection:** Choose partition and specific run
- **Playback Controls:** Step through or play training iterations
- **Network Visualization:** View honest and byzantine workers connected to parameter server
- **Real-time Metrics:** Track accuracy, loss, and learning rate at each iteration
- **Experiment Details:** View complete metadata for selected run

### Comparative Metrics Page (`/compare`)

- **Filtering:** Filter runs by partition, optimizer, and attack type
- **Visual Comparison:** Compare up to 6 runs with overlaid line charts
- **Detailed Table:** Sortable table with all metrics
- **Selection:** Toggle individual runs for detailed comparison
- **Statistics:** View mean and standard deviation of accuracy across runs

## 🔍 Key Features

### Data Loading Service (`src/lib/dataLoader.ts`)

- **loadAllRuns()** - Load all available experimental runs
- **loadPartitionRuns()** - Load runs from specific partition
- **loadRunByName()** - Load specific run by name
- **filterRuns()** - Filter runs by various criteria
- **getRunsSummary()** - Get aggregated statistics

### Type Safety

All data structures are strongly typed:
- `RunData` - Complete run with metadata and iterations
- `RunMeta` - Experiment configuration and results
- `IterationPoint` - Per-iteration training metrics
- `RunStatistics` - Aggregated statistics

## 🌐 Browser Support

- Chrome/Edge (recommended)
- Firefox
- Safari

## 📝 Build for Production

```bash
npm run build
npm run start
```

## 🐛 Troubleshooting

If you encounter issues:

1. Clear `.next` folder: `rm -rf .next`
2. Reinstall dependencies: `rm -rf node_modules && npm install`
3. Check Node.js version: Requires Node.js 18.17 or later

## 📄 License

Private - Educational Project

## 👥 Authors

Built for IE105 - Web Development Course

---

**Note:** This application uses real experimental data from federated learning research. The visualizations help understand the impact of different:
- Data partition strategies (IID, Dirichlet, Label Separation)
- Byzantine attack types (Label Flipping, Furthest Label Flipping)
- Aggregation methods (Mean, Trimmed Mean, CC, LFighter, FABA)
- Optimizers (CSGD, CMomentum)
