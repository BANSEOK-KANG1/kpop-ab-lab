import os, random, time, uuid
import pandas as pd
import streamlit as st
from src.features import make_pair
from src.io_cache import save_csv, ensure_dir

st.set_page_config(page_title="K-POP Headline A/B", page_icon="🎶", layout="centered")

st.title("K-POP 헤드라인 프레이밍 A/B 테스트")
st.write("감정형 vs 정보형 헤드라인의 클릭률·체류시간을 비교합니다.")

DATA = "data/news_links.sample.csv"
LOG_DIR = "data/logs"
ensure_dir(LOG_DIR)

@st.cache_data
def load_links(path=DATA):
    return pd.read_csv(path)

links = load_links()
if links.empty:
    st.warning("news_links.sample.csv에 링크를 추가하세요.")
    st.stop()

sid = st.session_state.get("sid")
if not sid:
    st.session_state["sid"] = sid = str(uuid.uuid4())

row = links.sample(1, random_state=random.randint(0,10**6)).iloc[0]
title, url = row["title"], row["url"]

pair = make_pair(title)
variant = random.choice(["A","B"])

headline = pair.emotional if variant=="A" else pair.factual
st.subheader(headline)

start = time.time()
clicked = st.link_button("기사 보러가기", url)
end = time.time()
dwell_ms = int((end-start)*1000)

# 로그
log = pd.DataFrame([{
    "sid": sid,
    "ts": pd.Timestamp.utcnow().isoformat()+"Z",
    "variant": variant,
    "title": title,
    "url": url,
    "impression": 1,
    "click": int(clicked),
    "dwell_ms": dwell_ms,
    "position": 1
}])

fname = os.path.join(LOG_DIR, f"ab_headline_{pd.Timestamp.utcnow().date()}.csv")
if os.path.exists(fname):
    log.to_csv(fname, mode="a", header=False, index=False)
else:
    log.to_csv(fname, index=False)

st.success("노출이 기록되었습니다. 좌측 메뉴에서 새로고침해 다양한 샘플을 더 수집하세요.")
st.caption("로그는 data/logs/ab_headline_YYYY-MM-DD.csv에 누적 저장됩니다.")
