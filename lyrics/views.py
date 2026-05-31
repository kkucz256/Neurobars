from django.shortcuts import render
from django.apps import apps
from django.http import JsonResponse

LIMIT = 1

def search_lyrics_api(request):
    results = []
    client = apps.get_app_config("lyrics").qdrant_client
    query = request.GET.get("query", "")
    
    try:
        limit = int(request.GET.get("limit", LIMIT))
    except ValueError:
        limit = LIMIT

    if query.strip() == "":
        return JsonResponse({"results": "No query provided."})

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

    return JsonResponse({"results": results})