"""
이메일 분류 모듈
본문 내용을 기반으로 이메일을 자동으로 분류합니다.
"""

import re
import json
from typing import Dict, List, Tuple
from bs4 import BeautifulSoup


class MailClassifier:
    """이메일을 본문 내용에 따라 분류하는 클래스"""
    
    def __init__(self, keywords_config: str):
        """
        Args:
            keywords_config: JSON 형식의 분류 키워드 설정
        """
        try:
            self.keywords = json.loads(keywords_config)
        except json.JSONDecodeError:
            self.keywords = {
                "업무": ["회의", "보고", "프로젝트", "계획"],
                "영업": ["고객", "제안", "계약", "판매"],
                "기술": ["버그", "오류", "지원", "개발"],
                "기타": []
            }
    
    def extract_text_from_html(self, html_content: str) -> str:
        """HTML에서 텍스트 추출"""
        if not html_content:
            return ""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            # 스크립트와 스타일 제거
            for script in soup(["script", "style"]):
                script.decompose()
            text = soup.get_text(separator=' ', strip=True)
            return text
        except Exception as e:
            print(f"HTML 파싱 오류: {e}")
            return html_content
    
    def clean_text(self, text: str) -> str:
        """텍스트 전처리"""
        # 공백 정규화
        text = re.sub(r'\s+', ' ', text)
        # 특수문자 제거 (한글, 영문, 숫자, 기본 문장부호만 유지)
        text = re.sub(r'[^\w\s가-힣.,!?]', '', text)
        return text.lower().strip()
    
    def classify(self, subject: str, body: str, html_body: str = None) -> Tuple[str, float]:
        """
        이메일을 분류합니다.
        
        Args:
            subject: 이메일 제목
            body: 이메일 본문 (텍스트)
            html_body: 이메일 본문 (HTML)
        
        Returns:
            (분류 카테고리, 신뢰도 점수)
        """
        # HTML에서 텍스트 추출
        if html_body:
            html_text = self.extract_text_from_html(html_body)
        else:
            html_text = ""
        
        # 제목과 본문 합치기
        combined_text = f"{subject} {body} {html_text}".lower()
        combined_text = self.clean_text(combined_text)
        
        category_scores = {}
        
        # 각 카테고리별로 키워드 매칭
        for category, keywords in self.keywords.items():
            if category == "기타":
                continue
            
            matches = 0
            for keyword in keywords:
                keyword = keyword.lower()
                # 키워드가 포함된 횟수 세기
                matches += combined_text.count(keyword)
            
            if matches > 0:
                category_scores[category] = matches
        
        # 가장 점수가 높은 카테고리 선택
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            max_score = category_scores[best_category]
            # 정규화된 신뢰도 점수 (0-1)
            confidence = min(max_score / 5.0, 1.0)  # 최대 5개 일치 = 100% 신뢰도
            return best_category, confidence
        
        # 매칭되지 않으면 기타
        return "기타", 0.0
    
    def get_category_emoji(self, category: str) -> str:
        """카테고리에 해당하는 이모지 반환"""
        emoji_map = {
            "업무": "📋",
            "영업": "💼",
            "기술": "🔧",
            "기타": "📌"
        }
        return emoji_map.get(category, "📌")
