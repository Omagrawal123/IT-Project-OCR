'use client';

import { useState } from 'react';
import ImageUploader from '@/components/upload/ImageUploader';
import ResultsDisplay from '@/components/results/ResultsDisplay';
import { ExtractionResult } from '@/lib/types';
import { Loader2, FileText } from 'lucide-react';

export default function Home() {
  const [result, setResult] = useState<ExtractionResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 py-8 px-4">
      <div className="container mx-auto max-w-7xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-3 mb-4">
            <FileText size={48} className="text-blue-600 dark:text-blue-400" />
            <h1 className="text-4xl font-bold text-gray-900 dark:text-gray-100">
              Event Poster Extraction
            </h1>
          </div>
          <p className="text-gray-600 dark:text-gray-400 text-lg max-w-2xl mx-auto">
            Upload an event poster and extract structured event data using AI-powered OCR and vision analysis
          </p>
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Upload Section */}
          <div className="space-y-4">
            <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6">
              <h2 className="text-2xl font-semibold mb-4 text-gray-800 dark:text-gray-200">
                Upload Poster
              </h2>
              <ImageUploader
                onResult={setResult}
                onLoadingChange={setIsLoading}
              />
            </div>

            {/* Info Card */}
            <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
              <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
                How it works
              </h3>
              <ul className="space-y-2 text-sm text-blue-800 dark:text-blue-200">
                <li className="flex items-start gap-2">
                  <span className="font-bold">1.</span>
                  <span>Upload your event poster (PNG, JPG, or WEBP)</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="font-bold">2.</span>
                  <span>AI analyzes image complexity to choose best extraction method</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="font-bold">3.</span>
                  <span>Extract event details: name, date, venue, contact, and more</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="font-bold">4.</span>
                  <span>Review, edit, and export structured JSON data</span>
                </li>
              </ul>
            </div>
          </div>

          {/* Results Section */}
          <div>
            {isLoading && (
              <div className="flex flex-col items-center justify-center h-64 bg-white dark:bg-gray-800 rounded-lg shadow-md">
                <Loader2 className="animate-spin h-12 w-12 text-blue-600 dark:text-blue-400 mb-4" />
                <p className="text-gray-600 dark:text-gray-400 font-medium">
                  Analyzing poster and extracting data...
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                  This may take a few seconds
                </p>
              </div>
            )}

            {result && !isLoading && (
              <ResultsDisplay result={result} />
            )}

            {!result && !isLoading && (
              <div className="flex flex-col items-center justify-center h-64 bg-white dark:bg-gray-800 rounded-lg shadow-md border-2 border-dashed border-gray-300 dark:border-gray-600">
                <FileText size={48} className="text-gray-400 mb-4" />
                <p className="text-gray-500 dark:text-gray-400 font-medium">
                  No results yet
                </p>
                <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">
                  Upload a poster to get started
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <footer className="mt-12 text-center text-sm text-gray-500 dark:text-gray-400">
          <p>
            Powered by FastAPI, PaddleOCR, and AI Vision Models
          </p>
        </footer>
      </div>
    </main>
  );
}
