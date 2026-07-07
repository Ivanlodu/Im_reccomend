import httpx
from .database import SessionLocal
from .models import User
from datetime import datetime, timedelta

async def save_user(access_token:str, refresh_token:str, expires_in: int):
    async with httpx.AsyncClient() as client:
        profile_response = await client.get(
            "https://api.spotify.com/v1/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        profile_data = profile_response.json()
        spotify_id = profile_data.get("id")
        display_name = profile_data.get("display_name")
        email = profile_data.get("email")
        token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    db = SessionLocal()
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
    print(f"User {display_name} saved to the database.")
    return new_user