import google.generativeai as genai
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Categorizer:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        
        self.categories = [
            "Semiconductors",
            "Raw Materials",
            "Advanced Materials",
            "Components",
            "Consumer Electronics",
            "Photonics & Quantum",
            "Connectivity/6G",
            "Robotics",
            "Energy/Power",
            "Sustainable/Circular Engineering"
        ]
    
    def categorize_article(self, title: str) -> list:
        """
        기사 제목을 분석해서 올바른 카테고리 할당
        """
        try:
            prompt = f"""당신은 기술 산업 뉴스 분류 전문가입니다.

다음 기사 제목을 읽고, 10개 카테고리 중에서 가장 관련된 것을 정확히 1-2개만 선택하세요.

기사 제목: {title}

10개 카테고리:
1. Semiconductors - 반도체, 칩, 펍, 파운드리
2. Raw Materials - 희토류, 광물, 리튬, 원자재
3. Advanced Materials - 그래핀, 나노기술, 특수 소재
4. Components - 센서, 디스플레이, 액추에이터, 부품
5. Consumer Electronics - 스마트폰, 웨어러블, 스마트홈
6. Photonics & Quantum - 광자학, 양자컴퓨팅, 광기술
7. Connectivity/6G - 5G, 6G, 무선 통신, 네트워크
8. Robotics - 로봇, 자동화, 산업용 로봇
9. Energy/Power - 배터리, 전력, 에너지 저장
10. Sustainable/Circular Engineering - 순환경제, 지속가능성, E-폐기물

응답 형식 (반드시 이 형식):
카테고리: [카테고리명]"""

            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            logger.info(f"분류 응답: {result_text}")
            
            # 파싱
            categories = []
            if "카테고리:" in result_text:
                cat_part = result_text.split("카테고리:")[1].strip()
                cat_part = cat_part.replace("[", "").replace("]", "")
                
                cat_list = [c.strip() for c in cat_part.split(',')]
                
                for cat in cat_list:
                    if cat in self.categories:
                        categories.append(cat)
                    else:
                        # 부분 매칭
                        for valid_cat in self.categories:
                            if valid_cat.lower() in cat.lower() or cat.lower() in valid_cat.lower():
                                if valid_cat not in categories:
                                    categories.append(valid_cat)
                                break
            
            # 최대 2개만
            categories = categories[:2]
            
            # 파싱 실패 시 기본값: Components (보수적)
            if not categories:
                categories = ["Components"]
                logger.warning(f"⚠️ 파싱 실패, 기본값 설정: {title[:50]}... → Components")
            
            logger.info(f"✅ 분류 완료: {title[:50]}... → {categories}")
            return categories
        
        except Exception as e:
            logger.error(f"❌ 분류 오류: {str(e)}")
            return ["Components"]  # 오류 시도 기본값
