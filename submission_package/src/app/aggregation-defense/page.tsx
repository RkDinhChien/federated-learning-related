import AggregationDefenseClient from './AggregationDefenseClient';

export const metadata = {
  title: 'Aggregation Defense | FL Visualizer',
  description: 'Visualize how robust aggregators defend against Byzantine attacks',
};

export default function AggregationDefensePage() {
  return <AggregationDefenseClient />;
}
