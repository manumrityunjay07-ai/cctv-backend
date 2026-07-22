-- Supabase Schema for CCTV Natural Language Search

-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Table for storing zones
CREATE TABLE zones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    polygon_points JSONB NOT NULL, -- Storing [[x, y], [x, y], ...]
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Table for storing structured events
CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id VARCHAR(50) NOT NULL,
    event_type VARCHAR(50) NOT NULL, -- e.g., 'enter', 'exit', 'dwell', 'shelf_visit'
    zone_id UUID REFERENCES zones(id),
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,
    video_clip_path TEXT,
    summary TEXT,
    embedding vector(384), -- assuming sentence-transformers all-MiniLM-L6-v2 (384 dimensions)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Create an index for vector similarity search
CREATE INDEX ON events USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
