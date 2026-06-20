import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
# 'postmessage' is a special redirect URI value used when using the authorization code flow with JavaScript popups
REDIRECT_URI = "postmessage" 

class AuthRequest(BaseModel):
    code: str

@app.post("/api/auth/google")
async def auth_google(data: AuthRequest):
    # 1. Exchange the auth code for an access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": data.code,
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
        
    token_data = token_response.json()
    if "error" in token_data:
        raise HTTPException(status_code=400, detail=token_data.get("error_description"))

    access_token = token_data.get("access_token")

    # 2. Use the access token to fetch user data from Google
    async with httpx.AsyncClient() as client:
        user_info_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
    user_profile = user_info_response.json()
    
    # Return user information to the client side
    return {
        "email": user_profile.get("email"),
        "name": user_profile.get("name"),
        "picture": user_profile.get("picture"),
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main.py", host="0.0.0.0", port=8000, reload=True)