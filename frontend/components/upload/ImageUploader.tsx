'use client';

import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, Image as ImageIcon, X, Loader2, AlertTriangle } from 'lucide-react';
import { extractEventData } from '@/lib/api';
import { ExtractionResult } from '@/lib/types';
import { formatFileSize } from '@/lib/utils';

interface ImageUploaderProps {
  onResult: (result: ExtractionResult) => void;
  onLoadingChange: (loading: boolean) => void;
}

export default function ImageUploader({ onResult, onLoadingChange }: ImageUploaderProps) {
  const [preview, setPreview] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string>('');
  const [fileSize, setFileSize] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [apiKey, setApiKey] = useState<string>('');
  const [showApiKey, setShowApiKey] = useState(false);

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      const file = acceptedFiles[0];
      if (!file) return;

      // Create preview
      const previewUrl = URL.createObjectURL(file);
      setPreview(previewUrl);
      setFileName(file.name);
      setFileSize(file.size);
      setError(null);

      // Check if API key is provided before extraction
      if (!apiKey) {
        setError('Please enter your Gemini API key before uploading an image.');
        return;
      }

      setIsLoading(true);
      onLoadingChange(true);

      try {
        const result = await extractEventData(file, {
          api_key: apiKey
        });
        onResult(result);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Extraction failed';
        if (errorMessage.includes('API key') || errorMessage.includes('401')) {
          setError('Invalid API key. Please check your Gemini API key and try again.');
        } else {
          setError(errorMessage);
        }
        console.error('Extraction error:', err);
      } finally {
        setIsLoading(false);
        onLoadingChange(false);
      }
    },
    [onResult, onLoadingChange, apiKey]
  );

  const { getRootProps, getInputProps, isDragActive, isDragReject } = useDropzone({
    onDrop,
    accept: { 'image/*': ['.png', '.jpg', '.jpeg', '.webp'] },
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024, // 10MB
  });

  const clearPreview = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (preview) {
      URL.revokeObjectURL(preview);
    }
    setPreview(null);
    setFileName('');
    setFileSize(0);
    setError(null);
  };

  return (
    <div className="w-full">
      {/* API Key Input */}
      <div className="mb-4 space-y-2">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          Gemini API Key
        </label>
        <div className="relative">
          <input
            type={showApiKey ? "text" : "password"}
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="Enter your Google Gemini API key"
            className="w-full px-4 py-2 pr-20 border border-gray-300 dark:border-gray-600 rounded-lg
                       bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100
                       focus:ring-2 focus:ring-blue-500 focus:border-transparent
                       placeholder-gray-400 dark:placeholder-gray-500"
          />
          <button
            type="button"
            onClick={() => setShowApiKey(!showApiKey)}
            className="absolute right-2 top-1/2 -translate-y-1/2 px-3 py-1 text-xs
                       text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
          >
            {showApiKey ? "Hide" : "Show"}
          </button>
        </div>
        <p className="text-xs text-gray-500 dark:text-gray-400">
          Get your free API key at{' '}
          <a
            href="https://ai.google.dev/gemini-api/docs/api-key"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-600 dark:text-blue-400 hover:underline"
          >
            Google AI Studio
          </a>
        </p>
        {!apiKey && (
          <p className="text-xs text-yellow-600 dark:text-yellow-400 flex items-center gap-1">
            <AlertTriangle size={12} />
            API key required for extraction
          </p>
        )}
      </div>

      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all
          ${isDragActive && !isDragReject ? 'border-blue-500 bg-blue-50 dark:bg-blue-950' : ''}
          ${isDragReject ? 'border-red-500 bg-red-50 dark:bg-red-950' : ''}
          ${!isDragActive && !preview ? 'border-gray-300 hover:border-blue-400 dark:border-gray-700 dark:hover:border-blue-600' : ''}
          ${preview ? 'border-gray-300 dark:border-gray-700' : ''}
        `}
      >
        <input {...getInputProps()} />

        {preview ? (
          <div className="space-y-4">
            <div className="relative inline-block">
              <img
                src={preview}
                alt="Preview"
                className="max-h-64 mx-auto rounded shadow-md"
              />
              {!isLoading && (
                <button
                  onClick={clearPreview}
                  className="absolute top-2 right-2 bg-red-500 text-white rounded-full p-1 hover:bg-red-600 transition"
                  title="Remove image"
                >
                  <X size={16} />
                </button>
              )}
            </div>
            <div className="text-sm text-gray-600 dark:text-gray-400">
              <p className="font-medium">{fileName}</p>
              <p>{formatFileSize(fileSize)}</p>
            </div>
            {isLoading && (
              <div className="flex items-center justify-center gap-2 text-blue-600 dark:text-blue-400">
                <Loader2 className="animate-spin" size={20} />
                <span>Extracting event data...</span>
              </div>
            )}
            {!isLoading && (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Click or drag to change image
              </p>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {isDragReject ? (
              <div className="flex flex-col items-center gap-4">
                <X className="h-12 w-12 text-red-400" />
                <p className="text-red-600 dark:text-red-400">
                  Invalid file type or size
                </p>
              </div>
            ) : (
              <>
                <Upload className="mx-auto h-12 w-12 text-gray-400" />
                <div>
                  <p className="text-lg font-medium text-gray-700 dark:text-gray-300">
                    {isDragActive ? 'Drop your event poster here' : 'Drop your event poster here'}
                  </p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    or click to browse
                  </p>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-400">
                  <ImageIcon size={16} />
                  <span>PNG, JPG, WEBP (max 10MB)</span>
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded-lg">
          <p className="text-red-700 dark:text-red-300 text-sm font-medium">
            Error: {error}
          </p>
        </div>
      )}
    </div>
  );
}
