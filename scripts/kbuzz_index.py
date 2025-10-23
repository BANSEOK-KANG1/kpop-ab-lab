import os, argparse, math
import pandas as pd
from datetime import datetime, timedelta
from src.yt import channel_videos
from src.wiki import pageviews_daily
from src.lastfm import artist_info
from src.io_cache import save_csv, ensure_dir

def zscore(s):
    s = pd.Series(s, dtype=float)
    mu, sigma = s.mean(), s.std(ddof=0)
    if sigma == 0 or pd.isna(sigma):
        return s*0
    return (s - mu) / sigma

def main(days: int, out: str, artists_csv: str):
    YT = os.getenv("YOUTUBE_API_KEY", "")
    LFM = os.getenv("LASTFM_API_KEY", "")
    if not YT:
        raise SystemExit("Env YOUTUBE_API_KEY required")
    if not LFM:
        print("WARN: LASTFM_API_KEY missing — Last.fm 신호 없이 진행")

    artists = pd.read_csv(artists_csv)
    rows = []
    end = datetime.utcnow().date()
    start = end - timedelta(days=days)
    for _, r in artists.iterrows():
        artist = r["artist"]
        wiki = r["wikipedia_article"]
        ch = r["youtube_channel_id"]
        # YouTube: 최근 동영상 합계
        yt_items = channel_videos(YT, ch, max_results=10)
        yt_views = sum([it.get("viewCount", 0) for it in yt_items])
        # Wikimedia: 최근 일자 평균 뷰
        pv = pageviews_daily(wiki, start.strftime("%Y%m%d"), end.strftime("%Y%m%d"))
        wiki_mean = float(pv["views"].mean()) if not pv.empty else 0.0
        # Last.fm: 팬심(리스너/플레이) 지표
        lfm_listeners = lfm_playcount = 0.0
        if LFM:
            try:
                info = artist_info(artist, LFM)
                a = info.get("artist", {})
                stats = a.get("stats", {})
                lfm_listeners = float(stats.get("listeners", 0))
                lfm_playcount = float(stats.get("playcount", 0))
            except Exception as e:
                pass
        rows.append({
            "artist": artist,
            "yt_views_sum": yt_views,
            "wiki_views_mean": wiki_mean,
            "lfm_listeners": lfm_listeners,
            "lfm_playcount": lfm_playcount
        })
    df = pd.DataFrame(rows)
    # 정규화 및 가중합
    for col in ["yt_views_sum", "wiki_views_mean", "lfm_listeners"]:
        df[col+"_z"] = zscore(df[col])
    # 가중치(임의): YouTube 0.5, Wikipedia 0.3, Last.fm 0.2
    df["kbuzz_index"] = 0.5*df["yt_views_sum_z"] + 0.3*df["wiki_views_mean_z"] + 0.2*df["lfm_listeners_z"]
    df = df.sort_values("kbuzz_index", ascending=False)
    ensure_dir(os.path.dirname(out))
    save_csv(df, out, index=False)

    # 간단 보고서
    top = df[["artist","kbuzz_index"]].head(10)
    report = ["# K-Buzz Index 결과 (상위 10)\n"]
    for i, row in top.reset_index(drop=True).iterrows():
        report.append(f"{i+1}. {row['artist']}: {row['kbuzz_index']:.2f}")
    with open("reports/RESULTS.md", "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print("Saved:", out, "and reports/RESULTS.md")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--artists_csv", type=str, default="data/artists.sample.csv")
    ap.add_argument("--out", type=str, default=f"data/kbuzz_{pd.Timestamp.today().date()}.csv")
    args = ap.parse_args()
    main(args.days, args.out, args.artists_csv)
