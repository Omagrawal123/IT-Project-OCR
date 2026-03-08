'use client';

import { useState } from 'react';
import { ExtractionResult, FieldData, ExtraField } from '@/lib/types';
import { formatFieldName, getConfidenceColor } from '@/lib/utils';

const FIELD_ORDER = [
  'event_name',
  'date',
  'end_date',
  'opening_ceremony_time',
  'time',
  'special_hours',
  'speech_time',
  'venue_name',
  'venue_address',
  'description',
  'organizer',
  'contact_email',
  'contact_phone',
  'ticket_price',
  'website',
  'registration_link',
];

interface DynamicFormProps {
  result: ExtractionResult;
  onDataChange?: (updatedResult: ExtractionResult) => void;
}

export default function DynamicForm({ result, onDataChange }: DynamicFormProps) {
  const [formData, setFormData] = useState(result);

  const handleFieldChange = (fieldName: string, newValue: string) => {
    const updatedFields = {
      ...formData.fields,
      [fieldName]: {
        ...formData.fields[fieldName as keyof typeof formData.fields],
        value: newValue,
      },
    };

    const updated = { ...formData, fields: updatedFields };
    setFormData(updated);
    onDataChange?.(updated);
  };

  const handleExtraFieldChange = (index: number, newValue: string) => {
    if (!formData.extra) return;

    const updatedExtra = [...formData.extra];
    updatedExtra[index] = { ...updatedExtra[index], value: newValue };

    const updated = { ...formData, extra: updatedExtra };
    setFormData(updated);
    onDataChange?.(updated);
  };

  const renderField = (fieldName: string, data: FieldData | undefined) => {
    if (!data || data.value === null || data.value === undefined) return null;

    const isLongText = ['description'].includes(fieldName);
    const label = formatFieldName(fieldName);

    return (
      <div key={fieldName} className="space-y-2">
        <div className="flex items-center justify-between">
          <label htmlFor={fieldName} className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {label}
          </label>
          <div className="flex items-center gap-2">
            <span className={`text-xs px-2 py-1 rounded ${getConfidenceColor(data.confidence)}`}>
              {Math.round(data.confidence * 100)}%
            </span>
            <span className="text-xs text-gray-500 dark:text-gray-400">{data.source}</span>
          </div>
        </div>

        {isLongText ? (
          <textarea
            id={fieldName}
            value={data.value || ''}
            onChange={(e) => handleFieldChange(fieldName, e.target.value)}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-gray-100"
          />
        ) : (
          <input
            id={fieldName}
            type="text"
            value={data.value || ''}
            onChange={(e) => handleFieldChange(fieldName, e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-gray-100"
          />
        )}
      </div>
    );
  };

  const orderedFields = FIELD_ORDER.filter(
    (name) => formData.fields[name]?.value != null && formData.fields[name]?.value !== ''
  ).map((name) => [name, formData.fields[name]] as [string, FieldData]);
  const otherFields = Object.entries(formData.fields).filter(
    ([name, data]) => data?.value && !FIELD_ORDER.includes(name)
  );
  const coreFields = [...orderedFields, ...otherFields];

  return (
    <div className="space-y-6">
      {/* Core fields */}
      {coreFields.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-4 text-gray-800 dark:text-gray-200">
            Event Details
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {coreFields.map(([fieldName, data]) => renderField(fieldName, data))}
          </div>
        </div>
      )}

      {/* Extra fields */}
      {formData.extra && formData.extra.length > 0 && (
        <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-semibold mb-4 text-gray-800 dark:text-gray-200">
            Additional Information
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {formData.extra.map((field, idx) => (
              <div key={idx} className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    {formatFieldName(field.key)}
                  </label>
                  <span className={`text-xs px-2 py-1 rounded ${getConfidenceColor(field.confidence)}`}>
                    {Math.round(field.confidence * 100)}%
                  </span>
                </div>
                <input
                  type="text"
                  value={String(field.value)}
                  onChange={(e) => handleExtraFieldChange(idx, e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-800 dark:text-gray-100"
                />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
