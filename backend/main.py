import os
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
import httpx
from dotenv import load_dotenv
from pkce import generate_code_verifier, generate_code_challenge
from db.populate import extract_track_data, save_tracks, save_user, fetch_saved_tracks, save_listen_events
load_dotenv()
app = FastAPI()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
print("Loaded client ID:", CLIENT_ID)
print("Loaded redirect URI:", REDIRECT_URI)
SCOPE = "user-read-private user-read-email user-library-read"

pkce_store = {}
@app.get("/login")
def login():
    verifier = generate_code_verifier()
    challenge = generate_code_challenge(verifier)
    pkce_store["verifier"] = verifier

    auth_url = (
        "https://accounts.spotify.com/authorize"
        f"?client_id={CLIENT_ID}"
        "&response_type=code"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={SCOPE}"
        "&code_challenge_method=S256"
        f"&code_challenge={challenge}"
    )
    return RedirectResponse(auth_url)

@app.get("/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    verifier = pkce_store.get("verifier")

    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://accounts.spotify.com/api/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "client_id": CLIENT_ID,
                "code_verifier": verifier,
            },
        )
    token_data = token_response.json()
    print("Token data received:", token_data)
    user = await save_user(access_token=token_data["access_token"], refresh_token=token_data["refresh_token"], expires_in=token_data["expires_in"])
    raw_tracks = await fetch_saved_tracks(access_token=token_data["access_token"])
    extracted = extract_track_data(raw_tracks)
    save_tracks(extracted)
    save_listen_events(extracted, user.id)
    print("Final tracks returned:", raw_tracks)
    return {"message":"User saved tracks returned","spotify_id": user.spotify_id, "tracks": raw_tracks}
    