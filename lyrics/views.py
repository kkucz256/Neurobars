from django.shortcuts import render
from django.apps import apps
from django.http import JsonResponse

LIMIT = 1

def search_lyrics_api(request):
    results = []
    client = apps.get_app_config("lyrics").qdrant_client
    query = request.GET.get("query", "")
    if query.strip() == "":
        return JsonResponse({"results": "No query provided."})

    query_vector = apps.get_app_config("lyrics").embedding_model.encode(query).tolist()

    response = client.query_points(
        collection_name="lyrics_collection", query=query_vector, limit=LIMIT
    )
    for point in response.points:
        results.append({
            "points": point.score,
            "artist": point.payload["artist"],
            "title": point.payload["title"],
            "lyrics": point.payload["lyrics"][:200] + "..."
        })

    return JsonResponse({"results": results})