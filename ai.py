"""
AI 분류 및 요약 (Gemini API 사용)
"""
import google.generativeai as genai
import logging
import json
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIProcessor:
    def __init__(self, api_key: str):
        """API 키로 초기화"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        
        self.categories = [
            "반도체",
            "원자재",
            "신소재",
            "전자제품 부품",
            "소비자 가전 제품",
            "네트워크",
            "로봇",
            "배터리",
            "신기술/신기술 연구자료",
            "스타트업/Spin-off 투자"
        ]
    
    def categorize_and_summarize(self, title: str, content: str) -> dict:
        """
        기사를 분류하고 요약
        
        Returns:
            {
                'categories': ['반도체', '신기술/신기술 연구자료'],
                'summary': '요약 문...',
                'companies': ['ASML', 'Infineon'],
                'success': True/False
            }
        """
        try:
            prompt = f"""당신은 유럽 기술 뉴스 분석 전문가입니다.

다음 기사를 분석하고:
1. 기사에서 언급되는 유럽 회사 찾기
2. 기사를 10개 카테고리로 분류 (1개 이상 가능)
3. 기사를 200자 이내로 요약

기사 제목: {title}

기사 본문:
{content[:3000]}

10개 카테고리:
1. 반도체 - 반도체 제조, 칩 설계, 파운드리
2. 원자재 - 희토류, 광물, 리튬 등
3. 신소재 - 그래핀, 나노기술 등
4. 전자제품 부품 - 센서, 디스플레이, 캐패시터 등
5. 소비자 가전 제품 - 스마트폰, 웨어러블 등
6. 네트워크 - 5G, 6G, 통신 인프라
7. 로봇 - 산업용 로봇, 자동화
8. 배터리 - 배터리 기술, 에너지 저장
9. 신기술/신기술 연구자료 - 양자컴퓨팅, 광자학 등
10. 스타트업/Spin-off 투자 - 신생 기업 투자, Spin-off

JSON 형식으로 응답:
{{
    "categories": ["카테고리1", "카테고리2"],
    "summary": "요약 문...",
    "companies": ["회사1", "회사2"],
    "is_europe_relevant": true/false
}}

주의사항:
- 유럽과 무관하거나 유럽 회사가 없으면 is_europe_relevant: false
- 10개 카테고리 중에만 선택
- 유럽 회사만 companies에 포함
- 요약은 정확하고 간결하게"""

            response = self.model.generate_content(prompt, timeout=30)
            result_text = response.text.strip()
            
            # JSON 파싱
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_json = json.loads(json_match.group())
                logger.info(f"✅ 분류: {title[:50]}... → {result_json['categories']}")
                result_json['success'] = True
                return result_json
            else:
                logger.warning(f"⚠️ JSON 파싱 실패: {title[:50]}")
                return {
                    'categories': [],
                    'summary': '',
                    'companies': [],
                    'is_europe_relevant': False,
                    'success': False
                }
        
        except Exception as e:
            logger.error(f"❌ AI 분류 오류: {str(e)}")
            return {
                'categories': [],
                'summary': '',
                'companies': [],
                'is_europe_relevant': False,
                'success': False
            }
    
    def check_similarity(self, text1: str, text2: str) -> float:
        """
        두 텍스트의 유사도 확인 (50% 이상 중복)
        """
        try:
            prompt = f"""두 텍스트가 같은 뉴스 기사인지 확인하세요.

텍스트 1:
{text1[:500]}

텍스트 2:
{text2[:500]}

0~100 사이의 숫자로만 응답 (0: 완전 다름, 100: 동일)"""

            response = self.model.generate_content(prompt, timeout=10)
            result_text = response.text.strip()
            
            # 숫자 추출
            import re
            numbers = re.findall(r'\d+', result_text)
            if numbers:
                similarity = int(numbers[0])
                logger.info(f"유사도: {similarity}%")
                return similarity / 100  # 0~1 범위로 변환
            
            return 0
        
        except Exception as e:
            logger.error(f"❌ 유사도 확인 오류: {str(e)}")
            return 0
