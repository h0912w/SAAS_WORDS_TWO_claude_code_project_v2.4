"""LINGUIST List 롱테일 검색어 후보 생성기 (2026-08-23, 사용자 지시).

SAAS_WORDS_TWO의 표준 "DomainWord+FunctionWord 2단어 Title Case" 파이프라인과는
별개의 일회성 작업이다 - 사용자가 ChatGPT 작성 방법론을 참고자료로 제공하며
"Linguist List"라는 고정 앵커어에 결합할 수 있는 검색어 후보를 recall 우선으로
최대한 넓게 생성하라고 지시했다. 최종 판별은 이 프로젝트 기존 규칙대로 Google Ads
Keyword Planner 게이트(config/keyword_metrics.yaml)로 한다 - 이 스크립트는 생성만
담당하고 검색량/경쟁도/SEO/상표권 판단은 하지 않는다.

산출물은 output/deliverables/linguist_list/candidates.csv (앵커어와 결합된 최종
검색어 문자열 전체, 중복 제거) - 기존 4개 SaaS 문서 스키마와는 무관한 별도 파일.
"""

from __future__ import annotations

import csv
from pathlib import Path

ANCHOR = "Linguist List"

# ---------------------------------------------------------------------------
# 축(axis) 단어 목록 - 세션이 직접 큐레이션(word_bank 큐레이션과 동일 역할).
# ChatGPT 초안의 35개 항목을 참고했으나 세션 판단으로 재구성/축약했다.
# ---------------------------------------------------------------------------

INTENT = [
    "info", "information", "guide", "how to use", "tutorial", "review", "reviews",
    "alternative", "alternatives", "vs", "comparison", "compare", "search",
    "download", "sign up", "signup", "login", "log in", "subscribe",
    "subscription", "news", "updates", "latest news", "membership", "directory",
    "archive", "forum", "community", "mailing list", "listserv",
]

PROFESSIONS = [
    "linguist", "researcher", "professor", "lecturer", "postdoc",
    "research assistant", "computational linguist", "NLP engineer",
    "language specialist", "translator", "interpreter",
    "localization specialist", "speech scientist", "language data analyst",
    "field linguist", "sociolinguist", "phonetician",
]

PROFESSION_ATTRIBUTES = [
    "academic", "industry", "remote", "freelance", "contract", "full time",
    "part time", "entry level", "senior", "international", "government",
    "nonprofit",
]

SUBFIELDS = [
    "syntax", "semantics", "pragmatics", "phonetics", "phonology",
    "morphology", "sociolinguistics", "psycholinguistics",
    "computational linguistics", "corpus linguistics", "applied linguistics",
    "cognitive linguistics", "historical linguistics", "forensic linguistics",
    "clinical linguistics", "neurolinguistics", "language acquisition",
    "language documentation", "linguistic typology", "discourse analysis",
    "translation studies", "language pedagogy",
]

AI_TECH = [
    "NLP", "LLM", "natural language processing", "machine translation",
    "speech recognition", "speech synthesis", "conversational AI",
    "language models", "language AI", "language technology", "text analytics",
    "sentiment analysis", "information extraction", "data annotation",
    "language annotation", "model evaluation", "AI training",
    "large language models", "generative AI",
]

ACADEMIC_ACTIVITIES = [
    "conference", "workshop", "seminar", "symposium", "webinar",
    "summer school", "call for papers", "CFP", "abstract submission",
    "paper submission", "journal", "publication", "dissertation", "thesis",
    "research project", "grant", "fellowship", "scholarship", "colloquium",
    "roundtable",
]

EDUCATION_LEVELS = [
    "undergraduate", "graduate", "masters", "MA", "MSc", "PhD", "doctoral",
    "postdoctoral", "certificate", "course", "training", "summer school",
    "internship", "diploma",
]

AUDIENCES = [
    "students", "graduate students", "PhD students", "researchers",
    "professors", "academics", "postdocs", "teachers", "linguists",
    "job seekers", "recruiters", "universities", "language professionals",
    "beginners", "undergraduates",
]

COUNTRIES = [
    "United States", "USA", "US", "UK", "United Kingdom", "Canada",
    "Australia", "Germany", "France", "Spain", "Italy", "Netherlands",
    "Belgium", "Switzerland", "Austria", "Sweden", "Norway", "Denmark",
    "Finland", "Poland", "Ireland", "Portugal", "Greece", "Russia",
    "Japan", "China", "Korea", "South Korea", "India", "Singapore",
    "Taiwan", "Hong Kong", "Vietnam", "Thailand", "Indonesia", "Malaysia",
    "Philippines", "Israel", "Turkey", "Saudi Arabia", "UAE", "Egypt",
    "South Africa", "Nigeria", "Kenya", "Brazil", "Mexico", "Argentina",
    "Chile", "Colombia", "New Zealand", "Europe", "Asia", "Southeast Asia",
    "Latin America", "Africa", "Middle East", "Scandinavia",
]

CITIES = [
    "New York", "Boston", "Chicago", "Los Angeles", "San Francisco",
    "Washington DC", "London", "Oxford", "Cambridge", "Edinburgh",
    "Manchester", "Berlin", "Munich", "Paris", "Amsterdam", "Brussels",
    "Vienna", "Zurich", "Geneva", "Stockholm", "Copenhagen", "Oslo",
    "Helsinki", "Dublin", "Rome", "Madrid", "Barcelona", "Warsaw",
    "Tokyo", "Kyoto", "Beijing", "Shanghai", "Seoul", "Singapore",
    "Hong Kong", "Taipei", "Sydney", "Melbourne", "Toronto", "Montreal",
]

LANGUAGES = [
    "English", "Spanish", "French", "German", "Italian", "Portuguese",
    "Dutch", "Russian", "Polish", "Swedish", "Norwegian", "Danish",
    "Finnish", "Greek", "Turkish", "Arabic", "Hebrew", "Persian", "Urdu",
    "Hindi", "Bengali", "Punjabi", "Tamil", "Telugu", "Chinese",
    "Mandarin", "Cantonese", "Japanese", "Korean", "Vietnamese", "Thai",
    "Indonesian", "Malay", "Tagalog", "Swahili", "Amharic", "Yoruba",
    "Zulu", "ASL", "American Sign Language", "BSL", "sign language",
    "indigenous languages", "endangered languages", "creole languages",
    "Latin", "Ancient Greek", "Sanskrit", "Esperanto",
]

MODIFIERS = [
    "best", "top", "latest", "new", "current", "updated", "free", "online",
    "remote", "paid", "funded", "fully funded", "international", "global",
    "academic", "professional", "beginner", "advanced", "official",
]

TIME_TERMS = [
    "2026", "2027", "2028", "today", "this week", "this month", "upcoming",
    "latest", "current", "annual",
]

COMMERCIAL_INTENT = [
    "jobs", "job listings", "job board", "job search", "career", "careers",
    "employment", "vacancy", "vacancies", "open positions", "salary",
    "hiring", "internships", "paid", "funding", "grants", "scholarships",
    "fellowships", "consulting", "freelance", "services", "employer",
    "recruiter", "career path", "certification", "application", "visa",
    "relocation", "database", "corpus", "dataset", "software",
    "association", "society",
]

PROBLEM_WORDS = [
    "login problem", "subscription issue", "email problem",
    "search not working", "account issue", "posting problem",
    "job posting", "submission deadline", "application problem",
    "access issue", "archive not loading", "password reset",
]

COMPARISON_TARGETS = [
    "job boards", "academic job sites", "linguistics websites",
    "research databases", "conference directories", "academic communities",
    "mailing lists", "language job sites",
]

ABBREVIATIONS = ["NLP", "AI", "LLM", "CFP", "PhD", "MA", "MSc", "ESL", "EFL", "TESOL", "ASL", "BA", "BSc"]

QUESTION_PHRASES = [
    "how to find jobs", "how to join", "how to submit a paper",
    "how to post a job", "where to find conferences",
    "what is", "why use", "how to access the archive",
    "how to search", "how to subscribe",
]


def _single_axis_candidates() -> set[str]:
    """앵커 + 축 단어 1개 조합 (recall 우선, 대부분의 축 전체를 직접 결합)."""
    candidates: set[str] = set()
    single_axes = [
        INTENT, PROFESSIONS, SUBFIELDS, AI_TECH, ACADEMIC_ACTIVITIES,
        EDUCATION_LEVELS, AUDIENCES, COUNTRIES, CITIES, LANGUAGES,
        MODIFIERS, TIME_TERMS, COMMERCIAL_INTENT, PROBLEM_WORDS,
        COMPARISON_TARGETS, ABBREVIATIONS, QUESTION_PHRASES,
        PROFESSION_ATTRIBUTES,
    ]
    for axis in single_axes:
        for term in axis:
            candidates.add(f"{ANCHOR} {term}")
    return candidates


def _pair_candidates() -> set[str]:
    """2축 교차(long-tail) - 모든 축을 서로 교차하지 않고, 자연스러운 검색
    의도를 형성하는 축 쌍만 선택해 조합 폭발을 방지한다."""
    candidates: set[str] = set()
    pairs: list[tuple[list[str], list[str]]] = [
        (MODIFIERS, INTENT),
        (MODIFIERS, COMMERCIAL_INTENT),
        (INTENT, COUNTRIES),
        (COMMERCIAL_INTENT, COUNTRIES),
        (COMMERCIAL_INTENT, CITIES),
        (PROFESSIONS, PROFESSION_ATTRIBUTES),
        (PROFESSIONS, COUNTRIES),
        (SUBFIELDS, INTENT),
        (SUBFIELDS, EDUCATION_LEVELS),
        (EDUCATION_LEVELS, SUBFIELDS),
        (LANGUAGES, PROFESSIONS),
        (LANGUAGES, COMMERCIAL_INTENT),
        (AUDIENCES, INTENT),
        (AUDIENCES, COMMERCIAL_INTENT),
        (AI_TECH, ACADEMIC_ACTIVITIES),
        (ACADEMIC_ACTIVITIES, COUNTRIES),
        (MODIFIERS, SUBFIELDS),
        (TIME_TERMS, ACADEMIC_ACTIVITIES),
        (TIME_TERMS, COMMERCIAL_INTENT),
        (PROFESSION_ATTRIBUTES, COMMERCIAL_INTENT),
        (LANGUAGES, ACADEMIC_ACTIVITIES),
        (AUDIENCES, COUNTRIES),
        (PROFESSIONS, CITIES),
        (MODIFIERS, COUNTRIES),
        (MODIFIERS, CITIES),
        (MODIFIERS, LANGUAGES),
        (COMMERCIAL_INTENT, LANGUAGES),
    ]
    for axis_a, axis_b in pairs:
        for a in axis_a:
            for b in axis_b:
                candidates.add(f"{ANCHOR} {a} {b}")
    return candidates


# 실제 검색 롱테일 형태(ChatGPT 예시: "remote jobs Germany")를 반영한 3축 교차 -
# 조합 폭발 방지를 위해 각 축을 의도적으로 좁힌 부분집합만 사용.
_MODIFIER_SUBSET = ["remote", "paid", "funded", "international", "free", "online"]
_COUNTRY_SUBSET = COUNTRIES[:25]


def _triple_axis_candidates() -> set[str]:
    candidates: set[str] = set()
    for m in _MODIFIER_SUBSET:
        for c in COMMERCIAL_INTENT:
            for country in _COUNTRY_SUBSET:
                candidates.add(f"{ANCHOR} {m} {c} {country}")
    for level in EDUCATION_LEVELS:
        for sub in SUBFIELDS:
            for country in _COUNTRY_SUBSET[:12]:
                candidates.add(f"{ANCHOR} {level} {sub} {country}")
    return candidates


def generate() -> list[str]:
    all_candidates = _single_axis_candidates() | _pair_candidates() | _triple_axis_candidates()
    # 완전 중복(대소문자 차이 등)만 제거, 검색 형태가 다르면 유지(#26).
    seen_lower: dict[str, str] = {}
    for c in all_candidates:
        seen_lower.setdefault(c.lower(), c)
    return sorted(seen_lower.values())


def main() -> None:
    candidates = generate()
    out_dir = Path(__file__).resolve().parents[1] / "output" / "deliverables" / "linguist_list"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "candidates.csv"
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["candidate"])
        for c in candidates:
            writer.writerow([c])
    print(f"generated {len(candidates)} candidates -> {out_path}")


if __name__ == "__main__":
    main()
