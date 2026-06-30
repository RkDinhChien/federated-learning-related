import type { Metadata } from 'next';
import './globals.css';
import NavigationBar from '@/components/NavigationBar';

export const metadata: Metadata = {
  title: 'Federated Learning Visualizer',
  description: 'Advanced visualization platform for federated learning experiments with Byzantine attack defense',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        <NavigationBar />
        {children}
      </body>
    </html>
  );
}
