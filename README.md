# Daum Mail Slack Bot 🤖

다음 메일에서 이메일을 자동으로 불러와서 본문 내용에 따라 분류하고, Slack의 '다음' 채널에 프로젝트 형식으로 추가하는 봇입니다.

## 🌟 기능

- ✅ 다음 메일 IMAP 연동
- ✅ 이메일 본문 내용 기반 자동 분류
- ✅ Slack API 연동
- ✅ 프로젝트 항목 자동 생성
- ✅ 정기적 자동 실행 (스케줄링)

## 🛠️ 필요한 것

- Python 3.8+
- 다음 메일 계정
- Slack 워크스페이스 및 토큰
- 다음 메일 앱 비밀번호

## 📦 설치 방법

```bash
# 저장소 클론
git clone https://github.com/mcsr1219/daum-mail-slack-bot.git
cd daum-mail-slack-bot

# 가상 환경 생성
python -m venv venv

# 가상 환경 활성화
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

## ⚙️ 설정

1. `.env` 파일 생성
2. 필요한 정보 입력 (아래 참고)
3. `python main.py` 실행

## 🔑 환경 변수 (.env)

```
DAUM_EMAIL=your-email@daum.net
DAUM_PASSWORD=your-app-password
SLACK_TOKEN=xoxb-your-token
SLACK_CHANNEL=다음
CLASSIFICATION_KEYWORDS={"category1": ["keyword1", "keyword2"], ...}
```

## 📝 사용 방법

```bash
python main.py
```

## 📄 라이선스

MIT
