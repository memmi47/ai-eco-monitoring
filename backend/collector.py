"""
collector.py — AI Eco Monitor 뉴스 자동 수집기

수집 전략:
- Google News RSS로 등록된 모든 기업명 검색 (600개 전체)
- TechCrunch / Reuters Tech 고정 RSS로 AI 키워드 필터링
- crawl_history 중복 체크 후 analysis_results까지 자동 파이프라인 연결
"""

import os
import time
import sqlite3
import logging
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote

import feedparser
import httpx

# ============================================================
# 로거 설정
# ============================================================

logger = logging.getLogger("collector")
if not logger.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [COLLECTOR] %(message)s",
        handlers=[logging.StreamHandler()],
    )

# ============================================================
# 상수
# ============================================================

AI_KEYWORDS = [
    "HBM", "NVL72", "AI DC", "GPU", "DRAM", "NAND", "LLM",
    "generative AI", "data center", "semiconductor", "NVIDIA", "AI chip",
    "memory bandwidth", "inference", "AI accelerator", "CXL", "HBM3",
]

STATIC_RSS_FEEDS = [
    "https://techcrunch.com/feed/",
    "https://feeds.reuters.com/reuters/technologyNews",
]

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"

# API 엔드포인트 (백엔드 자기 자신) — Railway는 PORT 환경변수로 포트가 결정됨
_PORT = os.environ.get("PORT", "8000")
ANALYZE_ENDPOINT = os.environ.get("ANALYZE_ENDPOINT", f"http://localhost:{_PORT}/api/analyze/v2")

# 요청 사이 대기 시간 (초) — Google News RSS rate limit 방지
REQUEST_DELAY = float(os.environ.get("COLLECTOR_REQUEST_DELAY", "0.5"))

# ============================================================
# DB 헬퍼
# ============================================================

def _get_db_conn(db_path: str) -> sqlite3.Connection:
    """Collector 전용 SQLite 연결 (thread-safe, row_factory 적용)."""
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def load_companies(db_path: str, tier_filter: Optional[str] = None) -> list[dict]:
    """
    companies 테이블에서 기업 목록 로드.
    tier_filter: "T1" | "T2" | "T3" | None (전체)
    """
    conn = _get_db_conn(db_path)
    try:
        cursor = conn.cursor()
        if tier_filter:
            # tier 컬럼이 없을 경우를 대비해 layer 기반 tier도 시도
            cursor.execute(
                "SELECT id, company_name, tier FROM companies WHERE tier = ?",
                (tier_filter,)
            )
        else:
            cursor.execute("SELECT id, company_name, tier FROM companies")
        rows = [dict(r) for r in cursor.fetchall()]
        return rows
    except Exception as e:
        logger.error(f"기업 목록 로드 실패: {e}")
        return []
    finally:
        conn.close()


def check_duplicate(url: str, conn: sqlite3.Connection) -> bool:
    """crawl_history에 동일 URL이 존재하면 True 반환."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM crawl_history WHERE source_url = ? LIMIT 1", (url,))
        return cursor.fetchone() is not None
    except Exception:
        return False


def save_crawl_history(article: dict, company_id: int, conn: sqlite3.Connection) -> Optional[int]:
    """crawl_history에 기사 저장. 저장된 row id 반환."""
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO crawl_history (company_id, title, source_url, published_date, content, crawled_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                company_id,
                article.get("title", "")[:500],
                article.get("url", ""),
                article.get("published"),
                article.get("snippet", "")[:2000],
                datetime.now(timezone.utc).isoformat(),
            ),
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        logger.warning(f"crawl_history 저장 실패 ({article.get('url','')}): {e}")
        return None

# ============================================================
# RSS 수집
# ============================================================

def _parse_feed_entries(feed) -> list[dict]:
    """feedparser 결과를 통일된 dict 목록으로 변환."""
    articles = []
    for entry in feed.entries:
        title = getattr(entry, "title", "") or ""
        url = getattr(entry, "link", "") or ""
        snippet = getattr(entry, "summary", "") or getattr(entry, "description", "") or ""
        published_raw = getattr(entry, "published", None) or getattr(entry, "updated", None)

        # HTML 태그 간단 제거
        import re
        snippet = re.sub(r"<[^>]+>", " ", snippet).strip()

        articles.append({
            "title": title.strip(),
            "url": url.strip(),
            "snippet": snippet[:1000],
            "published": published_raw,
        })
    return articles


def fetch_google_news(keyword: str) -> list[dict]:
    """Google News RSS에서 키워드 검색 결과 수집."""
    try:
        url = GOOGLE_NEWS_RSS.format(query=quote(keyword))
        feed = feedparser.parse(url)
        return _parse_feed_entries(feed)
    except Exception as e:
        logger.warning(f"Google News RSS 실패 ({keyword}): {e}")
        return []


def fetch_static_rss(feed_url: str) -> list[dict]:
    """고정 RSS 피드 (TechCrunch, Reuters) 수집."""
    try:
        feed = feedparser.parse(feed_url)
        return _parse_feed_entries(feed)
    except Exception as e:
        logger.warning(f"정적 RSS 실패 ({feed_url}): {e}")
        return []

# ============================================================
# 필터링
# ============================================================

def _build_company_index(companies: list[dict]) -> dict[str, int]:
    """company_name → company_id 매핑 (소문자 정규화)."""
    return {c["company_name"].lower(): c["id"] for c in companies if c.get("company_name")}


def filter_and_match(
    articles: list[dict],
    companies: list[dict],
    ai_keywords: list[str],
) -> list[dict]:
    """
    기사를 필터링하고 매칭되는 company_id를 첨부.
    - 기업명 또는 AI 키워드가 제목/스니펫에 포함된 기사만 통과
    - 매칭된 첫 번째 company_id 반환 (없으면 스킵)
    """
    company_index = _build_company_index(companies)
    kw_lower = [k.lower() for k in ai_keywords]
    matched = []

    for article in articles:
        text = (article.get("title", "") + " " + article.get("snippet", "")).lower()

        # 기업명 매칭 (우선)
        matched_company_id = None
        for name_lower, cid in company_index.items():
            if name_lower and name_lower in text:
                matched_company_id = cid
                break

        # AI 키워드 매칭 (기업명 매칭 없을 경우)
        if matched_company_id is None:
            has_kw = any(kw in text for kw in kw_lower)
            if not has_kw:
                continue  # 둘 다 없으면 스킵

        article["company_id"] = matched_company_id
        matched.append(article)

    return matched

# ============================================================
# 분석 트리거
# ============================================================

def trigger_analysis(company_id: int, title: str, snippet: str) -> dict:
    """
    /api/analyze/v2 호출.
    company_id가 None이면 스킵 (AI 키워드만 매칭된 경우).
    """
    if company_id is None:
        return {"skipped": True, "reason": "no company match"}
    try:
        with httpx.Client(timeout=120.0) as client:
            resp = client.post(
                ANALYZE_ENDPOINT,
                json={"company_id": company_id, "title": title, "snippet": snippet},
            )
            resp.raise_for_status()
            return resp.json()
    except httpx.HTTPStatusError as e:
        return {"error": f"HTTP {e.response.status_code}", "detail": str(e)}
    except Exception as e:
        return {"error": str(e)}

# ============================================================
# 메인 수집 사이클
# ============================================================

def run_collection_job(db_path: str, tier_filter: Optional[str] = None):
    """
    뉴스 수집 전체 사이클.

    tier_filter:
        "T1" → T1 핵심기업만 (6시간 주기 스케줄용)
        None  → 전체 기업 (24시간 주기 스케줄용)
    """
    label = f"[tier={tier_filter or 'ALL'}]"
    logger.info(f"=== 수집 사이클 시작 {label} ===")

    # 1. 기업 목록 로드
    companies = load_companies(db_path, tier_filter=tier_filter)
    if not companies:
        logger.warning(f"기업 목록 없음 {label}, 사이클 종료")
        return

    logger.info(f"대상 기업 수: {len(companies)} {label}")

    conn = _get_db_conn(db_path)

    total_fetched = 0
    total_filtered = 0
    total_saved = 0
    total_analyzed_ok = 0
    total_analyzed_fail = 0

    try:
        # 2. 고정 RSS 수집 (TechCrunch, Reuters) — AI 키워드 필터만 적용
        static_articles: list[dict] = []
        for feed_url in STATIC_RSS_FEEDS:
            articles = fetch_static_rss(feed_url)
            logger.info(f"정적 RSS {feed_url.split('/')[2]}: {len(articles)}건 수집")
            static_articles.extend(articles)
            time.sleep(REQUEST_DELAY)

        filtered_static = filter_and_match(static_articles, companies, AI_KEYWORDS)
        total_fetched += len(static_articles)
        total_filtered += len(filtered_static)

        for article in filtered_static:
            url = article.get("url", "")
            if not url or check_duplicate(url, conn):
                continue
            cid = article.get("company_id")
            row_id = save_crawl_history(article, cid or 0, conn)
            if row_id and cid:
                total_saved += 1
                result = trigger_analysis(cid, article["title"], article["snippet"])
                if "error" in result:
                    total_analyzed_fail += 1
                    logger.debug(f"분석 실패: {article['title'][:60]} — {result['error']}")
                elif not result.get("skipped"):
                    total_analyzed_ok += 1

        # 3. 기업별 Google News RSS 검색
        for company in companies:
            cname = company.get("company_name", "")
            if not cname:
                continue

            try:
                articles = fetch_google_news(cname)
                total_fetched += len(articles)

                # 이 경우 모든 기사가 해당 기업 관련이므로 company_id 직접 할당
                for a in articles:
                    a["company_id"] = company["id"]

                for article in articles:
                    url = article.get("url", "")
                    if not url or check_duplicate(url, conn):
                        continue
                    total_filtered += 1
                    save_crawl_history(article, company["id"], conn)
                    total_saved += 1
                    result = trigger_analysis(company["id"], article["title"], article["snippet"])
                    if "error" in result:
                        total_analyzed_fail += 1
                    elif not result.get("skipped"):
                        total_analyzed_ok += 1

            except Exception as e:
                logger.warning(f"기업 '{cname}' 수집 오류 (스킵): {e}")

            time.sleep(REQUEST_DELAY)

        logger.info(
            f"=== 수집 사이클 완료 {label} | "
            f"수집 {total_fetched}건 | 필터통과 {total_filtered}건 | "
            f"저장 {total_saved}건 | 분석성공 {total_analyzed_ok}건 | "
            f"분석실패 {total_analyzed_fail}건 ==="
        )

    except Exception as e:
        logger.error(f"수집 사이클 치명적 오류 {label}: {e}", exc_info=True)
    finally:
        conn.close()
