'use client';

import { ExtractionResult } from '@/lib/types';
import { Activity, AlertTriangle, CheckCircle2 } from 'lucide-react';

interface MetadataPanelProps {
  result: ExtractionResult;
}

export default function MetadataPanel({ result }: MetadataPanelProps) {
  const getRouteColor = (route: string) => {
    if (route === 'ocr_first') return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
    if (route === 'vision') return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
    return 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200';
  };

  const getRouteLabel = (route: string) => {
    if (route === 'ocr_first') return 'OCR-First';
    if (route === 'vision') return 'Vision';
    return 'OCR → Vision (Fallback)';
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600 dark:text-green-400';
    if (confidence >= 0.6) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 space-y-4">
      <h2 className="text-xl font-bold text-gray-800 dark:text-gray-200 flex items-center gap-2">
        <Activity size={24} />
        Extraction Metadata
      </h2>

      {/* Route - PROMINENTLY DISPLAYED */}
      <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-950 dark:to-purple-950
                      rounded-lg p-4 border-2 border-blue-200 dark:border-blue-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity size={20} className="text-blue-600 dark:text-blue-400" />
            <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
              Extraction Method:
            </span>
          </div>
          <span className={`px-4 py-2 rounded-lg text-base font-bold shadow-sm ${getRouteColor(result.route)}`}>
            {getRouteLabel(result.route)}
          </span>
        </div>
        <p className="text-xs text-gray-600 dark:text-gray-400 mt-2 ml-7">
          {result.route === 'ocr_first' && 'Fast OCR-based extraction with text analysis'}
          {result.route === 'vision' && 'Direct vision model analysis for complex images'}
          {result.route === 'ocr_fallback_vision' && 'OCR was insufficient, upgraded to vision analysis'}
        </p>
      </div>

      {/* Overall Confidence */}
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
          Overall Confidence:
        </span>
        <span className={`text-2xl font-bold ${getConfidenceColor(result.confidence)}`}>
          {Math.round(result.confidence * 100)}%
        </span>
      </div>

      {/* Complex for OCR: Yes/No only (no scores) */}
      <div className="pt-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <span className="text-sm font-medium text-gray-600 dark:text-gray-400">
          Complex for OCR
        </span>
        <span className="font-semibold text-gray-800 dark:text-gray-200">
          {result.route === 'ocr_first' ? 'No' : 'Yes'}
        </span>
      </div>

      {/* Warnings */}
      {result.warnings && result.warnings.length > 0 && (
        <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
          <h3 className="text-sm font-semibold mb-2 text-gray-700 dark:text-gray-300 flex items-center gap-2">
            <AlertTriangle size={16} className="text-yellow-600" />
            Warnings
          </h3>
          <div className="space-y-2">
            {result.warnings.map((warning, idx) => (
              <div
                key={idx}
                className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded p-3"
              >
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  {typeof warning === 'string' ? warning : JSON.stringify(warning)}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Success indicator */}
      {result.warnings?.length === 0 && (
        <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
            <CheckCircle2 size={20} />
            <span className="text-sm font-medium">Extraction successful, no warnings</span>
          </div>
        </div>
      )}
    </div>
  );
}
