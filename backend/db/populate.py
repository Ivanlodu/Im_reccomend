import httpx
from .database import SessionLocal
from .models import User
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

async def fetch_saved_tracks(access_token:str):
    all_tracks = []
    offset = 0
    limit = 50

    async with httpx.AsyncClient() as client:
        while True:
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

    return all_tracks
