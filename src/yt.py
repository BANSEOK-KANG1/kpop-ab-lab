import os
from typing import List, Dict
import googleapiclient.discovery

def _yt(api_key: str):
    return googleapiclient.discovery.build("youtube", "v3", developerKey=api_key, cache_discovery=False)

def channel_videos(api_key: str, channel_id: str, max_results: int = 20) -> List[Dict]:
    yt = _yt(api_key)
    res = yt.search().list(part="id,snippet", channelId=channel_id, maxResults=max_results, order="date", type="video").execute()
    items = res.get("items", [])
    vids = [it["id"]["videoId"] for it in items if it.get("id", {}).get("videoId")]
    return video_stats(api_key, vids)

def video_stats(api_key: str, video_ids: List[str]) -> List[Dict]:
    if not video_ids:
        return []
    yt = _yt(api_key)
    batched = []
    for i in range(0, len(video_ids), 50):
        part = video_ids[i:i+50]
        res = yt.videos().list(part="statistics,snippet", id=",".join(part)).execute()
        for it in res.get("items", []):
            s = it.get("statistics", {})
            sn = it.get("snippet", {})
            batched.append({
                "videoId": it.get("id"),
                "publishedAt": sn.get("publishedAt"),
                "title": sn.get("title"),
                "viewCount": int(s.get("viewCount", 0)),
                "likeCount": int(s.get("likeCount", 0)),
                "commentCount": int(s.get("commentCount", 0))
            })
    return batched
