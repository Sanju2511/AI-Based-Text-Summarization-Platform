# AI-Based Text Summarization Platform

A full-stack web application for summarizing plain text and PDF documents using a local transformer-based NLP model.

## Features

- Accepts direct text input
- Accepts PDF uploads
- Extracts and cleans PDF text safely
- Generates AI-based summaries
- Supports paragraph or bullet-style output
- Allows summary-length control
- Shows document statistics and compression ratio
- Includes keyword extraction for additional insight
- Provides downloadable summary export

## Recommended Stack

- Frontend: HTML, CSS, JavaScript
- Backend: FastAPI
- AI: Hugging Face Transformers
- PDF processing: `pypdf`
- Export: `reportlab`

## Project Structure

```text
AL_Learning/
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── schemas.py
│   └── services/
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── PROJECT_REPORT.md
├── PROJECT_REPORT.pdf
├── requirements.txt
├── render.yaml
└── .env.example
```

## Run Instructions

1. Open a terminal in the project folder:

```bash
cd /path/to/AL_Learning
```

2. Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Download the summarization model once:

```bash
ALLOW_MODEL_DOWNLOAD=1 python scripts/preload_model.py
```

5. Start the application:

```bash
python -m backend.main
```

6. Open the app in your browser:

```text
http://127.0.0.1:8000
```

## Quick Verification Commands

```bash
PYTHONPYCACHEPREFIX=./tmp/pycache .venv/bin/python3 scripts/smoke_test.py
```

## How It Works

1. The user provides direct text or uploads a PDF.
2. The backend validates the input and extracts text safely.
3. The application cleans the content and selects the summarization path:
   - Short input: hybrid extractive mode for cleaner concise output
   - Longer input: local Hugging Face transformer model
4. The summary is returned with keywords, statistics, and export support.

## API Endpoints

- `GET /`
  - Serves the frontend
- `GET /health`
  - Returns a simple health response
- `POST /api/summarize`
  - Accepts text or PDF input and returns summary output
- `POST /api/export`
  - Generates a downloadable summary PDF

## Testing

The project was checked for:

- text summarization
- PDF summarization
- offline local model loading
- export to PDF
- backend import and compile checks

## Notes

- The local summarization model is configured for CPU execution.
- For short content, the app uses a hybrid extractive path because very small abstractive models can produce weaker summaries on already-short text.
- The generated model cache is ignored by git through `.gitignore`.
