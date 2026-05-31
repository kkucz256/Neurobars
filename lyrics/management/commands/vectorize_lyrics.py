from django.core.management.base import BaseCommand
from lyrics.models import Song
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

class Command(BaseCommand):
    def handle(self, *args, **options):
        client = QdrantClient(url="http://localhost:6333")
        model = SentenceTransformer('all-MiniLM-L6-v2')

        if not client.collection_exists("lyrics_collection"):
            client.create_collection(
                collection_name="lyrics_collection",
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            
        songs = Song.objects.all()

        for song in songs:
            lyrics = song.lyrics
            embedding = model.encode(lyrics).tolist()
            
            point = PointStruct(
                id=song.id,
                vector=embedding,
                payload={
                    "title": song.title,
                    "artist": song.artist,
                    "lyrics": song.lyrics
                }
            )
            
            client.upsert(collection_name="lyrics_collection", points=[point])
        self.stdout.write(self.style.SUCCESS(f"Successfully vectorized and uploaded {len(songs)} songs to Qdrant!"))