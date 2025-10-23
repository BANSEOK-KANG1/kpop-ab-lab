import requests
import pandas as pd
from urllib.parse import quote

def pageviews_daily(article: str, start: str, end: str, project: str = "en.wikipedia") -> pd.DataFrame:
    # start, end: YYYYMMDD
    encoded = quote(article.replace(" ", "_"), safe="")
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{project}/all-access/all-agents/{encoded}/daily/{start}/{end}"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    j = r.json()
    rows = []
    for it in j.get("items", []):
        rows.append({
            "date": it["timestamp"][:8],
            "views": it["views"]
        })
    return pd.DataFrame(rows)
