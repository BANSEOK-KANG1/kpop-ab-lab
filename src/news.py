# src/news.py
import yaml
import feedparser
import hashlib
import pandas as pd

def fetch_rss_pool(yaml_path: str) -> pd.DataFrame:
    """
    news_sources.yaml에 정의된 RSS 피드들을 긁어서
    기사 풀(DataFrame)을 만든다.
    반환 컬럼: id, title, url, domain
    """
    try:
        with open(yaml_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
    except FileNotFoundError:
        # yaml 자체가 없으면 빈 DF
        return pd.DataFrame(columns=["id","title","url","domain"])
    except Exception:
        # YAML 파싱 에러 등
        return pd.DataFrame(columns=["id","title","url","domain"])

    sources = cfg.get("sources", [])
    rows = []

    for src in sources:
        feed_url = src.get("url")
        domain = src.get("domain", "")
        if not feed_url:
            continue

        parsed = feedparser.parse(feed_url)

        # feedparser.parse() 실패 시 parsed.entries는 빈 리스트일 수도 있음
        for entry in parsed.get("entries", []):
            title = entry.get("title", "").strip()
            link  = entry.get("link", "").strip()

            if not title or not link:
                continue

            # 고유 ID: 링크 기반으로 해시
            uid = hashlib.md5(link.encode("utf-8")).hexdigest()[:12]

            rows.append({
                "id": uid,
                "title": title,
                "url": link,
                "domain": domain,
            })

    if not rows:
        return pd.DataFrame(columns=["id","title","url","domain"])

    df = pd.DataFrame(rows)

    # 중복 제거 (같은 링크 여러 RSS에 있을 수 있으니까)
    df = df.drop_duplicates(subset=["url"]).reset_index(drop=True)

    return df
