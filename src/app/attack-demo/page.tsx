import AttackDemo from '@/components/AttackDemo';

export const metadata = {
  title: 'Attack Demo | FL Visualizer',
  description: 'Interactive visualization of Byzantine attacks in federated learning',
};

export default function AttackDemoPage() {
  return (
    <div className="container mx-auto p-8">
      <AttackDemo />
    </div>
  );
}
