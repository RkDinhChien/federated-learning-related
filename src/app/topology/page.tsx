import { loadAllRuns, getAvailablePartitions } from '@/lib/dataLoader';
import TopologyPageClient from './TopologyPageClient';

export default async function TopologyPage() {
  const runs = await loadAllRuns();
  const partitions = await getAvailablePartitions();

  return <TopologyPageClient runs={runs} partitions={partitions} />;
}
