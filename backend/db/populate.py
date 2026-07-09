import httpx
from .database import SessionLocal
from .models import User, Track, Artist, ListenEvent
from datetime import datetime, timedelta

async def save_user(access_token: str, refresh_token: str, expires_in: int):
    async with httpx.AsyncClient() as client:
        profile_response = await client.get(
            "https://api.spotify.com/v1/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    if profile_response.status_code != 200:
        raise ValueError(f"Spotify profile request failed: {profile_response.status_code} {profile_response.text}")

    profile_data = profile_response.json()
    spotify_id = profile_data.get("id")
    display_name = profile_data.get("display_name")
    email = profile_data.get("email")
    token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    db = SessionLocal()

    existing_user = db.query(User).filter(User.spotify_id == spotify_id).first()

    if existing_user:
        # User already exists — update their tokens instead of creating a duplicate
        existing_user.access_token = access_token
        existing_user.refresh_token = refresh_token
        existing_user.token_expires_at = token_expires_at
        existing_user.display_name = display_name
        existing_user.email = email
        db.commit()
        db.refresh(existing_user)
        db.close()
        return existing_user
    else:
        new_user = User(
            spotify_id=spotify_id,
            display_name=display_name,
            email=email,
            access_token=access_token,
            refresh_token=refresh_token,
            token_expires_at=token_expires_at
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        db.close()
        return new_user

async def fetch_saved_tracks(access_token: str):
    all_tracks = []
    offset = 0
    limit = 50

    async with httpx.AsyncClient(timeout=15.0) as client:
        while True:
            print(f"Fetching offset {offset}...")
            response = await client.get(
                "https://api.spotify.com/v1/me/tracks",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"limit": limit, "offset": offset},
            )
            data = response.json()
            items = data.get("items", [])

            if not items:
                break

            all_tracks.extend(items)
            offset += limit

    return all_tracks  # raw, unextracted

def extract_track_data(all_tracks):
    extracted = []

    for item in all_tracks:
        track = item.get('track')
        if not track:
            continue

        album = track.get('album')
        artists = track.get('artists')

        if not album or not artists:
            continue

        extracted.append({
            "track_id": track['id'],
            "track_name": track['name'],
            "album_name": album['name'],
            "release_date": album['release_date'],
            "artist_id": artists[0]['id'],
            "artist_name": artists[0]['name'],
            "added_at": item.get('added_at'),  # new field, from the outer item
        })

    return extracted

def save_tracks(extracted_tracks):
    db = SessionLocal()

    for t in extracted_tracks:
        # --- Artist: check first, create if missing ---
        existing_artist = db.query(Artist).filter(
            Artist.spotify_id == t["artist_id"]
        ).first()

        if existing_artist:
            artist = existing_artist
        else:
            artist = Artist(
                spotify_id=t["artist_id"],
                name=t["artist_name"]
            )
            db.add(artist)
            db.commit()
            db.refresh(artist)

        # --- Track: check first, create if missing ---
        existing_track = db.query(Track).filter(
            Track.spotify_id == t["track_id"]
        ).first()

        if existing_track:
            continue  # already saved, skip

        new_track = Track(
            spotify_id=t["track_id"],
            name=t["track_name"],
            artist_id=artist.id,       # FK to Artist's internal id
            album=t["album_name"],
            release_date=t["release_date"]  # stored as string now
        )
        db.add(new_track)
        db.commit()

    db.close()

def save_listen_events(extracted_tracks, user_id):
    db = SessionLocal()

    for t in extracted_tracks:
        # Need the Track's internal id, not its spotify_id, for the FK
        track = db.query(Track).filter(Track.spotify_id == t["track_id"]).first()

        if not track:
            continue  # track wasn't saved for some reason, skip

        listened_at = None
        if t.get("added_at"):
            # Spotify format: "2023-05-01T12:34:56Z"
            listened_at = datetime.strptime(t["added_at"], "%Y-%m-%dT%H:%M:%SZ")

        new_event = ListenEvent(
            user_id=user_id,
            track_id=track.id,
            listened_at=listened_at
        )
        db.add(new_event)

    db.commit()
    db.close()