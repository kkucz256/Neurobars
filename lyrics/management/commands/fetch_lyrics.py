import os
import re
import requests
import random
import time
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
from lyrics.models import Song

load_dotenv()

GENIUS_ACCESS_TOKEN = os.getenv("GENIUS_ACCESS_TOKEN")
API_URL = "https://api.genius.com"


class Command(BaseCommand):
    help = "Fetch lyrics for multiple artists from Genius API, clean them, and save to SQLite."

    def add_arguments(self, parser):
        parser.add_argument("artists", type=str, nargs="+", help="List of artist names separated by spaces")
        parser.add_argument(
            "--pages",
            type=int,
            default=1,
            help="Number of API pages to fetch per artist (1 page = 10 songs)",
        )

    def fetch_genius_search_results(self, artist_name, page=1):
        headers = {"Authorization": f"Bearer {GENIUS_ACCESS_TOKEN}"}
        params = {"q": artist_name, "page": page, "per_page": 10}
        response = requests.get(
            f"{API_URL}/search", headers=headers, params=params
        ).json()
        return response["response"]["hits"]

    def scrape_lyrics_from_url(self, song_url):
        request = requests.get(song_url).text
        soup = BeautifulSoup(request, "html.parser")

        lyrics_div = soup.find_all(
            "div",
            class_=lambda class_name: self.check_if_contains_container(
                class_name, "Lyrics__Container"
            ),
        )
        headers_tag = soup.find(
            "div",
            class_=lambda class_name: self.check_if_contains_container(
                class_name, "LyricsHeader__Container"
            ),
        )
        if headers_tag:
            headers_tag.decompose()

        final_lyrics = ""
        for element in lyrics_div:
            final_lyrics += element.get_text(separator="\n") + "\n"

        text = final_lyrics.replace("\u205f", " ")
        text = re.sub(r"\[([^\]]*?)\n([^\]]*?)\]", r"[\1 \2]", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" +", " ", text)
        clean_lyrics = text.strip()
        return clean_lyrics if clean_lyrics else "Lyrics not found."

    def check_if_contains_container(self, class_name, name):
        classes = str(class_name).split()
        if class_name is not None and any(name in cls for cls in classes):
            return True
        return False

    def handle(self, *args, **options):
        artist_list = options["artists"]
        max_pages = options["pages"]

        self.stdout.write(
            self.style.MIGRATE_LABEL(
                f"Starting bulk fetch pipeline for {len(artist_list)} artists. Pages per artist: {max_pages}."
            )
        )

        global_added = 0
        global_updated = 0

        for artist in artist_list:
            self.stdout.write(self.style.MIGRATE_LABEL(f"\n==================== PROCESSING: {artist} ===================="))
            
            for page in range(1, max_pages + 1):
                self.stdout.write(f"--- {artist}: Fetching page {page} of {max_pages} ---")
                search_results = self.fetch_genius_search_results(artist, page=page)

                if not search_results:
                    self.stdout.write(f"No more results found for {artist} on Genius API.")
                    break

                for song in search_results:
                    title = song["result"]["title"]
                    url = song["result"]["url"]
                    actual_artist = song["result"]["primary_artist"]["name"]
                    
                    delay = random.uniform(1.5, 3.5)
                    self.stdout.write(f"Sleeping for {delay:.2f}s to prevent rate limiting...")
                    time.sleep(delay)

                    self.stdout.write(f"Scraping lyrics for: {title}...")
                    lyrics = self.scrape_lyrics_from_url(url)

                    if lyrics and lyrics != "Lyrics not found.":
                        song_obj, created = Song.objects.update_or_create(
                            title=title, artist=actual_artist, defaults={"lyrics": lyrics}
                        )

                        if created:
                            self.stdout.write(self.style.SUCCESS(f"Successfully ADDED: {title} ({actual_artist})"))
                            global_added += 1
                        else:
                            self.stdout.write(self.style.WARNING(f"Successfully UPDATED: {title} ({actual_artist})"))
                            global_updated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n[BULK PIPELINE FINISHED] Total Added: {global_added}, Total Updated: {global_updated}."
            )
        )