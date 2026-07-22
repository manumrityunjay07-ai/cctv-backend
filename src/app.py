import os
import uuid
import json
import logging
import sqlite3
import datetime
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from urllib.parse import quote
from dotenv import load_dotenv
from google import genai
import time
import urllib3
from urllib3.util.retry import Retry
from urllib3.poolmanager import PoolManager
import ssl
import certifi

# Configure SSL for HTTPS connections
ssl_context = ssl.create_default_context(cafile=certifi.where())
ssl_context.check_hostname = True
ssl_context.verify_mode = ssl.CERT_REQUIRED

# Disable SSL warnings if needed
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from .embeddings import EventIndexer
from .search import NLSearchEngine
from .redis import init_redis, get_redis_client

load_dotenv()

RAW_VIDEOS_DIR = os.path.join("data", "raw_videos")
os.makedirs(RAW_VIDEOS_DIR, exist_ok=True)

app = FastAPI(title="CCTV Cloud Search API")

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def retry_gemini_api(func, max_retries=3, backoff_factor=2):
    """Wrapper to retry Gemini API calls with exponential backoff."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            error_str = str(e).lower()
            if attempt < max_retries - 1 and any(x in error_str for x in ['disconnected', 'timeout', 'connection', 'remote']):
                wait_time = backoff_factor ** attempt
                logger.warning(f"API call failed (attempt {attempt + 1}): {e}. Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

import subprocess
app.mount("/videos", StaticFiles(directory=RAW_VIDEOS_DIR), name="videos")
os.makedirs("data/snapshots", exist_ok=True)
app.mount("/snapshots", StaticFiles(directory="data/snapshots"), name="snapshots")
# We use the cloud now
indexer = None
search_engine = None

def init_components():
    global indexer, search_engine
    if indexer is not None:
        return
    init_redis()
    indexer = EventIndexer()
    search_engine = NLSearchEngine()
    
    # Init DB
    conn = sqlite3.connect("data/events.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id TEXT PRIMARY KEY,
            person_id TEXT,
            event_type TEXT,
            zone_name TEXT,
            start_time TEXT,
            end_time TEXT,
            duration_seconds REAL,
            summary TEXT,
            risk_score INTEGER DEFAULT 0,
            snapshot TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.get("/api/health")
def read_root():
    rc = get_redis_client()
    return {
        "status": "ok",
        "components_loaded": indexer is not None,
        "mode": "cloud_processing",
        "redis": "connected" if rc else "unavailable",
    }

@app.post("/api/upload_and_process")
def upload_and_process(file: UploadFile = File(...)):
    if not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    init_components()
    
    file_path = os.path.join(RAW_VIDEOS_DIR, file.filename)
    with open(file_path, 'wb') as out_file:
        out_file.write(file.file.read())
        
    indexer.clear_all()
    
    conn = sqlite3.connect("data/events.db")
    cursor = conn.cursor()
    cursor.execute('''DELETE FROM events''')
    conn.commit()
    conn.close()
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        raise HTTPException(status_code=500, detail="Google API Key required for cloud processing.")
    
    logger.info(f"API Key present: {api_key[:20]}...") 
    
    try:
        # Initialize client with proper configuration
        logger.info("Initializing Gemini client...")
        client = genai.Client(api_key=api_key)
        
        # Test connectivity
        logger.info("Testing connectivity to Gemini API...")
        models = client.models.list()
        logger.info("✓ Successfully connected to Gemini API")
        
    except Exception as e:
        logger.error(f"Failed to initialize or connect Gemini client: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Cannot connect to Google API: {type(e).__name__}. Check your internet and API key.")
    
    logger.info(f"Uploading video to Gemini File API... File: {file_path}")
    try:
        # Check file exists and size
        if not os.path.exists(file_path):
            raise HTTPException(status_code=400, detail="Video file not found after upload")
        
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        logger.info(f"Video file size: {file_size_mb:.2f} MB")
        
        def upload_to_gemini():
            return client.files.upload(file=file_path)
        
        video_file = retry_gemini_api(upload_to_gemini, max_retries=3)
        logger.info(f"File uploaded successfully to Gemini")
    except Exception as e:
        logger.error(f"Failed to upload to Gemini: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Cloud upload failed: {type(e).__name__}: {str(e)}")
        
    logger.info(f"Video uploaded as: {video_file.uri}. Waiting for processing...")
    
    # Wait for processing with timeout
    max_wait = 600  # 10 minutes timeout
    elapsed = 0
    while video_file.state.name == "PROCESSING" and elapsed < max_wait:
        logger.info(f"Gemini is processing the video... (elapsed: {elapsed}s)")
        time.sleep(5)
        elapsed += 5
        try:
            video_file = client.files.get(name=video_file.name)
        except Exception as e:
            logger.error(f"Failed to check video status: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to check processing status: {str(e)}")
    
    if elapsed >= max_wait:
        logger.error("Video processing timeout after 10 minutes")
        raise HTTPException(status_code=500, detail="Video processing timeout")
        
    if video_file.state.name == "FAILED":
        logger.error(f"Gemini failed to process the video. State: {video_file.state}")
        raise HTTPException(status_code=500, detail="Cloud video processing failed.")
        
    logger.info("Video processed! Prompting Gemini for events...")
    
    # Use Gemini to extract ALL events as structured JSON
    prompt = """
    Watch this CCTV footage carefully.
    Identify every distinct person that appears in the video.
    For each person, generate a JSON array of events that occur. 
    An event is whenever they do an action, dwell somewhere, or interact with an object.
    
    Output strictly as a raw JSON array of objects without markdown formatting.
    Each object must match this schema:
    {
      "person_id": "P01",
      "event_type": "dwell|pickup|return|walking",
      "zone_name": "checkout|aisle|entrance",
      "duration_seconds": 12.5,
      "summary": "Detailed description of their appearance (clothing) and their action.",
      "risk_score": 0-100 (high if stealing/suspicious)
    }
    """
    
    try:
        logger.info("Requesting Gemini content generation...")
        
        def generate_content():
            return client.models.generate_content(
                model='gemini-flash-latest',
                contents=[prompt, video_file]
            )
        
        response = retry_gemini_api(generate_content, max_retries=3)
        logger.info("Received analysis from Gemini!")
    except Exception as e:
        logger.error(f"Failed to generate content from Gemini: {type(e).__name__}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Content generation failed: {type(e).__name__}: {str(e)}")
    
    try:
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json\n", "").replace("```", "").strip()
        events_data = json.loads(raw_text)
    except Exception as e:
        logger.error(f"Failed to parse Gemini JSON: {e}\nRaw Output: {response.text}")
        events_data = []

    all_events = []
    base_time = datetime.datetime.now()
    
    conn = sqlite3.connect("data/events.db")
    cursor = conn.cursor()
    
    for e in events_data:
        event_id = str(uuid.uuid4())
        person_id = str(e.get("person_id", "Unknown"))
        summary = e.get("summary", "No details")
        
        # Save to DB
        cursor.execute(
            '''
            INSERT INTO events (id, person_id, event_type, zone_name, start_time, duration_seconds, summary, risk_score)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (event_id, person_id, e.get("event_type", "unknown"), e.get("zone_name", "unknown"), base_time.isoformat(), e.get("duration_seconds", 0), summary, e.get("risk_score", 0))
        )
        
        # Index in ChromaDB
        metadata = {
            "person_id": person_id,
            "risk_score": e.get("risk_score", 0),
            "video_filename": file.filename,
            "zone_name": e.get("zone_name", "unknown"),
            "duration_seconds": e.get("duration_seconds", 0),
        }
        indexer.index_event(event_id, summary, metadata)
        all_events.append(event_id)
        
    conn.commit()
    conn.close()
    
    return {"message": "Cloud processing complete", "events_found": len(all_events)}

@app.get("/api/search")
def search_api(query: str):
    if not query:
        return {"results": []}
    if search_engine is None:
        return {"results": [], "answer": "Backend not initialized. Please process a video first."}
        
    summary, formatted_results = search_engine.search_and_summarize(query)
    
    final_results = []
    for res in formatted_results:
        meta = res["metadata"]
        doc = res["document"]
        video_filename = meta.get("video_filename", "")
        backend_url = "https://cctv-backend-seod.onrender.com"
        clipUrl = f"{backend_url}/videos/{quote(video_filename)}" if video_filename else "https://www.w3schools.com/html/mov_bbb.mp4"
        
        # Inject snapshot URL directly so it shows up next to the video in the UI
        person_id = meta.get("person_id", "")
        snapshot_url = f"{backend_url}/api/best_photo?person_id={person_id}" if person_id else None
        
        final_results.append({
            "id": res["id"],
            "summary": doc,
            "clipUrl": clipUrl,
            "snapshot": snapshot_url,
            "riskScore": meta.get("risk_score", 0),
            "metadata": meta
        })
        
    return {"results": final_results, "answer": summary}

@app.get("/api/analytics")
def get_analytics():
    if indexer is None:
        return {"zoneData": [], "riskData": []}
        
    all_events = indexer.get_all_events()
    metas = all_events.get("metadatas", []) or []
    
    zone_counts = {}
    risk_buckets = {"Safe (0-40)": 0, "Moderate (41-79)": 0, "High Risk (80+)": 0}
    
    for meta in metas:
        zone_name = meta.get("zone_name")
        if zone_name:
            zone_counts[zone_name] = zone_counts.get(zone_name, 0) + 1
                
        risk = int(meta.get("risk_score", 0))
        if risk >= 80:
            risk_buckets["High Risk (80+)"] += 1
        elif risk >= 41:
            risk_buckets["Moderate (41-79)"] += 1
        else:
            risk_buckets["Safe (0-40)"] += 1
            
    zone_data = [{"name": k, "visits": v} for k, v in zone_counts.items()]
    risk_data = [{"name": k, "value": v} for k, v in risk_buckets.items()]
    
    return {"zoneData": zone_data, "riskData": risk_data}

@app.get("/api/search_by_person")
def search_by_person_api(person_id: str):
    if indexer is None:
        return {"results": []}
    results = indexer.search_by_person(str(person_id))
    docs = results.get("documents", []) or []
    metas = results.get("metadatas", []) or []
    ids = results.get("ids", []) or []
    
    final_results = []
    for i in range(len(ids)):
        meta = metas[i]
        video_filename = meta.get("video_filename", "")
        backend_url = "https://cctv-backend-seod.onrender.com"
        clipUrl = f"{backend_url}/videos/{quote(video_filename)}" if video_filename else "https://www.w3schools.com/html/mov_bbb.mp4"
        
        person_id = meta.get("person_id", "")
        snapshot_url = f"{backend_url}/api/best_photo?person_id={person_id}" if person_id else None
        
        final_results.append({
            "id": ids[i],
            "summary": docs[i],
            "clipUrl": clipUrl,
            "snapshot": snapshot_url,
            "riskScore": meta.get("risk_score", 0),
            "metadata": meta
        })
    return {"results": final_results}

@app.get("/api/best_photo")
def get_best_photo(person_id: str):
    if indexer is None:
        return {"ok": False, "reason": "Not initialized"}
    
    # Try to find which video this person was in by searching for their events
    results = indexer.search_by_person(str(person_id))
    metas = results.get("metadatas", []) or []
    if not metas:
        return {"ok": False, "reason": "Person not found"}
        
    video_filename = metas[0].get("video_filename", "")
    if not video_filename:
        return {"ok": False, "reason": "Video not found"}
        
    video_path = os.path.join(RAW_VIDEOS_DIR, video_filename)
    if not os.path.exists(video_path):
        return {"ok": False, "reason": "Video file missing"}
        
    snapshot_filename = f"snapshot_{person_id}.jpg"
    snapshot_path = os.path.join("data/snapshots", snapshot_filename)
    
    # Extract a frame using ffmpeg at 2 seconds in (simulating a good face capture)
    try:
        if not os.path.exists(snapshot_path):
            subprocess.run([
                "ffmpeg", "-y", "-i", video_path, 
                "-ss", "00:00:02", "-vframes", "1", snapshot_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return FileResponse(snapshot_path)
    except Exception as e:
        logger.error(f"Snapshot extraction failed: {e}")
        return {"ok": False, "reason": "Extraction failed"}
