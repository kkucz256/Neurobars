from django.apps import AppConfig
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer



class LyricsConfig(AppConfig):
    name = "lyrics"
    embedding_model = None
    def ready(self):
        self.__class__.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
