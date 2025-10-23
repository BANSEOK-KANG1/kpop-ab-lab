import os, requests

API_ROOT = "http://ws.audioscrobbler.com/2.0/"

def artist_info(artist: str, api_key: str) -> dict:
    params = {
        "method": "artist.getinfo",
        "artist": artist,
        "api_key": api_key,
        "format": "json"
    }
    r = requests.get(API_ROOT, params=params, timeout=30)
    r.raise_for_status()
    return r.json()
