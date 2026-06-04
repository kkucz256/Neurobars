from ninja import NinjaAPI, Schema
from django.apps import apps
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from .src.llm_service import ask_llm_rag, generate_qdrant_query, generate_lyrics_in_style, generate_quiz_riddle
import random
import os

api = NinjaAPI(title="Neurobars API", version="1.0.0")
LIMIT = 3

qdrant_host = os.environ.get("QDRANT_HOST", "localhost")
client = QdrantClient(url=f"http://{qdrant_host}:6333")

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
    
class GeneratorResponseSchema(Schema):
    artist: str
    topic: str
    generated_lyrics: str
    used_references: list[SourceSchema]
    
class QuizResponseSchema(Schema):
    riddle: str
    options: list[str]
    correct_answer: str
    raw_lyrics_hint: str


@api.get("/search-and-process", response=RagResponseSchema)
def search_and_process_lyrics_api(request, query: str, limit: int = LIMIT):
    """
    User asks a question -> LLM optimizes query -> Qdrant searches -> LLM generates final response.
    """
    if not query.strip():
        return {"answer": "No query provided.", "optimized_query": "", "query": "", "sources": []}

    results = []
    
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

@api.get("/generate-bars", response=GeneratorResponseSchema)
def generate_bars_endpoint(request, artist: str, topic: str):
    """
    Few-shot generation: Fetches real lyrics of an artist from Qdrant and uses them to generate a new verse on a custom topic.
    """
    
    artist_filter = Filter(
        must=[
            FieldCondition(
                key="artist",
                match=MatchValue(value=artist)
            )
        ]
    )

    embedding_dim = len(apps.get_app_config("lyrics").embedding_model.encode("test"))
    dummy_vector = [0.0] * embedding_dim

    response = client.query_points(
        collection_name="lyrics_collection",
        query=dummy_vector,
        query_filter=artist_filter,
        limit=5
    )

    if not response.points:
        return {
            "artist": artist,
            "topic": topic,
            "generated_lyrics": f"Could not find any tracks by '{artist}' in the database to learn their style.",
            "used_references": []
        }

    references = []
    style_chunks = []

    for point in response.points:
        lyrics_text = point.payload["lyrics"]
        title = point.payload["title"]
        
        references.append({
            "points": point.score,
            "artist": artist,
            "title": title,
            "lyrics": lyrics_text[:200] + "..."
        })
        style_chunks.append(f"Track: {title}\nLyrics:\n{lyrics_text}\n---")

    style_context = "\n\n".join(style_chunks)
    
    new_lyrics = generate_lyrics_in_style(artist_name=artist, topic=topic, style_context=style_context)

    return {
        "artist": artist,
        "topic": topic,
        "generated_lyrics": new_lyrics,
        "used_references": references
    }
    
@api.get("/quiz-game", response=QuizResponseSchema)
def quiz_game_endpoint(request):
    """
    Fetches a random song chunk from Qdrant, uses LLM to generate a riddle, 
    and returns a 4-option multiple choice question for the frontend game.
    """
    
    random_offset = random.randint(0, 50)
    
    records, _ = client.scroll(
        collection_name="lyrics_collection",
        limit=10,
        with_payload=True,
        with_vectors=False
    )
    
    if not records:
        return {
            "riddle": "No lyrics found in the database to start the game.",
            "options": [],
            "correct_answer": "",
            "raw_lyrics_hint": ""
        }
        
    target_record = random.choice(records)
    
    correct_artist = target_record.payload["artist"]
    raw_lyrics = target_record.payload["lyrics"]
    
    riddle_text = generate_quiz_riddle(raw_lyrics)
    
    all_artists = set(rec.payload["artist"] for rec in records if rec.payload["artist"] != correct_artist)
    
    backup_artists = ["Kanye West", "Kendrick Lamar", "Drake", "Travis Scott", "Eminem", "Jay-Z"]
    while len(all_artists) < 3:
        all_artists.add(random.choice(backup_artists))
        
    wrong_options = random.sample(list(all_artists), 3)
    
    options_pool = wrong_options + [correct_artist]
    random.shuffle(options_pool)
    
    return {
        "riddle": riddle_text,
        "options": options_pool,
        "correct_answer": correct_artist,
        "raw_lyrics_hint": raw_lyrics[:300] + "..."
    }    