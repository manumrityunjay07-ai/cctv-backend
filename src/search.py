import os
from groq import Groq
from google import genai
from .embeddings import EventIndexer

class NLSearchEngine:
    def __init__(self, provider="groq"):
        self.provider = provider
        self.groq_client = None
        
        if provider == "groq":
            api_key = os.getenv("GROQ_API_KEY")
            if api_key and api_key != "your_groq_api_key_here":
                self.groq_client = Groq(api_key=api_key)
            else:
                print("Warning: Groq API key not set properly. Falling back to Gemini.")
                self.provider = "gemini"
                
        if self.provider == "gemini":
            api_key = os.getenv("GOOGLE_API_KEY")
            if api_key and api_key != "your_gemini_api_key_here":
                self.gemini_client = genai.Client(api_key=api_key)
            else:
                print("Warning: Gemini API key not set either. LLM features disabled.")
                self.provider = None

        self.indexer = EventIndexer()

    def parse_query(self, query):
        """
        Use LLM to extract intent and filters (e.g. time, duration, person, zone) 
        from the natural language query.
        For a hackathon, we can rely heavily on the semantic vector search, 
        but parsing helps for exact filters.
        """
        # Basic rule-based parsing for common filters
        filters = {}
        q = query.lower()

        # person id
        import re
        m = re.search(r"person\s+(\d+)", q)
        if m:
            filters['person_id'] = m.group(1)

        # duration like 'longer than 30 minutes'
        m = re.search(r"longer than (\d+)\s*(minutes|minute|min)", q)
        if m:
            mins = int(m.group(1))
            filters['min_duration_seconds'] = mins * 60

        m = re.search(r"more than (\d+)\s*(seconds|second|secs)", q)
        if m:
            filters['min_duration_seconds'] = int(m.group(1))

        # zones referenced by name - simple contains check
        # gather zone names if available
        zone_names = []
        try:
            from .zones import ZoneManager
            zm = ZoneManager()
            zone_names = list(zm.zones.keys())
        except Exception:
            zone_names = []

        for zn in zone_names:
            if zn.lower() in q:
                filters['zone_name'] = zn
                break

        return {"semantic_query": query, "filters": filters}

    def search_and_summarize(self, query, top_k=3):
        """
        End-to-end search:
        1. Parse query
        2. Vector search ChromaDB
        3. Generate summary of results using LLM
        """
        parsed = self.parse_query(query)
        
        # Vector search
        results = self.indexer.search(parsed["semantic_query"], top_k=top_k)
        
        documents = results['documents'][0] if results['documents'] else []
        metadatas = results['metadatas'][0] if results['metadatas'] else []
        ids = results['ids'][0] if results['ids'] else []
        
        if not documents:
            return "No relevant events found.", []

        # Apply simple metadata filters if provided
        filters = parsed.get('filters', {})
        filtered_ids = []
        filtered_docs = []
        filtered_metas = []
        for doc, meta, id_ in zip(documents, metadatas, ids):
            keep = True
            if filters.get('person_id') and str(meta.get('person_id')) != str(filters['person_id']):
                keep = False
            if filters.get('zone_name') and meta.get('zone_name') != filters['zone_name']:
                keep = False
            if filters.get('min_duration_seconds'):
                if float(meta.get('duration_seconds') or 0) < float(filters['min_duration_seconds']):
                    keep = False
            if keep:
                filtered_ids.append(id_)
                filtered_docs.append(doc)
                filtered_metas.append(meta)

        documents = filtered_docs
        metadatas = filtered_metas
        ids = filtered_ids

        if not documents:
            return "No events match the requested filters.", []
            
        # Group by person_id to return only one result per customer
        unique_persons = {}
        grouped_results = []
        for doc, meta, id_ in zip(documents, metadatas, ids):
            person_id = meta.get("person_id")
            if person_id not in unique_persons:
                unique_persons[person_id] = True
                grouped_results.append({
                    "id": id_,
                    "document": doc,
                    "metadata": meta
                })
            
        context = "\n".join([f"Event: {res['document']} (Customer ID: {res['metadata'].get('person_id')})" for res in grouped_results])
        
        prompt = f"""
        User Question: {query}
        Retrieved Video Events:
        {context}
        
        Based ONLY on the retrieved video events, provide a direct, conversational answer to the user's question. 
        Keep it concise (1-2 sentences). Do not mention that you are an AI or that you are looking at events.
        Just answer the question directly based on the evidence.
        """
        
        summary = self._call_llm(prompt)
            
        return summary, grouped_results

    def _call_llm(self, prompt):
        if self.provider == "groq":
            if self.groq_client is None:
                return "LLM integration unavailable. Groq client not initialized."
            try:
                chat_completion = self.groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a CCTV analysis assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    model="llama-3.1-8b-instant",
                )
                return chat_completion.choices[0].message.content
            except Exception as e:
                return f"Error connecting to Groq LLM: {str(e)}"
        elif self.provider == "gemini":
            try:
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=prompt
                )
                return response.text
            except Exception as e:
                return f"Error connecting to LLM: {str(e)}"
        else:
            return "LLM integration unavailable. Please set API keys."

if __name__ == "__main__":
    print("Search module loaded.")
