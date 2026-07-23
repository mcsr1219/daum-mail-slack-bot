"""
다음 메일 IMAP 연동 모듈
IMAP을 사용하여 다음 메일에서 이메일을 불러옵니다.
"""

import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Optional
from datetime import datetime, timedelta


class MailReader:
    """다음 메일 IMAP 클라이언트"""
    
    DAUM_IMAP_SERVER = "imap.daum.net"
    DAUM_IMAP_PORT = 993
    
    def __init__(self, email_address: str, app_password: str):
        """
        Args:
            email_address: 다음 메일 주소 (예: user@daum.net)
            app_password: 다음 메일 앱 비밀번호
        """
        self.email_address = email_address
        self.app_password = app_password
        self.imap = None
    
    def connect(self) -> bool:
        """다음 메일 IMAP 서버에 연결"""
        try:
            self.imap = imaplib.IMAP4_SSL(self.DAUM_IMAP_SERVER, self.DAUM_IMAP_PORT)
            self.imap.login(self.email_address, self.app_password)
            print(f"✅ {self.email_address}로 다음 메일 연결 성공")
            return True
        except imaplib.IMAP4.error as e:
            print(f"❌ IMAP 연결 실패: {e}")
            return False
        except Exception as e:
            print(f"❌ 예상치 못한 오류: {e}")
            return False
    
    def disconnect(self):
        """IMAP 연결 종료"""
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
                print("✅ IMAP 연결 종료")
            except Exception as e:
                print(f"❌ 연결 종료 중 오류: {e}")
    
    def get_unread_emails(self, folder: str = "INBOX", days: int = 1) -> List[Dict]:
        """
        읽지 않은 이메일 불러오기
        
        Args:
            folder: 메일함 이름 (기본값: INBOX)
            days: 며칠 전부터 조회할지 (기본값: 1일)
        
        Returns:
            이메일 정보 리스트
        """
        emails = []
        try:
            # 메일함 선택
            status, mailbox = self.imap.select(folder)
            if status != "OK":
                print(f"❌ 메일함 선택 실���: {folder}")
                return emails
            
            # 날짜 기준으로 검색
            search_date = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
            status, email_ids = self.imap.search(
                None, 
                f'UNSEEN SINCE "{search_date}"'
            )
            
            if status != "OK":
                print("❌ 이메일 검색 실패")
                return emails
            
            # 각 이메일 처리
            for email_id in email_ids[0].split():
                status, msg_data = self.imap.fetch(email_id, "(RFC822)")
                if status != "OK":
                    continue
                
                try:
                    msg = email.message_from_bytes(msg_data[0][1])
                    email_info = self._parse_email(msg, email_id)
                    if email_info:
                        emails.append(email_info)
                except Exception as e:
                    print(f"⚠️ 이메일 파싱 오류: {e}")
                    continue
            
            print(f"✅ {len(emails)}개의 읽지 않은 이메일 로드됨")
            return emails
        
        except Exception as e:
            print(f"❌ 이메일 조회 중 오류: {e}")
            return emails
    
    def _parse_email(self, msg: email.message.Message, email_id: bytes) -> Optional[Dict]:
        """이메일 메시지 파싱"""
        try:
            # 제목
            subject = self._decode_header(msg.get("Subject", "제목 없음"))
            
            # 발신자
            sender = self._decode_header(msg.get("From", "발신자 없음"))
            
            # 수신일
            date_str = msg.get("Date", "")
            
            # 본문 추출
            body_text = ""
            body_html = ""
            
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    
                    if content_type == "text/plain":
                        try:
                            body_text = part.get_payload(decode=True).decode(
                                part.get_content_charset() or 'utf-8',
                                errors='ignore'
                            )
                        except:
                            body_text = part.get_payload(decode=False)
                    
                    elif content_type == "text/html":
                        try:
                            body_html = part.get_payload(decode=True).decode(
                                part.get_content_charset() or 'utf-8',
                                errors='ignore'
                            )
                        except:
                            body_html = part.get_payload(decode=False)
            else:
                content_type = msg.get_content_type()
                payload = msg.get_payload(decode=True)
                
                if content_type == "text/plain":
                    body_text = payload.decode(
                        msg.get_content_charset() or 'utf-8',
                        errors='ignore'
                    )
                elif content_type == "text/html":
                    body_html = payload.decode(
                        msg.get_content_charset() or 'utf-8',
                        errors='ignore'
                    )
            
            # 본문이 없으면 일부만 사용
            if not body_text and not body_html:
                body_text = msg.get_payload()
            
            return {
                "id": email_id.decode() if isinstance(email_id, bytes) else email_id,
                "subject": subject,
                "sender": sender,
                "date": date_str,
                "body_text": body_text[:500] if body_text else "",  # 처음 500자
                "body_html": body_html,
                "full_body_text": body_text  # 전체 본문 (분류용)
            }
        
        except Exception as e:
            print(f"⚠️ 이메일 파싱 중 오류: {e}")
            return None
    
    def _decode_header(self, header: str) -> str:
        """헤더 디코딩"""
        if not header:
            return ""
        
        try:
            decoded_parts = decode_header(header)
            decoded_string = ""
            
            for part, charset in decoded_parts:
                if isinstance(part, bytes):
                    decoded_string += part.decode(charset or 'utf-8', errors='ignore')
                else:
                    decoded_string += part
            
            return decoded_string
        except Exception:
            return header
    
    def mark_as_read(self, email_id: str) -> bool:
        """이메일을 읽음으로 표시"""
        try:
            self.imap.store(email_id, '+FLAGS', '\\Seen')
            return True
        except Exception as e:
            print(f"⚠️ 읽음 표시 실패: {e}")
            return False
