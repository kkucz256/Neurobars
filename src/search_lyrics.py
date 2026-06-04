from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

client = QdrantClient(url="http://localhost:6333")
model = SentenceTransformer("all-MiniLM-L6-v2")


def search_similar_songs(query_text, limit=1):
    query_vector = model.encode(query_text).tolist()

    response = client.query_points(
        collection_name="lyrics_collection", query=query_vector, limit=limit
    )
    return response.points


if __name__ == "__main__":
    test_query = "Loving kanye"

    print(f"Searching for: '{test_query}'...")
    points = search_similar_songs(test_query, limit=1)

    for point in points:
        print(f"\n[MATCH FOUND] Score: {point.score:.4f}")
        print(f"Title: {point.payload['title']} by {point.payload['artist']}")
        print("-" * 50)
        print(f"Lyrics snippet:\n{point.payload['lyrics'][:200]}...")
        print("-" * 50)