"""
Phase 1, Step 6: Enrichment job.

Pulls a small batch of tracks (default 25) that don't yet have a
description, generates a rich text description for each via local
Ollama, and prints them for review. Nothing is written back to
Postgres yet -- run this repeatedly while you tune PROMPT_TEMPLATE,
then flip DRY_RUN to False once the outputs look good.

Assumes:
- `tracks` table: id, name, artist_id, album (nullable), description (nullable, text)
- `artists` table: id, name, genres (nullable, text[] or text)
- Postgres connection via env vars (DATABASE_URL) using psycopg
"""

import os
import time
import psycopg
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")  # e.g. postgresql://user:pass@localhost:5432/spotify
OLLAMA_MODEL = "llama3.1:8b"
BATCH_SIZE = 25
DRY_RUN = True  # set False once you're happy with the prompt, to write descriptions back

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

PROMPT_TEMPLATE = """You are a music critic writing short, vivid, sonically-specific descriptions of songs for a recommendation engine. The description will be embedded and used for semantic similarity search, so it must describe HOW the song sounds and FEELS, not just facts about it.

Track: "{track_name}"
Artist: {artist_name}
Album: {album}
Genres (if known): {genres}

Write a 2-3 sentence description covering:
- Sonic texture and production (e.g. "hazy autotuned vocals over a sparse trap beat", "warm analog synths with tape hiss")
- Mood/energy (e.g. "melancholic but danceable", "aggressive and claustrophobic")
- What kind of listening moment it fits (e.g. "late-night drive", "gym warmup", "rainy Sunday morning")

Avoid generic filler like "a great song" or "catchy tune". Be specific and sensory. Do not just restate the genre tag. Output ONLY the description, no preamble.
"""


def fetch_batch(conn, limit: int):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT t.id, t.name, t.album, a.name AS artist_name, a.genres
            FROM tracks t
            JOIN artists a ON a.id = t.artist_id
            WHERE t.description IS NULL
            LIMIT %s
            """,
            (limit,),
        )
        cols = [desc[0] for desc in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def generate_description(track: dict) -> str:
    prompt = PROMPT_TEMPLATE.format(
        track_name=track["name"],
        artist_name=track["artist_name"],
        album=track["album"] or "unknown",
        genres=track["genres"] or "unknown",
    )
    response = client.chat.completions.create(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
    )
    return response.choices[0].message.content.strip()


def write_description(conn, track_id, description: str):
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE tracks SET description = %s WHERE id = %s",
            (description, track_id),
        )
    conn.commit()


def main():
    with psycopg.connect(DATABASE_URL) as conn:
        batch = fetch_batch(conn, BATCH_SIZE)
        print(f"Pulled {len(batch)} tracks needing enrichment.\n")

        for i, track in enumerate(batch, 1):
            start = time.time()
            description = generate_description(track)
            elapsed = time.time() - start

            print(f"[{i}/{len(batch)}] {track['artist_name']} — {track['name']} ({elapsed:.1f}s)")
            print(f"  {description}\n")

            if not DRY_RUN:
                write_description(conn, track["id"], description)

        if DRY_RUN:
            print("DRY_RUN is True — nothing written to Postgres. Review outputs above, tune PROMPT_TEMPLATE, and re-run.")
        else:
            print("Descriptions written to Postgres.")


if __name__ == "__main__":
    main()