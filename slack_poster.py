"""
Slack 포스팅 모듈
분류된 이메일을 Slack 채널에 프로젝트 형식으로 추가합니다.
"""

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from typing import Dict, Optional


class SlackPoster:
    """Slack에 메시지를 포스팅하는 클래스"""
    
    def __init__(self, bot_token: str):
        """
        Args:
            bot_token: Slack Bot 토큰 (xoxb-...)
        """
        self.client = WebClient(token=bot_token)
    
    def post_email_as_project(
        self,
        channel: str,
        email_info: Dict,
        category: str,
        confidence: float,
        category_emoji: str
    ) -> bool:
        """
        이메일을 Slack 채널에 프로젝트 항목 형식으로 포스팅
        
        Args:
            channel: Slack 채널명 (# 포함, 예: '#다음')
            email_info: 이메일 정보 딕셔너리
            category: 분류 카테고리
            confidence: 분류 신뢰도 (0-1)
            category_emoji: 카테고리 이모지
        
        Returns:
            성공 여부
        """
        try:
            # 채널명 정규화
            if not channel.startswith('#'):
                channel = f"#{channel}"
            
            # 신뢰도 표시 (별)
            confidence_stars = "⭐" * int(confidence * 5)
            
            # 본문 요약 (처음 100자)
            body_preview = email_info.get("body_text", "")[:100]
            if len(email_info.get("body_text", "")) > 100:
                body_preview += "..."
            
            # Block Kit으로 포맷팅
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"{category_emoji} *[{category}] {email_info.get('subject', '제목 없음')}*"
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*발신자:*\n{email_info.get('sender', '알 수 없음')}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*신뢰도:*\n{confidence_stars} ({int(confidence * 100)}%)"
                        }
                    ]
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*본문 요약:*\n```{body_preview}```"
                    }
                },
                {
                    "type": "divider"
                }
            ]
            
            # 메시지 포스팅
            response = self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=f"[{category}] {email_info.get('subject', '제목 없음')}"  # 폴백 텍스트
            )
            
            print(f"✅ Slack에 포스팅 완료: {email_info.get('subject', '제목 없음')} ({category})")
            return True
        
        except SlackApiError as e:
            print(f"❌ Slack 포스팅 실패: {e.response['error']}")
            return False
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            return False
    
    def post_summary(self, channel: str, total: int, classified: Dict[str, int]) -> bool:
        """
        처리 요약을 Slack에 포스팅
        
        Args:
            channel: Slack 채널명
            total: 처리된 총 이메일 수
            classified: 카테고리별 이메일 수
        
        Returns:
            성공 여부
        """
        try:
            if not channel.startswith('#'):
                channel = f"#{channel}"
            
            # 분류 현황 텍스트 생성
            classification_text = "\n".join(
                [f"• {cat}: {count}개" for cat, count in classified.items()]
            )
            
            blocks = [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"📊 *다음 메일 처리 완료*\n총 {total}개 이메일 분류됨\n\n{classification_text}"
                    }
                }
            ]
            
            self.client.chat_postMessage(
                channel=channel,
                blocks=blocks,
                text=f"📊 다음 메일 처리 완료: {total}개"
            )
            
            print(f"✅ 요약 메시지 포스팅 완료")
            return True
        
        except SlackApiError as e:
            print(f"⚠️ 요약 포스팅 실패: {e.response['error']}")
            return False
        except Exception as e:
            print(f"⚠️ 예상치 못한 오류: {e}")
            return False
