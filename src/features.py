import re, random
from dataclasses import dataclass

EMOJIS = ["✨","🔥","💥","🎶","🚀","💎","🌟","📈"]
FACT_WORDS = ["[공식]", "[속보]", "[데이터]", "[지표]", "[요약]"]

@dataclass
class HeadlinePair:
    emotional: str
    factual: str

def to_emotional(title: str) -> str:
    emo = random.choice(EMOJIS)
    return f"{emo} {title} — 반드시 봐야 할 포인트 {random.randint(2,4)}가지"

def to_factual(title: str) -> str:
    tag = random.choice(FACT_WORDS)
    # 숫자·엔티티 보존, 과장 최소화
    return f"{tag} {title} | 핵심지표·링크 수집"

def make_pair(title: str) -> HeadlinePair:
    return HeadlinePair(emotional=to_emotional(title), factual=to_factual(title))
