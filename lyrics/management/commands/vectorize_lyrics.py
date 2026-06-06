import os
import re
import uuid
from django.core.management.base import BaseCommand
from lyrics.models import Song
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

class Command(BaseCommand):
    help = "Chunk, vectorize, and bulk upload lyrics to Qdrant with optional offset and limit."

    def add_arguments(self, parser):
        parser.add_argument(
            '--offset',
            type=int,
            default=0,
            help='Number of songs to skip from the start.'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Maximum number of songs to process.'
        )

    def handle(self, *args, **options):
        offset = options['offset']
        limit = options['limit']

        qdrant_host = os.environ.get("QDRANT_HOST", "localhost")
        client = QdrantClient(url=f"http://{qdrant_host}:6333")
        model = SentenceTransformer('all-MiniLM-L6-v2')

        if not client.collection_exists("lyrics_collection"):
            client.create_collection(
                collection_name="lyrics_collection",
                vectors_config=VectorParams(size=384, distance=Distance.COSINE)
            )
            
        songs_query = Song.objects.all()
        db_total = songs_query.count()

        if offset > 0:
            songs_query = songs_query[offset:]

        if limit is not None:
            songs_query = songs_query[:limit]

        songs = list(songs_query)
        total_to_process = len(songs)
        
        if total_to_process == 0:
            self.stdout.write(self.style.WARNING("No songs found matching the given offset/limit criteria."))
            return

        self.stdout.write(self.style.MIGRATE_LABEL(
            f"Starting vectorization. Total in DB: {db_total} | Processing: {total_to_process} (Offset: {offset}, Limit: {limit})..."
        ))

        points_batch = []
        total_chunks_uploaded = 0
        batch_size = 100

        for index, song in enumerate(songs, start=1):
            if index % 10 == 0 or index == total_to_process:
                global_index = offset + index
                self.stdout.write(
                    f"Processing song {index}/{total_to_process} [DB Global: {global_index}/{db_total}]: {song.title} ({song.artist})..."
                )

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
                
                points_batch.append(
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            "title": song.title,
                            "artist": song.artist,
                            "lyrics": full_chunk_text
                        }
                    )
                )
                
                if len(points_batch) >= batch_size:
                    client.upsert(collection_name="lyrics_collection", points=points_batch)
                    total_chunks_uploaded += len(points_batch)
                    points_batch = []

        if points_batch:
            client.upsert(collection_name="lyrics_collection", points=points_batch)
            total_chunks_uploaded += len(points_batch)
                
        self.stdout.write(self.style.SUCCESS(
            f"\n[SUCCESS] Successfully chunked, vectorized and batch-uploaded {total_chunks_uploaded} segments from {total_to_process} songs to Qdrant!"
        ))