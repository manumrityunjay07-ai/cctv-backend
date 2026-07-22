# CCTV Natural Language Search

A hackathon project to build "Natural Language Search for CCTV". The system ingests surveillance video, detects and tracks people, recognizes activities (entering, exiting, waiting, picking up/returning products, sitting, standing, interacting with shelves), converts these into timestamped event logs, indexes them for retrieval, and lets a user query the footage in plain English.

## Project Structure

- `venv/`: Python virtual environment.
- `data/`: Contains video files and event databases.
  - `raw_videos/`: Uploaded raw surveillance videos.
  - `clips/`: Extracted video clips of specific events.
  - `events.db`: SQLite database for local testing (or migration metadata).
- `src/`: Source code for the application.
  - `detection.py`: YOLOv8 detection logic.
  - `tracking.py`: ByteTrack integration.
  - `zones.py`: Logic for zone definitions and rule-based events.
  - `vlm_captioning.py`: Vision-Language Model interactions for captioning if needed.
  - `embeddings.py`: Embeddings generation using CLIP/DINO.
  - `search.py`: LLM-powered natural language search logic.
  - `app.py`: FastAPI backend and local Gradio demo.
- `requirements.txt`: Python dependencies.
- `.env`: Environment variables configuration.

## Setup

1. **Activate Virtual Environment**
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

2. **API Keys**
   Add your API keys to the `.env` file:
   - `GOOGLE_API_KEY`: Google Gemini API key (fallback LLM).
   - `GROQ_API_KEY`: Groq API key (primary LLM for fast inference).
   - `SUPABASE_URL` & `SUPABASE_KEY`: Supabase project URL and service key.

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: if any package fails to install, check the validation script output.)*

4. **FFmpeg**
   The project requires `ffmpeg`. Please ensure it is installed and added to your system PATH.
   - **Windows:** Download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)
   - **Mac:** `brew install ffmpeg`
   - **Linux:** `sudo apt install ffmpeg`

## Running Locally

To run the local Gradio demo, use:
```bash
python src/app.py
```

## Deployment Architecture

The deployed version differs from local development to maximize free-tier hosting limits:
- **Frontend**: React (Vite) deployed on **Vercel**.
- **Backend API**: Lightweight FastAPI orchestration on **Render**.
- **CV / Embeddings Compute**: Dockerized processing job on **Hugging Face Spaces**.
- **Database / Auth / Storage**: **Supabase** (Postgres + pgvector + Auth + Storage).

### Known Limitations (24-Hour Hackathon Scope)
- No real-time RTSP streaming (batch processing only).
- Render free tier spins down after ~15 mins, causing 30-60s cold starts.
- Supabase free tier pauses after 7 days of inactivity (requires keep-alive ping).
- ChromaDB is used for local rapid iteration, but production deployment utilizes Supabase `pgvector` to avoid multiple free-tier databases.
