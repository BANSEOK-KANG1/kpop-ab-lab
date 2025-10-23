# K-POP AB Lab — A/B 테스트 + 동향 파악 (0원, Python, GitHub 구동)

K-POP·엔터 산업을 위한 **A/B 테스트와 동향 파악** 레포지토리입니다.  
**무료 API**만 사용하며, 파이썬으로 실행하고 깃허브에 전시하기 쉽게 구성했습니다.

## 무엇을 제공하나
- **K-Buzz Index**: YouTube(조회), Wikimedia Pageviews(관심), Last.fm(팬심) 신호를 정규화 후 가중합한 **주간 화제성 지수**
- **헤드라인 프레이밍 A/B**: 감정형 vs 정보형 헤드라인의 **클릭률·체류시간** 실험(로컬/Streamlit)
- **컴백 타이밍 분석(샘플)**: 업로드 시각·요일의 초기 조회 속도에 대한 준실험 로직 골격

## 폴더 구조
```
kpop-ab-lab/
  ├─ src/
  │   ├─ yt.py          # YouTube API 호출/캐시/유틸
  │   ├─ wiki.py        # Wikimedia Pageviews 호출
  │   ├─ lastfm.py      # Last.fm API(Spotify 대체/보완)
  │   ├─ features.py    # 텍스트 헤드라인 변환, 로그 유틸
  │   └─ io_cache.py    # 간단 캐시/파일 IO
  ├─ dash/
  │   └─ app_headline_ab.py  # Streamlit A/B 앱
  ├─ scripts/
  │   └─ kbuzz_index.py      # 주간 K-Buzz Index 계산 스크립트
  ├─ data/
  │   ├─ artists.sample.csv  # 아티스트 메타(샘플)
  │   ├─ news_links.sample.csv  # A/B 실험용 링크(샘플)
  │   └─ logs/               # A/B 로그 CSV 저장 위치
  ├─ reports/
  │   └─ RESULTS.md          # 결과 요약(작성 템플릿)
  ├─ tests/
  │   └─ test_schemas.py     # API 응답 필드 체크 예시
  ├─ requirements.txt
  └─ README.md
```

## 실행 준비
1) 파이썬 3.10+
2) 의존성 설치
```bash
pip install -r requirements.txt
```
3) 환경변수 설정(무료 키)
- `YOUTUBE_API_KEY` : Google Cloud 콘솔에서 YouTube Data API v3 키
- `LASTFM_API_KEY`  : Last.fm API 키

(Spotify Web API는 정책 변동 가능성이 있어 기본 경로에서 제외했으며, 필요 시 직접 추가하세요.)

환경변수 예시(Mac/Linux):
```bash
export YOUTUBE_API_KEY="YOUR_KEY"
export LASTFM_API_KEY="YOUR_KEY"
```

## 1) K-Buzz Index 계산
아티스트 목록(`data/artists.sample.csv`)을 기반으로 최근 일자 기준 **YouTube 조회 합계**, **Wikipedia 일별 페이지뷰(최근 14일 평균)**, **Last.fm 팬심 신호(청취·리스너)**를 수집해 z-score 정규화 → 가중합하여 **주간 지수**를 만듭니다.

```bash
python scripts/kbuzz_index.py --days 14 --out data/kbuzz_2025-10-23.csv
```

산출물:
- `data/kbuzz_YYYY-MM-DD.csv` : 소스별 지표·정규화·가중합 결과
- `reports/RESULTS.md` : 상위 Top-N, 급상승 리스트 (스크립트가 자동 업데이트)

## 2) 헤드라인 프레이밍 A/B(Streamlit)
샘플 뉴스 링크(`data/news_links.sample.csv`)를 불러와 **감정형(A)**과 **정보형(B)** 타이틀을 무작위 배정으로 노출합니다.  
사용자의 클릭/체류시간/노출위치가 `data/logs/ab_headline_*.csv`로 기록됩니다.

```bash
streamlit run dash/app_headline_ab.py
```

분석 방법:
- CTR 비교: 카이제곱(또는 피셔), 효과크기(오즈비)
- 체류시간: 비모수(U-test) 또는 로그정규 가정 하 t-test
- 교란변수: 카드 위치·이모지/이미지 유무·시간대는 모두 로그에 저장

## 데이터 출처(공식 문서)
- **YouTube Data API v3**: videos.list / search.list / statistics  
- **Wikimedia REST Pageviews API**: per-article daily views  
- **Last.fm API**: artist.getInfo, artist.getTopTracks  
- **Streamlit**: 앱 프레임워크  
- **SciPy/Statsmodels**: 검정·회귀·ANCOVA 구현

## 참고 / 정책 주의
- YouTube API는 메서드별 쿼터가 다릅니다(일반 조회는 충분).  
- Last.fm은 비상업적 용도에서 자유로운 편이나 약관 준수 필요.  
- Spotify Web API는 2024~2025 정책 변경 이슈가 있어 본 레포의 기본 경로에서는 선택사항으로 처리합니다.

## 재현성
- 모든 결과는 `data/`에 CSV로 남기며, 레포에 올릴 때는 개인정보·토큰을 포함하지 않도록 `.gitignore`를 활용하세요.

즐거운 실험을!
