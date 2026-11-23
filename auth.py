import os
import secrets

from fastapi import Header, HTTPException
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")


def verify_api_key(
    x_api_key: str = Header(default=None)
):

    if not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="API key missing"
        )

    if not API_KEY:
        raise HTTPException(
            status_code=503,
            detail="API key is not configured"
        )

    if not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )

    return True