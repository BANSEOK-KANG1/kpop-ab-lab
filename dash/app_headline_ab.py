# ============================================
# K-POP Headline A/B (RSS 다카드 + 로그/요약)
# ============================================
# 목표:
# - 실제 K-POP/연예 뉴스 헤드라인을 RSS로 모은 뒤
# - 감정형(A) vs 정보형(B) 헤드라인을 카드 형태로 섞어서 노출
# - 사용자의 클릭을 variant 단위로 로깅
# - CTR(클릭률), 평균 체류시간 유사 지표(dwell_ms) 등 비교
#
# 이 파일은 Streamlit Cloud에서 바로 돌아갈 수 있도록
# 경로 처리와 fallback(폴백)까지 포함한다.

# ---------------------------
# 경로 세팅 (어디서 실행돼도 동작하도록)
# ---------------------------
import sys, os

THIS_FILE_DIR = os.path.dirname(os.path.abspath(__file__))          # .../kpop-ab-lab/dash
REPO_ROOT     = os.path.abspath(os.path.join(THIS_FILE_DIR, ".."))  # .../kpop-ab-lab
SRC_DIR       = os.path.join(REPO_ROOT, "src")                      # .../kpop-ab-lab/src
DATA_DIR      = os.path.join(REPO_ROOT, "data")
LOG_DIR       = os.path.join(DATA_DIR, "logs")

for path_candidate in [THIS_FILE_DIR, REPO_ROOT, SRC_DIR]:
    if path_candidate not in sys.path:
        sys.path.insert(0, path_candidate)

import random, uuid, time
import pandas as pd
import streamlit as st

# ---------------------------
# src 모듈 import 시도
# 실패하면 fallback 정의
# ---------------------------

# fetch_rss_pool: YAML에 정의된 RSS 소스들로부터
# DataFrame(columns=["id","title","url","domain", ...])을 반환한다고 가정
try:
    from src.news import fetch_rss_pool
except Exception:
    # fallback: RSS를 못 읽으면 빈 DataFrame 반환
    def fetch_rss_pool(yaml_path: str):
        # 기본적으로는 RSS에서 기사를 긁어와야 하지만,
        # Cloud에서 src/news.py를 못 찾는 경우 최소한 앱은 뜨도록 빈 값 반환
        return pd.DataFrame(columns=["id", "title", "url", "domain"])

# make_pair: 원 제목을 받아 감정형 / 정보형 버전을 만들어주는 함수
# 예: 감정형 "충격 고백... '눈물'" vs 정보형 "00 소속사 계약 관련 공식입장"
try:
    from src.features import make_pair
except Exception:
    # fallback: 제목 그대로 감정형/정보형 라벨만 붙여서 흉내 낸다
    class _PairStub:
        def __init__(self, t):
            base = t if t else "(제목 없음)"
            self.emotional = f"[감정형] {base}"
            self.factual   = f"[정보형] {base}"
    def make_pair(title: str):
        return _PairStub(title)

# ensure_dir: 폴더 없으면 만들어주는 유틸
try:
    from src.io_cache import ensure_dir
except Exception:
    def ensure_dir(path: str):
        os.makedirs(path, exist_ok=True)
        return path

# --------------------------------
# Streamlit 페이지 기본 설정
# --------------------------------
st.set_page_config(
    page_title="K-POP Headline A/B",
    page_icon="🎶",
    layout="wide"
)

st.title("K-POP 헤드라인 프레이밍 A/B 테스트")
st.write(
    "감정형 vs 정보형 헤드라인의 클릭률·체류시간(옵션)을 비교합니다. "
    "RSS에서 실제 기사들을 가져와 다수 카드를 한 화면에 노출합니다."
)

# 로그 디렉토리 준비
ensure_dir(LOG_DIR)

# 유저 세션 ID (가명) 부여
sid = st.session_state.get("sid")
if not sid:
    st.session_state["sid"] = sid = str(uuid.uuid4())

# --------------------------------
# 사이드바 (실험 설정)
# --------------------------------
n_cards = st.sidebar.slider(
    "한 번에 보여줄 카드 수",
    min_value=6,
    max_value=20,
    value=12,
    step=2,
    help="이만큼의 카드(기사)를 한 번에 뽑아서 A/B 헤드라인 섞어서 보여줍니다."
)

st.sidebar.caption("여러 카드에 A/B 헤드라인을 섞어 노출합니다.")

st.sidebar.markdown("---")
st.sidebar.write("데이터 소스: `data/news_sources.yaml` (RSS 목록)")
st.sidebar.write(
    "※ Streamlit Cloud에서도 돌아가도록 fallback이 설정되어 있습니다. "
    "src/news.py가 없으면 빈 데이터로 동작합니다."
)

# --------------------------------
# 기사 로딩
# --------------------------------
yaml_path = os.path.join(DATA_DIR, "news_sources.yaml")

try:
    pool = fetch_rss_pool(yaml_path)
except Exception as e:
    # RSS 소스 읽기나 파싱 중 에러가 나면 pool을 빈 DF로 두고 경고만 띄운다
    st.error(f"RSS 소스 읽기 오류: {e}")
    pool = pd.DataFrame(columns=["id","title","url","domain"])

# --------------------------------
# 만약 pool이 비면: 안내하고 종료
# --------------------------------
if pool is None or pool.empty:
    st.warning(
        "RSS에서 기사를 가져오지 못했습니다.\n\n"
        "- `data/news_sources.yaml`이 비었거나 잘못되었을 수 있습니다.\n"
        "- `src/news.py` 안의 fetch_rss_pool 구현을 확인하세요.\n"
        "- Cloud 배포라면 requirements.txt에 feedparser, PyYAML이 포함되었는지 확인하세요."
    )
    # 여기서도 로그 섹션은 안 돌리면 UX 허전하니까 안내만 하고 stop
    st.stop()

# --------------------------------
# 카드 샘플링 (이번 화면에서 보여줄 기사 n_cards개)
# --------------------------------
df_cards = pool.sample(
    min(n_cards, len(pool)),
    random_state=random.randint(0, 10**6)
).reset_index(drop=True)

# --------------------------------
# 카드 그리드 + 클릭 로그 수집
# --------------------------------
cols = st.columns(3)   # 3열 그리드
log_rows = []
pos = 0

for idx, row in df_cards.iterrows():
    pos += 1
    col = cols[idx % 3]
    with col:
        # A/B 헤드라인 생성
        pair = make_pair(row.get("title", "(제목 없음)"))
        variant = random.choice(["A", "B"])
        headline = pair.emotional if variant == "A" else pair.factual

        # 카드 본문
        st.markdown(f"**{headline}**")
        st.caption(row.get("domain", "unknown-source"))

        # 버튼 (이걸 눌렀다는 건 클릭으로 간주)
        btn_key = f"btn_{row.get('id', idx)}_{variant}"
        clicked = st.button("기사 보기", key=btn_key)

        # 원문 링크
        url_val = row.get("url", "#")
        st.markdown(f"[원문 링크]({url_val})")

        # 로그 후보 행을 메모리 상에 쌓아둔다
        log_rows.append({
            "sid": sid,
            "ts": pd.Timestamp.utcnow().isoformat() + "Z",
            "variant": variant,
            "title": row.get("title", ""),
            "url": url_val,
            "impression": 1,
            "click": int(clicked),
            "dwell_ms": 0,    # 카드별 체류시간은 추후 추적 가능
            "position": pos
        })

# --------------------------------
# 로그 CSV로 저장
# --------------------------------
# 파일 이름은 날짜 단위로 쌓는다.
fname = os.path.join(
    LOG_DIR,
    f"ab_headline_{pd.Timestamp.utcnow().date()}.csv"
)

df_log = pd.DataFrame(log_rows)
if not df_log.empty:
    # 이미 존재하면 append, 없으면 새로 생성
    if os.path.exists(fname):
        df_log.to_csv(fname, mode="a", header=False, index=False, encoding="utf-8-sig")
    else:
        df_log.to_csv(fname, index=False, encoding="utf-8-sig")

st.success(
    f"{len(df_cards)}개 카드 노출 로그가 기록되었습니다. "
    f"(파일: {os.path.relpath(fname, REPO_ROOT)})"
)

# --------------------------------
# 로그 미리보기 & 요약 섹션
# --------------------------------

st.divider()
st.subheader("📒 오늘 로그 미리보기 & 요약")

def _read_logs(path):
    """
    저장된 CSV 로그를 읽어 DataFrame으로 반환.
    숫자/시간 컬럼 정리까지 포함.
    """
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path)

        # 타입 보정
        df["impression"] = pd.to_numeric(df["impression"], errors="coerce").fillna(0).astype(int)
        df["click"] = pd.to_numeric(df["click"], errors="coerce").fillna(0).astype(int)
        df["dwell_ms"] = pd.to_numeric(df["dwell_ms"], errors="coerce").fillna(0).astype(int)
        df["ts"] = pd.to_datetime(df["ts"], errors="coerce")
        return df
    except Exception as e:
        st.error(f"로그 읽기 오류: {e}")
        return None

df_today = _read_logs(fname)

if df_today is None or df_today.empty:
    st.info(
        "오늘 로그가 아직 없어요.\n\n"
        "위 카드들에서 '기사 보기' 버튼을 눌러 클릭 데이터를 쌓아보세요."
    )

else:
    # 최근 20개만 보여주기
    st.dataframe(df_today.tail(20), use_container_width=True)

    total_imp = int(df_today["impression"].sum())
    total_click = int(df_today["click"].sum())
    ctr = (total_click / total_imp * 100) if total_imp else 0.0
    mean_dwell = float(df_today["dwell_ms"].mean()) if not df_today.empty else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Impressions", f"{total_imp:,}")
    c2.metric("Clicks", f"{total_click:,}")
    c3.metric("CTR", f"{ctr:.2f}%")
    c4.metric("Avg dwell (ms)", f"{mean_dwell:.0f}")

    st.markdown("**A/B 비교**")

    # variant 단위로 집계
    by_var = (
        df_today
        .groupby("variant", as_index=False)
        .agg(
            impressions=("impression", "sum"),
            clicks=("click", "sum"),
            avg_dwell=("dwell_ms", "mean"),
        )
    )

    # CTR 계산 및 정리
    # (impressions=0 인 경우 div0 방지)
    by_var["ctr(%)"] = (
        by_var["clicks"] / by_var["impressions"]
    ).replace([float("inf")], 0).fillna(0) * 100.0

    by_var["avg_dwell"] = by_var["avg_dwell"].round(1)

    # 보기 좋게 컬럼 순서 정리
    by_var = by_var[["variant", "impressions", "clicks", "ctr(%)", "avg_dwell"]]

    st.dataframe(by_var, use_container_width=True)

    st.caption(
        "variant가 'A'면 감정형 헤드라인, 'B'면 정보형 헤드라인입니다. "
        "CTR(%)는 클릭수 / 노출수 × 100, avg_dwell은 평균 체류(추후 확장)."
    )
