from ninja import NinjaAPI, Schema
from django.apps import apps
from lyrics.models import Song
from qdrant_client import QdrantClient
from django.db.models import Count
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, MatchText
from .src.llm_service import ask_llm_rag, generate_qdrant_query, generate_lyrics_in_style, generate_quiz_riddle, ask_llm_without_context, validate_hiphop_intent
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
    if not query.strip():
        return {"answer": "No query provided.", "optimized_query": "", "query": "", "sources": []}
    
    if not validate_hiphop_intent(query):
        return {
            "answer": "Error: Your query was rejected by Neurobars Guardrail. We only process questions related to hip-hop music and culture.",
            "optimized_query": "BLOCKED",
            "query": query,
            "sources": []
        }

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

    if context_chunks:
        full_context = "\n\n".join(context_chunks)
        ai_answer = ask_llm_rag(context_lyrics=full_context, user_question=query)
    else:
        ai_answer = (
            "[NOTE: The following answer is generated from general AI knowledge. "
            "Neurobars database does not contain local lyrics for this query yet.]\n\n"
            + ask_llm_without_context(user_question=query)
        )

    return {
        "answer": ai_answer,
        "optimized_query": optimized_query,
        "query": query,
        "sources": results,
    }


@api.get("/search", response=list[SourceSchema])
def search_lyrics_api(request, query: str, limit: int = LIMIT):
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
    artist_input = artist.strip()

    artist_filter = Filter(
        must=[FieldCondition(key="artist", match=MatchValue(value=artist_input))]
    )

    embedding_model = apps.get_app_config("lyrics").embedding_model
    topic_vector = embedding_model.encode(topic).tolist()

    response = client.query_points(
        collection_name="lyrics_collection",
        query=topic_vector,
        query_filter=artist_filter,
        limit=20
    )

    points_list = list(response.points)
    
    if len(points_list) < 20 and len(points_list) > 0:
        needed_scraps = 20 - len(points_list)
        
        embedding_dim = len(topic_vector)
        dummy_vector = [0.0] * embedding_dim
        
        fallback_response = client.query_points(
            collection_name="lyrics_collection",
            query=dummy_vector,
            query_filter=artist_filter,
            limit=50  
        )
        
        existing_ids = {p.id for p in points_list}
        additional_points = [p for p in fallback_response.points if p.id not in existing_ids]
        
        if additional_points:
            random.shuffle(additional_points)
            points_list.extend(additional_points[:needed_scraps])

    references = []
    style_chunks = []

    for point in points_list:
        lyrics_text = point.payload["lyrics"]
        title = point.payload["title"]
        actual_artist = point.payload["artist"]
        
        references.append({
            "points": point.score if point.score is not None else 0.0,
            "artist": actual_artist,
            "title": title,
            "lyrics": lyrics_text[:200] + "..."
        })
        style_chunks.append(f"Track: {title}\nLyrics:\n{lyrics_text}\n---")

    if points_list:
        style_context = "\n\n".join(style_chunks)
        new_lyrics = generate_lyrics_in_style(artist_name=artist_input, topic=topic, style_context=style_context)
    else:
        style_context = "NO LOCAL CONTEXT AVAILABLE. Use your pre-trained knowledge about this artist's real-world style."
        new_lyrics = f"[GENERATED FROM AI KNOWLEDGE - NOT IN LOCAL DATABASE]\n\n" + generate_lyrics_in_style(
            artist_name=artist_input, topic=topic, style_context=style_context
        )

    return {
        "artist": artist_input,
        "topic": topic,
        "generated_lyrics": new_lyrics,
        "used_references": references
    }
    
@api.get("/quiz-game", response=QuizResponseSchema)
def quiz_game_endpoint(request):
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
    
@api.get("/artists", response=list[str])
def get_all_artists(request):
    artists = list(
        Song.objects.values('artist')
        .annotate(total_songs=Count('id'))
        .filter(total_songs__gt=10)
        .order_by('artist')
        .values_list('artist', flat=True)
    )
    return artists