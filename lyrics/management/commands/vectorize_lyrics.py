from django.core.management.base import BaseCommand
from lyrics.models import Song
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import re
import uuid
import os

class Command(BaseCommand):
    def handle(self, *args, **options):
        qdrant_host = os.environ.get("QDRANT_HOST", "localhost")
        client = QdrantClient(url=f"http://{qdrant_host}:6333")
        model = SentenceTransformer('all-MiniLM-L6-v2')

        if not client.collection_exists("lyrics_collection"):
            client.create_collection(
                collection_name="lyrics_collection",
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            
        songs = Song.objects.all()

        total_chunks_uploaded = 0

        for song in songs:
            raw_chunks = re.split(r"(\[.*?\])", song.lyrics)
            
            current_header = ""

            for item in raw_chunks:
                cleaned_item = item.strip()
                
                if not cleaned_item:
                    continue
                    
                if cleaned_item.startswith("[") and cleaned_item.endswith("]"):
                    current_header = cleaned_item
                    continue
                
                full_chunk_text = f"{current_header}\n{cleaned_item}"
                
                embedding = model.encode(full_chunk_text).tolist()
                
                point_id = str(uuid.uuid4())
                
                point = PointStruct(
                    id=point_id,
                    vector=embedding,
                    payload={
                        "title": song.title,
                        "artist": song.artist,
                        "lyrics": full_chunk_text
                    }
                )
                
                client.upsert(collection_name="lyrics_collection", points=[point])
                total_chunks_uploaded += 1
                
        self.stdout.write(self.style.SUCCESS(
            f"Successfully chunked, vectorized and uploaded {total_chunks_uploaded} segments from {len(songs)} songs to Qdrant!"
        ))                          