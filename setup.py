"""
설정 가이드 및 설치 스크립트
"""

from setuptools import setup, find_packages

setup(
    name="daum-mail-slack-bot",
    version="1.0.0",
    description="다음 메일에서 이메일을 자동으로 불러와서 분류하고 Slack에 포스팅하는 봇",
    author="mcsr1219",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "python-dotenv==1.0.0",
        "slack-sdk==3.23.0",
        "imapclient==3.0.1",
        "pyzmail36==1.0.4",
        "beautifulsoup4==4.12.2",
        "requests==2.31.0",
        "schedule==1.2.0",
    ],
    python_requires=">=3.8",
    entry_points={
        "console_scripts": [
            "daum-mail-slack-bot=main:main",
        ],
    },
)
