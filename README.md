# NeuroBars

An advanced, decoupled hip-hop lyrics ingestion, semantic search RAG pipeline, and interactive AI gaming hub built with Django Ninja and Qdrant.

## Setup Instructions

### 1. Environment & Secrets Configuration
Before running the infrastructure, you must create a `.env` file in the root directory of the project (the same folder where `manage.py` and `docker-compose.yml` reside). This file injects API keys and configuration variables into the memory of your containers securely.

Create a file named `.env` and populate it with your tokens:

```env
GROQ_API_KEY=your_actual_groq_api_key_here
GENIUS_ACCESS_TOKEN=your_actual_genius_access_token_here
```

### 2. Infrastructure & Application Bootstrapping (Docker Compose)
```bash
docker-compose up --build
```
To shut down the infrastructure run:

```bash
docker-compose down
```

### 3. Accessing the System

Once the containers are running, you can access the following dashboards directly from your host browser:

* **Interactive API Documentation (Swagger UI):** [http://localhost:8000/api/docs](https://www.google.com/search?q=http://localhost:8000/api/docs)
* **Qdrant Web Console Dashboard:** [http://localhost:6333/dashboard](https://www.google.com/search?q=http://localhost:6333/dashboard)

---

## Data Pipeline & Management Commands

All Django management commands must be executed **inside** the running backend container. Keep your `docker-compose up` terminal running, open a new terminal window on your machine, and use the following commands.

### Fetch Lyrics

Fetches, cleans, and saves raw lyrics directly from the Genius API into the relational database.
*Arguments: `artist_name` (string), `--pages` (integer, default=1, where 1 page = 10 songs).*

```bash
# Standard fetch (10 songs)
docker-compose exec web python manage.py fetch_lyrics "Kendrick Lamar"

# Deep fetch (e.g., 50 songs)
docker-compose exec web python manage.py fetch_lyrics "Kanye West" --pages 5
```

### Vectorize Lyrics (Database Seeding)

Pulls all fetched tracks from the local database, generates dense vector embeddings (384-dimensional) using the embedded `all-MiniLM-L6-v2` model, and inserts them into the Qdrant vector database.

```bash
docker-compose exec web python manage.py vectorize_lyrics
```

---

## Available API Endpoints (Features)

The backend provides JSON API interface under the `/api/` prefix:

1. **`/api/search-and-process`**: A RAG implementation that uses an LLM to optimize user search criteria, queries Qdrant for semantic lyrics matches, and responds as a rap music expert.
2. **`/api/search`**: Pure semantic vector search retrieving raw matched verse chunks and mapping metadata scores without LLM synthesis.
3. **`/api/generate-bars`**: Few-shot generator that extracts authentic style examples for a specific artist from Qdrant and instructs the LLM to write a brand new 16-bar verse on a custom topic.
4. **`/api/quiz-game`**: A gamified endpoint that pulls random verse blocks from the database, processes them through the LLM into a cryptic riddle, and generates a multiple-choice guess-the-rapper game scheme.

```

```