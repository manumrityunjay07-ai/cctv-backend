# CCTV Natural Language Search

## 1. Project Overview

CCTV Natural Language Search is an AI-powered video investigation platform that converts CCTV footage into searchable event data. Users can upload surveillance videos, analyze them with AI, search the extracted events using natural-language queries, and review analytics and timeline-based insights.

The project is built as a full-stack web application with:
- a React frontend for user interaction
- a FastAPI backend for processing and serving data
- AI-based event extraction for video understanding
- optional Redis and vector-based search support

---

## 2. Purpose

The system is designed to help users quickly inspect large amounts of CCTV footage without manually watching every minute of video. Instead of scrolling through raw footage, users can ask questions such as:
- “Who entered the store?”
- “Show suspicious activity near the checkout”
- “Find events related to person P01”

This makes the tool useful for security monitoring, retail analytics, and incident investigation.

---

## 3. Key Features

### Video Upload and Processing
- Upload CCTV videos through the web interface
- Save the uploaded video to the local data directory
- Process the video with AI to extract structured events

### Event Extraction
The backend extracts event information including:
- person identifier
- event type
- zone or location
- duration
- summary description
- risk score

### Natural Language Search
Users can search the extracted event data using plain English queries.

### Analytics Dashboard
The dashboard provides visual summaries of:
- zone visit counts
- risk distribution categories

### Person Timeline
The application can retrieve and display a timeline of activity for a specific person.

### Export and Processing Utilities
The repository also includes scripts for exporting snapshots, processing videos, and generating outputs for investigation.

---

## 4. Technology Stack

### Backend
- Python
- FastAPI
- Uvicorn
- SQLite
- Redis
- ChromaDB
- Google Generative AI
- python-dotenv
- python-multipart

### Frontend
- React
- Vite
- Recharts
- CSS

### Infrastructure
- Local development via PowerShell launcher
- Optional Docker Compose setup

---

## 5. Project Structure

- README.md – high-level project overview and setup notes
- start.ps1 – launcher script to start backend and frontend
- docker-compose.yml – optional Docker-based local deployment
- requirements.txt – Python dependencies
- src/ – backend application code
- frontend/ – React frontend code
- data/ – uploaded videos, snapshots, and local databases
- scripts/ – helper utilities for processing and export tasks
- tools/ – test and utility scripts

---

## 6. Backend Architecture

The backend entry point is the file src/app.py.

### Main Responsibilities
- expose REST API endpoints
- accept uploaded video files
- initialize required services
- process videos using AI
- store extracted events in SQLite
- index event data for search
- serve analytics and person-based results

### Main API Endpoints

#### Health Check
- GET /api/health
- Returns backend status and component availability

#### Upload and Process
- POST /api/upload_and_process
- Accepts a video file and analyzes it

#### Search
- GET /api/search
- Accepts a text query and returns matching results

#### Analytics
- GET /api/analytics
- Returns chart data for zones and risk levels

#### Person Search
- GET /api/search_by_person
- Returns results for a specific person ID

#### Timeline
- GET /api/person_timeline
- Returns event timeline data for a person

---

## 7. Frontend Architecture

The frontend is implemented in frontend/src/App.jsx.

### Main User Experience
1. User logs in
2. User uploads a video
3. Backend processes the video
4. User searches extracted events
5. User views analytics or person timeline results

### Main UI Areas
- login view
- video upload panel
- search interface
- analytics charts
- timeline modal
- export/job status handling

---

## 8. Data Model

The application stores detected events in a SQLite table called events.

### Event Fields
- id
- person_id
- event_type
- zone_name
- start_time
- end_time
- duration_seconds
- summary
- risk_score
- snapshot

These records are also indexed for retrieval and search.

---

## 9. Installation

### Prerequisites
- Python installed
- Node.js and npm installed
- ffmpeg installed and available on PATH

### Python Dependencies
Install backend dependencies:

```bash
pip install -r requirements.txt
```

### Frontend Dependencies
Install frontend packages:

```bash
cd frontend
npm install
```

---

## 10. Running Locally

### Option 1: One-click launcher
From the project root:

```powershell
./start.ps1
```

This starts:
- backend at http://localhost:8000
- frontend at http://localhost:5173

### Option 2: Manual Start
Run backend:

```bash
python src/app.py
```

Run frontend:

```bash
cd frontend
npm run dev
```

---

## 11. Environment Configuration

The application expects configuration values such as:
- GOOGLE_API_KEY
- GROQ_API_KEY
- SUPABASE_URL
- SUPABASE_KEY

These should be provided in a .env file.

---

## 12. Usage Example

1. Start the application locally.
2. Open the frontend in your browser.
3. Log in.
4. Upload a CCTV video.
5. Wait for processing to complete.
6. Use search terms such as:
   - “person near entrance”
   - “suspicious activity”
   - “checkout behavior”
7. Review analytics and timeline outputs.

---

## 13. Limitations

This project is a hackathon-style prototype and has some limitations:
- processing can be slow depending on video length and AI service response time
- cloud-based processing depends on valid API credentials
- some features may require external services or local support tools
- real-time streaming is not the main focus of the current implementation

---

## 14. Future Improvements

Potential enhancements include:
- stronger local inference support
- real-time video streaming
- improved event detection accuracy
- better person re-identification
- richer analytics and reporting
- authentication and access control
- export to reports and downloadable clips

---

## 15. Summary

CCTV Natural Language Search is a practical AI-driven solution for making CCTV footage searchable and easier to investigate. It bridges the gap between raw surveillance video and structured, queryable insights using modern web, backend, and AI technologies.
