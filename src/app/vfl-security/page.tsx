import VFLSecurityVisualizer from '@/components/VFLSecurityVisualizer';

export const metadata = {
  title: 'VFL Security Lab | Attack & Defense',
  description: 'Interactive visualization of label inference attacks and FLSG defense on real CIFAR-10 VFL experiments',
};

export default function VFLSecurityPage() {
  return <VFLSecurityVisualizer />;
}
