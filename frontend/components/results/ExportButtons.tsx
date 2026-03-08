'use client';

import { useState } from 'react';
import { Download, Copy, Check } from 'lucide-react';
import { ExtractionResult } from '@/lib/types';
import { downloadJSON, copyToClipboard } from '@/lib/utils';

interface ExportButtonsProps {
  result: ExtractionResult;
}

export default function ExportButtons({ result }: ExportButtonsProps) {
  const [copied, setCopied] = useState(false);

  const handleDownload = () => {
    const timestamp = new Date().toISOString().split('T')[0];
    const filename = `event-extraction-${timestamp}.json`;
    downloadJSON(result, filename);
  };

  const handleCopy = async () => {
    const success = await copyToClipboard(JSON.stringify(result, null, 2));
    if (success) {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
      <h3 className="text-lg font-semibold mb-4 text-gray-800 dark:text-gray-200">
        Export Data
      </h3>
      <div className="flex flex-wrap gap-3">
        <button
          onClick={handleDownload}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors font-medium"
        >
          <Download size={18} />
          Download JSON
        </button>
        <button
          onClick={handleCopy}
          className={`flex items-center gap-2 px-4 py-2 rounded-md font-medium transition-colors ${
            copied
              ? 'bg-green-600 text-white hover:bg-green-700'
              : 'bg-gray-600 text-white hover:bg-gray-700'
          }`}
        >
          {copied ? (
            <>
              <Check size={18} />
              Copied!
            </>
          ) : (
            <>
              <Copy size={18} />
              Copy to Clipboard
            </>
          )}
        </button>
      </div>
      <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">
        Export the extracted data as JSON for further processing or integration.
      </p>
    </div>
  );
}
