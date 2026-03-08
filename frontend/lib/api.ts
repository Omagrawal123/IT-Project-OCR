import { ExtractionResult } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface ExtractOptions {
  api_key?: string;
  lang?: string;
  timezone?: string;
  [key: string]: unknown;
}

export const extractEventData = async (
  file: File,
  options: ExtractOptions = {}
): Promise<ExtractionResult> => {
  const formData = new FormData();
  formData.append("file", file);
  Object.entries(options).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      formData.append(key, String(value));
    }
  });

  const response = await fetch(`${API_URL}/api/v1/extract`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || "Extraction failed");
  }
  return response.json();
};
