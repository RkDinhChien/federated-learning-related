import { loadAllRuns } from '@/lib/dataLoader';
import ComparePageClient from './ComparePageClient';

export default async function ComparePage() {
  const runs = await loadAllRuns();

  return <ComparePageClient runs={runs} />;
}
