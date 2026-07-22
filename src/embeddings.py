import os
import chromadb
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

class EventIndexer:
    def __init__(self, db_path="data/chroma_db"):
        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.collection = self.chroma_client.get_or_create_collection(name="events")
        
        # Configure Gemini API
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key and api_key != "your_gemini_api_key_here":
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None
            print("Warning: GOOGLE_API_KEY not found. Embeddings will fail.")
        
    def generate_embedding(self, text):
        """Generate embedding for text using Google Gemini."""
        result = self.client.models.embed_content(
            model="text-embedding-004",
            contents=text,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT")
        )
        return result.embeddings[0].values
        
    def index_event(self, event_id, event_summary, metadata=None):
        """Index a textual summary of an event into ChromaDB."""
        if not event_summary:
            return
            
        embedding = self.generate_embedding(event_summary)
        
        self.collection.add(
            ids=[str(event_id)],
            embeddings=[embedding],
            documents=[event_summary],
            metadatas=[metadata] if metadata else [{}]
        )
        
    def search(self, query, top_k=5):
        """Search the index for relevant events based on a natural language query."""
        # Note: task_type="retrieval_query" is optimal for the search query
        result = self.client.models.embed_content(
            model="text-embedding-004",
            contents=query,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY")
        )
        query_embedding = result.embeddings[0].values
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        return results

    def get_all_events(self):
        """Retrieve all events for analytics."""
        return self.collection.get()
        
    def clear_all(self):
        """Clear all events from ChromaDB collection."""
        try:
            items = self.collection.get()
            if items and items['ids']:
                self.collection.delete(ids=items['ids'])
        except Exception as e:
            print(f"Failed to clear chroma db: {e}")

    def search_by_person(self, person_id):
        """Search the index for events involving a specific person_id."""
        results = self.collection.get(
            where={"person_id": person_id}
        )
        return results

if __name__ == "__main__":
    print("Cloud Embeddings module loaded.")
