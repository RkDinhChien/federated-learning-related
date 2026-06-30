'use client';

import React, { useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Camera, Download, FileImage, Loader2 } from 'lucide-react';
import { toast } from 'sonner';

interface ScreenshotToolsProps {
  targetId: string;
  filename?: string;
}

export default function ScreenshotTools({ targetId, filename = 'screenshot' }: ScreenshotToolsProps) {
  const [isCapturing, setIsCapturing] = useState(false);

  const captureScreenshot = async (format: 'png' | 'svg' = 'png') => {
    setIsCapturing(true);
    
    try {
      const element = document.getElementById(targetId);
      if (!element) {
        toast.error('Element not found');
        return;
      }

      if (format === 'png') {
        // Use html2canvas for PNG
        const html2canvas = (await import('html2canvas')).default;
        const canvas = await html2canvas(element, {
          backgroundColor: '#ffffff',
          logging: false,
        } as any); // Type workaround for html2canvas options
        
        const dataUrl = canvas.toDataURL('image/png');
        downloadImage(dataUrl, `${filename}.png`);
        toast.success('PNG screenshot saved!');
      } else {
        // For SVG, if the element contains SVG
        const svg = element.querySelector('svg');
        if (!svg) {
          toast.error('No SVG element found');
          return;
        }
        
        const serializer = new XMLSerializer();
        const svgString = serializer.serializeToString(svg);
        const blob = new Blob([svgString], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        downloadImage(url, `${filename}.svg`);
        toast.success('SVG screenshot saved!');
      }
    } catch (error) {
      console.error('Screenshot error:', error);
      toast.error('Failed to capture screenshot');
    } finally {
      setIsCapturing(false);
    }
  };

  const downloadImage = (dataUrl: string, filename: string) => {
    const link = document.createElement('a');
    link.download = filename;
    link.href = dataUrl;
    link.click();
  };

  return (
    <div className="flex gap-2">
      <Button
        onClick={() => captureScreenshot('png')}
        disabled={isCapturing}
        variant="outline"
        size="sm"
      >
        {isCapturing ? (
          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
        ) : (
          <Camera className="h-4 w-4 mr-2" />
        )}
        Save as PNG
      </Button>
      
      <Button
        onClick={() => captureScreenshot('svg')}
        disabled={isCapturing}
        variant="outline"
        size="sm"
      >
        {isCapturing ? (
          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
        ) : (
          <FileImage className="h-4 w-4 mr-2" />
        )}
        Save as SVG
      </Button>
    </div>
  );
}

// High-resolution export for presentations
export function ExportForPresentation({ targetId, filename = 'presentation' }: ScreenshotToolsProps) {
  const [isExporting, setIsExporting] = useState(false);

  const exportHighRes = async () => {
    setIsExporting(true);
    
    try {
      const element = document.getElementById(targetId);
      if (!element) {
        toast.error('Element not found');
        return;
      }

      const html2canvas = (await import('html2canvas')).default;
      const canvas = await html2canvas(element, {
        backgroundColor: '#ffffff',
        logging: false,
        width: 1920, // Full HD width
        height: 1080, // Full HD height
      } as any); // Type workaround
      
      const dataUrl = canvas.toDataURL('image/png', 1.0); // Maximum quality
      
      const link = document.createElement('a');
      link.download = `${filename}_1920x1080.png`;
      link.href = dataUrl;
      link.click();
      
      toast.success('High-resolution image exported!');
    } catch (error) {
      console.error('Export error:', error);
      toast.error('Failed to export image');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <Button
      onClick={exportHighRes}
      disabled={isExporting}
      variant="default"
      size="sm"
    >
      {isExporting ? (
        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
      ) : (
        <Download className="h-4 w-4 mr-2" />
      )}
      Export for Presentation (1920×1080)
    </Button>
  );
}
