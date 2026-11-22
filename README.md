# WriteWise AI

WriteWise AI is a writing analysis platform. The Flask API checks grammar, readability, vocabulary, and sentence complexity. The React frontend talks to that API. Phase 5 adds optional AI-powered rewrites and writing feedback.

Phase 4 adds document upload. The API accepts a `.txt`, `.pdf`, or `.docx` file, extracts the text, and can run the same analysis used by `POST /api/analyze`.

## Supported file formats

| Format | Extension | What is extracted |
| --- | --- | --- |
| Plain text | `.txt` | File text, including UTF-8, UTF-8 with BOM, UTF-16, and Windows-1252 |
| PDF | `.pdf` | Text from every page |
| Word | `.docx` | Paragraphs and table cells |

The file extension is not enough on its own. The server also checks the file contents, so a renamed or corrupted file is rejected. Password-protected PDFs are rejected.

**Maximum file size: 5 MB.**

## Run the API

From `backend`, with the virtual environment active:

```powershell
.\venv\Scripts\Activate.ps1
python run.py
```

The API listens on `http://127.0.0.1:5001` unless `PORT` is set.

## Upload API

`POST /api/upload`

Send `multipart/form-data` with a file field named `file`.

Analysis is optional. Add either of these when you want the extracted text scored by the existing analysis service:

- form field: `analyze=true`
- query string: `?analyze=true`

Accepted true values are `true`, `1`, `yes`, and `on`.

### Example request

```powershell
curl.exe -X POST "http://127.0.0.1:5001/api/upload" -F "file=@example.pdf"
```

With analysis:

```powershell
curl.exe -X POST "http://127.0.0.1:5001/api/upload" -F "file=@example.pdf" -F "analyze=true"
```

### Example response

```json
{
  "success": true,
  "message": "File uploaded and text extracted successfully.",
  "file": {
    "filename": "example.pdf",
    "file_type": "PDF",
    "character_count": 1000,
    "word_count": 180
  },
  "text": "Extracted document text..."
}
```

When analysis is requested, the response also includes an `analysis` object. That object is the result returned by `AnalysisService` (the same shape as `POST /api/analyze`): grammar, readability, vocabulary, sentence complexity, and score.

### Error responses

| Situation | Status |
| --- | --- |
| Missing file, empty file, missing filename, or corrupted file | 400 |
| File larger than 5 MB | 413 |
| Extension other than `.txt`, `.pdf`, or `.docx` | 415 |

Error bodies look like:

```json
{
  "success": false,
  "message": "The uploaded file is empty."
}
```

## Other API routes

- `GET /api/health` — API and database status
- `POST /api/analyze` — JSON body `{ "text": "..." }` for writing analysis
- `POST /api/improve` — JSON body `{ "text": "...", "tone": "Professional" }` for an AI rewrite and feedback

## AI writing improvement

Set the provider credentials in `backend/.env`. The provider key is read only by Flask; do not put it in a `VITE_` variable or send it from the browser.

```dotenv
LLM_PROVIDER=gemini
GEMINI_API_KEY=your-server-side-google-ai-studio-key
LLM_MODEL=gemini-3.5-flash-lite
LLM_TIMEOUT_SECONDS=30
```

Install the backend dependencies after updating the provider package:

```bash
cd backend
python -m pip install -r requirements.txt
```

For Anthropic, set `LLM_PROVIDER=anthropic`, `ANTHROPIC_API_KEY`, and an Anthropic model ID instead. For Gemini, set `LLM_PROVIDER=gemini`, `GEMINI_API_KEY`, and `LLM_MODEL=gemini-3.5-flash-lite`. Keep both API keys in `backend/.env`; never expose them to the frontend. The Gemini model ID is listed as a stable model in Google's current model documentation.

`POST /api/improve` accepts non-empty text up to 12,000 characters and an optional exact tone: `Professional`, `Academic`, `Formal`, `Casual`, or `Friendly`. If tone is omitted, it defaults to `Professional`. The response includes a meaning-preserving rewrite, grammar explanations with original and corrected text, and suggestions grouped under `Readability`, `Vocabulary`, `Sentence structure`, and `Repetition`.

Example request:

```json
{
  "text": "The team complete the report yesterday.",
  "tone": "Professional"
}
```

Example response:

```json
{
  "success": true,
  "tone": "Professional",
  "rewrite": "The team completed the report yesterday.",
  "grammar_explanations": [
    {
      "original_text": "The team complete the report yesterday.",
      "corrected_text": "The team completed the report yesterday.",
      "explanation": "Use the past tense for an action that happened yesterday."
    }
  ],
  "suggestions": {
    "Readability": [],
    "Vocabulary": [],
    "Sentence structure": [],
    "Repetition": []
  }
}
```

The improvement endpoint does not save submitted text or AI results to MongoDB. Missing configuration returns `503`; invalid input returns `400`; timeouts return `504`; provider rate limits return `429`; and other provider or output errors return a generic `502` response without provider details.

## Tests

From `backend`:

```powershell
.\venv\Scripts\python.exe -m pytest -v
```
