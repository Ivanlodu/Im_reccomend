import os
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
import httpx
from dotenv import load_dotenv
from pkce import generate_code_verifier, generate_code_challenge

load_dotenv()
app = FastAPI()

CLIENT_ID = os.getenv("Client ID")
REDIRECT_URI = os.getenv("Redirect URI")
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

    return token_response.json()