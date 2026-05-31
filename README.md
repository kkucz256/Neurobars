# NeuroBars Backend

Lyrics ingestion and semantic search RAG pipeline built with Django and Qdrant.

# Setup Instructions

### Environment & Dependencies
Make sure your virtual environment is active, then install all required packages:
```bash
pip install -r requirements.txt
```
### Infrastructure (Docker)
To spin up the Qdrant vector database local instance with persistence and Web Dashboard:
```bash
docker run -d -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant
```
Qdrant Web UI Dashboard: http://localhost:6333/dashboard
### Database Migrations
If you modified the database models, apply migrations to keep SQLite in sync:
```bash
python manage.py makemigrations
python manage.py migrate
```
### Management Commands (Data Pipeline)
#### Fetch Lyrics
Fetches, cleans, and saves lyrics directly from the Genius API into the SQLite database.
Arguments: artist_name (string), --pages (integer, default=1, 1 page = 10 songs)

```bash
# Standard fetch (10 songs)
python manage.py fetch_lyrics "Kendrick Lamar"
```

#### Deep fetch (x*10 songs)
```bash
python manage.py fetch_lyrics "Kanye West" --pages x
```
#### Vectorize Lyrics
Pulls all tracks from SQLite, generates dense vector embeddings (384-dimensional) using a local all-MiniLM-L6-v2 model, and inserts them into the Qdrant vector database.
Make sure your Qdrant Docker container is running before executing this command!
```bash
python manage.py vectorize_lyrics
```
