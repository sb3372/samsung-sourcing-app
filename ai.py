"""
AI 분류 및 요약 (Gemini API 사용)
"""
import google.generativeai as genai
import logging
import json
import re
import time
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import CATEGORIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _jaccard_similarity(text1: str, text2: str) -> float:
    """단어 집합 기반 Jaccard 유사도 (0~1)"""
    if not text1 or not text2:
        return 0.0
    words1 = set(re.findall(r"\w+", text1.lower()))
    words2 = set(re.findall(r"\w+", text2.lower()))
    if not words1 or not words2:
        return 0.0
    intersection = words1 & words2
    union = words1 | words2
    return len(intersection) / len(union)


class AIProcessor:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")

    def _process_single(self, article: Dict) -> Dict:
        """단일 기사를 Gemini로 분류·요약"""
        title = article.get("title", "")
        content = article.get("content", "")
        text = f"{title}\n\n{content}"[:3000]

        prompt = f"""You are a European tech news analyst.

Analyze the following article and respond ONLY with valid JSON (no markdown, no code blocks).

Article:
{text}

Categories to choose from:
{json.dumps(CATEGORIES, ensure_ascii=False)}

JSON schema:
{{
  "is_europe_relevant": <true if the article involves a European company or European market, false otherwise>,
  "categories": [<list of matching category strings from the list above, can be multiple>],
  "summary": "<200-character Korean summary>",
  "companies": [<list of European company names mentioned>]
}}"""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            # Strip markdown code fences if present
            result_text = re.sub(r"^```[a-z]*\n?", "", result_text)
            result_text = re.sub(r"\n?```$", "", result_text)
            json_match = re.search(r"\{.*\}", result_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                article["is_europe_relevant"] = bool(parsed.get("is_europe_relevant", False))
                article["categories"] = [
                    c for c in parsed.get("categories", []) if c in CATEGORIES
                ]
                article["summary"] = str(parsed.get("summary", ""))[:200]
                article["companies"] = parsed.get("companies", [])
                logger.info(f"✅ {title[:50]} → {article['categories']}")
            else:
                logger.warning(f"⚠️ JSON 파싱 실패: {title[:50]}")
                article["is_europe_relevant"] = False
                article["categories"] = []
                article["summary"] = ""
                article["companies"] = []
        except Exception as e:
            logger.error(f"❌ AI 오류: {str(e)[:80]}")
            article["is_europe_relevant"] = False
            article["categories"] = []
            article["summary"] = ""
            article["companies"] = []

        return article

    def process_articles(self, articles: List[Dict]) -> List[Dict]:
        """기사 목록을 순차 처리"""
        results = []
        for article in articles:
            results.append(self._process_single(article))
            time.sleep(0.5)
        return results

    def process_articles_parallel(self, articles: List[Dict], max_workers: int = 5) -> List[Dict]:
        """기사 목록을 병렬 처리 (rate-limit 보호를 위해 0.5s sleep 포함)"""
        results: List[Dict] = [None] * len(articles)

        def worker(idx_article):
            idx, article = idx_article
            time.sleep(0.5)  # Gemini API 분당 요청 제한 보호
            return idx, self._process_single(article)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(worker, (i, a)): i for i, a in enumerate(articles)
            }
            for future in as_completed(futures):
                try:
                    idx, result = future.result()
                    results[idx] = result
                except Exception as e:
                    logger.error(f"❌ 병렬 처리 오류: {str(e)[:60]}")

        return [r for r in results if r is not None]

    def is_duplicate(self, article1: Dict, article2: Dict) -> bool:
        """50% 이상 Jaccard 유사도이면 중복으로 간주"""
        text1 = f"{article1.get('title', '')} {article1.get('content', '')}"
        text2 = f"{article2.get('title', '')} {article2.get('content', '')}"
        return _jaccard_similarity(text1, text2) >= 0.5
