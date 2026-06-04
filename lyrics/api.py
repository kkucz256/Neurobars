from ninja import NinjaAPI, Schema
from django.apps import apps
from .src.llm_service import ask_llm_rag, generate_qdrant_query

api = NinjaAPI(title="Neurobars API", version="1.0.0")
LIMIT = 3

class SourceSchema(Schema):
    points: float
    artist: str
    title: str
    lyrics: str

class RagResponseSchema(Schema):
    answer: str
    optimized_query: str
    query: str
    sources: list[SourceSchema]


@api.get("/search_and_process", response=RagResponseSchema)
def search_and_process_lyrics_api(request, query: str, limit: int = LIMIT):
    """
    User asks a question -> LLM optimizes query -> Qdrant searches -> LLM generates final response.
    """
    if not query.strip():
        return {"answer": "No query provided.", "optimized_query": "", "query": "", "sources": []}

    results = []
    client = apps.get_app_config("lyrics").qdrant_client
    
    optimized_query = generate_qdrant_query(query)
    
    query_vector = apps.get_app_config("lyrics").embedding_model.encode(optimized_query).tolist()

    internal_limit = max(limit * 3, 20)
    response = client.query_points(
        collection_name="lyrics_collection", query=query_vector, limit=internal_limit
    )
    
    seen_lyrics = set()
    context_chunks = []

    for point in response.points:
        lyrics_text = point.payload["lyrics"]
        artist = point.payload["artist"]
        title = point.payload["title"]
        
        if lyrics_text in seen_lyrics:
            continue
            
        results.append({
            "points": point.score,
            "artist": artist,
            "title": title,
            "lyrics": lyrics_text[:500] + "..."
        })
        
        context_chunks.append(f"Track: '{title}' by {artist}\nLyrics snippet:\n{lyrics_text}\n---")
        seen_lyrics.add(lyrics_text)
        
        if len(results) == limit:
            break

    ai_answer = "No relevant context found to answer the question."
    if context_chunks:
        full_context = "\n\n".join(context_chunks)
        ai_answer = ask_llm_rag(context_lyrics=full_context, user_question=query)

    return {
        "answer": ai_answer,
        "optimized_query": optimized_query,
        "query": query,
        "sources": results,
    }


@api.get("/search", response=list[SourceSchema])
def search_lyrics_api(request, query: str, limit: int = LIMIT):
    """
    Pure vector search in Qdrant database. Returns matching chunks without LLM processing.
    """
    if not query.strip():
        return []

    results = []
    client = apps.get_app_config("lyrics").qdrant_client
    
    query_vector = apps.get_app_config("lyrics").embedding_model.encode(query).tolist()

    internal_limit = max(limit * 3, 20)
    response = client.query_points(
        collection_name="lyrics_collection", query=query_vector, limit=internal_limit
    )
    
    seen_lyrics = set()

    for point in response.points:
        lyrics_text = point.payload["lyrics"]
        
        if lyrics_text in seen_lyrics:
            continue
            
        results.append({
            "points": point.score,
            "artist": point.payload["artist"],
            "title": point.payload["title"],
            "lyrics": lyrics_text
        })
        
        seen_lyrics.add(lyrics_text)
        
        if len(results) == limit:
            break

    return results