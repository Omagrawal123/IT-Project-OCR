'use client';

import { useState } from 'react';
import { ExtractionResult } from '@/lib/types';
import MetadataPanel from './MetadataPanel';
import DynamicForm from './DynamicForm';
import ExportButtons from './ExportButtons';

interface ResultsDisplayProps {
  result: ExtractionResult;
}

export default function ResultsDisplay({ result: initialResult }: ResultsDisplayProps) {
  const [result, setResult] = useState(initialResult);

  return (
    <div className="space-y-6">
      {/* Metadata Panel */}
      <MetadataPanel result={result} />

      {/* Extracted Fields Form */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold mb-4 text-gray-800 dark:text-gray-200">
          Extracted Data
        </h2>
        <DynamicForm result={result} onDataChange={setResult} />
      </div>

      {/* Export Buttons */}
      <ExportButtons result={result} />
    </div>
  );
}
