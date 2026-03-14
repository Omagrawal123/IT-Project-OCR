# Event Poster Extraction

A hybrid OCR and vision-based system that extracts structured event data from poster images. The backend is implemented in Python with FastAPI; the frontend is a Next.js application that uploads images, displays extracted fields, and allows export.

## Features

- **Route selection**: Chooses between an OCR-first path (PaddleOCR plus LLM) and a vision-only path (LLM with image input) using image complexity (blur, edge density, text density).
- **Fallback**: If OCR extraction misses critical fields or confidence is below threshold, the pipeline retries using the vision route.
- **Structured time and date handling**: Extracts event date, end date, regular opening hours, opening-ceremony or first-day times, and special hours for specific dates so that “what time on what date” is explicit.
- **Normalization**: Standardizes dates (ISO 8601), times (24-hour), phone numbers, emails, and URLs. Preserves German characters (ä, ö, ü, ß) and restores them when OCR or LLM output uses ASCII substitutes.
- **Validation**: Ensures critical fields (event name, date, time or opening-ceremony time, venue address) are present and adds warnings when they are missing or low-confidence.
- **Frontend**: Dynamic form built from extracted fields (with a fixed order for dates and times), metadata (route, overall confidence, “Complex for OCR” yes/no), and export (JSON download, copy to clipboard).

## Architecture

```
OCR-main/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── core/            # Pipeline, schemas
│   │   ├── preprocessing/   # Image preprocessing and complexity scoring
│   │   ├── extractors/      # PaddleOCR integration
│   │   ├── llm/             # LLM adapter (Gemini)
│   │   ├── postprocessing/  # Normalization and validation
│   │   └── api/v1/endpoints/# Extract endpoint
│   └── requirements.txt
└── frontend/                # Next.js 15 App Router
    ├── app/                 # Pages
    ├── components/          # Upload, results, metadata, form
    └── lib/                 # Types, API client, utilities
```

## Tech Stack

### Backend

- **Python 3.11+**
- **FastAPI** – HTTP API
- **OpenCV** – Image preprocessing (resize, grayscale, CLAHE, denoise)
- **PaddleOCR** – Text recognition (default language: German)
- **Google Gemini** – LLM for text and vision extraction
- **Pydantic** – Request/response and settings validation

### Frontend

- **Next.js 15** – React framework (App Router)
- **TypeScript** – Typing
- **Tailwind CSS** – Layout and styling
- **react-dropzone** – File upload
- **lucide-react** – Icons

## Setup

### Backend

1. Go to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate   # Linux/macOS
   # or  venv\Scripts\activate  on Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   PaddleOCR will download language models (e.g. to `~/.paddleocr/`) on first use.

4. Environment:
   ```bash
   cp .env.example .env
   ```
   Set at least:
   - `LLM_API_KEY` – Gemini API key (required for extraction)
   - Optionally `LLM_MODEL`, `OCR_DEFAULT_LANG`, `COMPLEXITY_THRESHOLD`, etc.

5. Run the API:
   ```bash
   uvicorn app.main:app --reload
   ```
   API: [http://localhost:8000](http://localhost:8000)  
   Docs: [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs)

### Frontend

1. Go to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install and run:
   ```bash
   npm install
   cp .env.local.example .env.local   # optional; default API URL is http://localhost:8000
   npm run dev
   ```
   App: [http://localhost:3000](http://localhost:3000)

### Docker

From the project root:

```bash
docker compose up --build
```

- Backend: [http://localhost:8000](http://localhost:8000)  
- Frontend: [http://localhost:3000](http://localhost:3000)

To run only backend or frontend, use the service name (e.g. `docker compose up --build backend` or `frontend`).

## Usage

1. Start backend and frontend (or use Docker).
2. Open [http://localhost:3000](http://localhost:3000), enter a Gemini API key if prompted, and upload a poster (JPEG, PNG, or WebP).
3. Wait for extraction; then review and edit the fields. The “Event Details” section shows fields in a fixed order (event name, date, end date, opening time on first day, regular hours, special hours, speech time, venue, etc.).
4. Use “Complex for OCR: Yes/No” in the metadata to see which route was used (OCR-first vs vision). Export the result as JSON or copy to clipboard.

### API

- **POST** `/api/v1/extract`  
  - **Body**: `multipart/form-data` with `file` (image) and optionally:
    - `api_key` – Gemini API key (if not set elsewhere)
    - `lang` – OCR language, e.g. `de` (default) or `en`
    - `timezone` – e.g. `Europe/Berlin`
    - `force_route` – `ocr_first` or `vision` to override automatic routing

Example:

```bash
curl -X POST "http://localhost:8000/api/v1/extract" \
  -F "file=@poster.jpg" \
  -F "api_key=YOUR_GEMINI_KEY" \
  -F "lang=de"
```

## Configuration

### Backend (environment variables)

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `gemini` | LLM provider (e.g. gemini) |
| `LLM_API_KEY` | - | Gemini API key |
| `LLM_MODEL` | - | Model name (e.g. gemini-2.5-flash) |
| `OCR_DEFAULT_LANG` | `de` | Default OCR language (e.g. de, en) |
| `PREPROCESS_MAX_DIM` | 2000 | Max image dimension (preprocessing) |
| `BLUR_THRESHOLD` | 100.0 | Blur detection threshold |
| `COMPLEXITY_THRESHOLD` | 0.7 | Above this, vision route is used |
| `CORS_ORIGINS` | see config | Allowed frontend origins |

### Frontend

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | http://localhost:8000 | Backend base URL |

## Pipeline Overview

1. **Upload** – Image received by the API.
2. **Preprocessing** – Resize, grayscale, CLAHE, denoise (OpenCV).
3. **Complexity** – Blur (variance), edge density, text density (e.g. MSER-based), overall complexity score.
4. **Routing**:
   - If **blurry** → vision.
   - If **overall_complexity > threshold** → vision.
   - Else if **text_density > 0.2** and not blurry → **ocr_first**.
   - Else → vision.
5. **Extraction**:
   - **ocr_first**: PaddleOCR (with chosen `lang`) → concatenated text and blocks → LLM extracts JSON. If the result is insufficient (missing critical fields or low confidence), the same image is sent to the vision route.
   - **vision**: Image (base64) sent to LLM for direct vision extraction.
6. **Normalization** – Dates, times, phones, emails, URLs; promotion of time-like and date-like fields from `extra` into core fields; **German umlaut restoration** (e.g. Nurnberg → Nürnberg, and UE/OE/AE → Ü/Ö/Ä in all-caps words).
7. **Validation** – Critical fields (event_name, date, time or opening_ceremony_time, venue_address), overall confidence, warnings.
8. **Response** – JSON with `route`, `confidence`, `fields`, `extra`, `warnings`, and optional `complexity_score` and `raw` (e.g. OCR text and debug info). The UI shows “Complex for OCR: No” when route is `ocr_first`, otherwise “Yes”; it does not display raw complexity numbers.

## Output Schema (summary)

- `type`: `"event_poster"`
- `route`: `"ocr_first"` | `"vision"` | `"ocr_fallback_vision"`
- `confidence`: number (0–1)
- `fields`: object with per-field `value`, `confidence`, `source`. Core fields include:
  - `event_name`, `date`, `end_date`
  - `opening_ceremony_time` (e.g. first-day or ceremony time, possibly with labels like “17:00 (Fachböcke), 18:00 (Festzelt) on 27 Sep”)
  - `time` (regular hours), `special_hours`, `speech_time`
  - `venue_name`, `venue_address`, `description`, `organizer`, `contact_email`, `contact_phone`, `ticket_price`, `website`, `registration_link`
- `extra`: list of `{ key, value, confidence }` for additional attributes
- `warnings`: list of validation messages
- `complexity_score` (optional): blur, edge_density, text_density, overall_complexity, is_blurry
- `raw` (optional): e.g. `ocr_text`, `layout_blocks`, `debug`

## German and English Support

The system is aimed at posters in **German** or **English**. Default OCR language is **German** (`lang=de`). The LLM is instructed to keep German characters (ä, ö, ü, ß, Ä, Ö, Ü) and not replace them with ae, oe, ue, or ss. The normalizer restores common place names and terms (e.g. Nürnberg, München, Köln, Fränkisches) and, for all-caps words, converts UE/OE/AE to Ü/Ö/Ä so that umlauts are preserved in the final output.

## Testing

- **Backend**: From `backend`, install test deps with `pip install -r requirements-dev.txt`, then run `pytest tests/ -v`. Use `-m "not slow"` to skip the full-pipeline test (OCR + mock LLM). Run `pytest tests/ -v` with no filter to include the slow test.
- **Manual**: Use German and English posters; try `force_route=ocr_first` and `force_route=vision`; check that dates/times (including opening and special hours) and venue/event name are correct and that umlauts appear where expected.

## Deployment

- **Backend**: Set `LLM_API_KEY` and any other env vars; run with `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- **Frontend**: Set `NEXT_PUBLIC_API_URL` to the backend URL; build with `npm run build` and serve or deploy (e.g. Vercel/Netlify). Ensure backend CORS allows the frontend origin.

## Troubleshooting

- **PaddleOCR**: If installation fails, try the official install instructions or mirror (e.g. `pip install paddlepaddle paddleocr`).
- **CORS**: Configure `CORS_ORIGINS` in the backend to include the frontend URL.
- **Extraction errors**: Ensure `LLM_API_KEY` is set and that the image format and size are within the allowed limits.

## License

See repository or project terms.
