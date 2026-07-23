"""
Daum Mail Slack Bot - 메인 프로그램
다음 메일에서 이메일을 불러와서 자동으로 분류하고 Slack에 포스팅합니다.
"""

import os
import sys
import schedule
import time
from dotenv import load_dotenv
from mail_reader import MailReader
from mail_classifier import MailClassifier
from slack_poster import SlackPoster
from typing import Dict


class DaumMailSlackBot:
    """다음 메일-Slack 연동 봇"""
    
    def __init__(self):
        """봇 초기화"""
        load_dotenv()
        
        # 환경 변수 로드
        self.daum_email = os.getenv("DAUM_EMAIL")
        self.daum_password = os.getenv("DAUM_APP_PASSWORD")
        self.slack_token = os.getenv("SLACK_BOT_TOKEN")
        self.slack_channel = os.getenv("SLACK_CHANNEL", "다음")
        self.classification_keywords = os.getenv(
            "CLASSIFICATION_KEYWORDS",
            '{"업무": ["회의", "보고"], "영업": ["고객", "제안"], "기술": ["버그", "오류"], "기타": []}'
        )
        
        # 스케줄 설정
        self.schedule_interval = int(os.getenv("SCHEDULE_INTERVAL", "5"))
        self.schedule_unit = os.getenv("SCHEDULE_UNIT", "minutes")
        
        # 모듈 초기화
        self.mail_reader = None
        self.mail_classifier = MailClassifier(self.classification_keywords)
        self.slack_poster = SlackPoster(self.slack_token)
        
        # 유효성 검사
        if not self._validate_config():
            sys.exit(1)
    
    def _validate_config(self) -> bool:
        """설정 유효성 검사"""
        required_vars = {
            "DAUM_EMAIL": self.daum_email,
            "DAUM_APP_PASSWORD": self.daum_password,
            "SLACK_BOT_TOKEN": self.slack_token
        }
        
        missing = [var for var, val in required_vars.items() if not val]
        
        if missing:
            print("❌ 필수 환경 변수가 설정되지 않았습니다:")
            for var in missing:
                print(f"  - {var}")
            print("\n💡 .env 파일을 생성하고 필요한 정보를 입력하세요.")
            print("   참고: .env.example 파일을 참고하세요.")
            return False
        
        print("✅ 설정 검증 완료")
        return True
    
    def process_emails(self) -> bool:
        """이메일 처리 메인 로직"""
        print("\n" + "="*60)
        print(f"📧 다음 메일 처리 시작 ({time.strftime('%Y-%m-%d %H:%M:%S')})")
        print("="*60)
        
        try:
            # 1. 메일 읽기 설정
            self.mail_reader = MailReader(self.daum_email, self.daum_password)
            
            if not self.mail_reader.connect():
                print("❌ 메일 서버 연결 실패")
                return False
            
            # 2. 읽지 않은 메일 불러오기
            emails = self.mail_reader.get_unread_emails(folder="INBOX", days=1)
            
            if not emails:
                print("📭 읽지 않은 이메일이 없습니다.")
                self.mail_reader.disconnect()
                return True
            
            # 3. 이메일 분류 및 Slack 포스팅
            classified_count = {}
            successful_posts = 0
            
            for email_info in emails:
                try:
                    # 분류
                    category, confidence = self.mail_classifier.classify(
                        email_info.get("subject", ""),
                        email_info.get("body_text", ""),
                        email_info.get("body_html", "")
                    )
                    
                    emoji = self.mail_classifier.get_category_emoji(category)
                    
                    print(f"\n📨 {email_info.get('subject', '제목 없음')}")
                    print(f"   분류: {emoji} {category} ({int(confidence*100)}%)")
                    
                    # Slack 포스팅
                    if self.slack_poster.post_email_as_project(
                        self.slack_channel,
                        email_info,
                        category,
                        confidence,
                        emoji
                    ):
                        successful_posts += 1
                        
                        # 읽음으로 표시
                        self.mail_reader.mark_as_read(email_info.get("id"))
                        
                        # 분류 통계
                        classified_count[category] = classified_count.get(category, 0) + 1
                    
                except Exception as e:
                    print(f"   ⚠️ 처리 오류: {e}")
                    continue
            
            # 4. 처리 완료 요약
            print("\n" + "="*60)
            print("📊 처리 완료 요약")
            print("="*60)
            print(f"총 이메일: {len(emails)}개")
            print(f"성공한 포스팅: {successful_posts}개")
            print(f"분류 현황:")
            for cat, count in classified_count.items():
                emoji = self.mail_classifier.get_category_emoji(cat)
                print(f"  {emoji} {cat}: {count}개")
            
            # 5. Slack에 요약 포스팅
            if successful_posts > 0:
                self.slack_poster.post_summary(
                    self.slack_channel,
                    successful_posts,
                    classified_count
                )
            
            self.mail_reader.disconnect()
            return True
        
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            if self.mail_reader:
                self.mail_reader.disconnect()
            return False
    
    def schedule_jobs(self):
        """스케줄링 설정"""
        print(f"⏰ 스케줄 설정: {self.schedule_interval}{self.schedule_unit}마다 실행")
        
        if self.schedule_unit == "minutes":
            schedule.every(self.schedule_interval).minutes.do(self.process_emails)
        elif self.schedule_unit == "hours":
            schedule.every(self.schedule_interval).hours.do(self.process_emails)
        elif self.schedule_unit == "days":
            schedule.every(self.schedule_interval).days.do(self.process_emails)
        else:
            print(f"⚠️ 알 수 없는 스케줄 단위: {self.schedule_unit}")
            return False
        
        return True
    
    def run_once(self):
        """한 번만 실행"""
        print("🚀 한 번만 실행 모드로 시작합니다.")
        self.process_emails()
    
    def run_scheduler(self):
        """스케줄러 실행 (지속적)"""
        print("🤖 스케줄러 모드로 시작합니다.")
        print("💡 중지하려면 Ctrl+C를 누르세요.\n")
        
        if not self.schedule_jobs():
            return
        
        # 첫 실행
        self.process_emails()
        
        # 스케줄러 반복 실행
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 1분마다 확인
        except KeyboardInterrupt:
            print("\n\n👋 봇이 종료되었습니다.")


def main():
    """메인 함수"""
    print("\n")
    print("╔════════════════════════════════════╗")
    print("║  Daum Mail Slack Bot v1.0          ║")
    print("║  다음 메일 자동 분류 & Slack 포스팅 ║")
    print("╚════════════════════════════════════╝")
    print("\n")
    
    bot = DaumMailSlackBot()
    
    # 명령어 인자 확인
    if len(sys.argv) > 1:
        if sys.argv[1] == "--once":
            bot.run_once()
        elif sys.argv[1] == "--schedule":
            bot.run_scheduler()
        else:
            print(f"❌ 알 수 없는 명령어: {sys.argv[1]}")
            print("\n사용 방법:")
            print("  python main.py --once       # 한 번만 실행")
            print("  python main.py --schedule   # 스케줄러 모드 (기본값)")
            sys.exit(1)
    else:
        # 기본값: 스케줄러 모드
        bot.run_scheduler()


if __name__ == "__main__":
    main()
