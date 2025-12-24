# 챗봇 이미지 파일 가이드

이 폴더에는 챗봇의 위젯 버튼 이미지와 프로필 이미지를 저장합니다.

## 📁 필요한 이미지 파일 (총 8개)

### 위젯 버튼 이미지 (플로팅 버튼에 표시)
1. **guest-widget.png** - 비로그인 사용자용 위젯 이미지
2. **timid-widget.png** - 안정형 투자자용 위젯 이미지
3. **normal-widget.png** - 중립형 투자자용 위젯 이미지
4. **speculative-widget.png** - 공격형 투자자용 위젯 이미지

### 프로필 이미지 (헤더와 메시지에 표시)
5. **guest-profile.png** - 비로그인 사용자용 프로필 이미지
6. **timid-profile.png** - 안정형 투자자용 프로필 이미지
7. **normal-profile.png** - 중립형 투자자용 프로필 이미지
8. **speculative-profile.png** - 공격형 투자자용 프로필 이미지

## 🎨 이미지 사양

### 위젯 이미지 (widget)
- 권장 크기: 70x70px ~ 200x200px
- 형식: PNG (투명 배경 권장)
- 용도: 화면 오른쪽 하단의 플로팅 버튼

### 프로필 이미지 (profile)
- 권장 크기: 100x100px ~ 300x300px
- 형식: PNG (투명 배경 권장)
- 용도: 채팅창 헤더, AI 메시지 옆 아바타

## 🎯 투자 성향별 컬러 가이드

- **안정형 (timid)**: 파란색 계열 (#3b82f6) - 신뢰감, 안정감
- **중립형 (normal)**: 파란색/녹색 혼합 - 균형감
- **공격형 (speculative)**: 녹색 계열 (#10b981) - 역동성, 성장

## ⚠️ 임시 이미지 안내

이미지가 없는 경우 🤖 이모지가 대신 표시됩니다.
브라우저 개발자 도구(F12) > Console 탭에서 어떤 이미지가 로드되지 않았는지 확인할 수 있습니다.

## 📝 이미지 변경 방법

1. 원하는 이미지를 위 파일명으로 이 폴더에 저장
2. 브라우저 새로고침 (Ctrl + F5로 캐시 무시)
3. 콘솔에서 "widgetImage: [타입] → [경로]" 로그 확인

## 💡 코드에서 이미지 경로 변경하기

`src/components/common/ChatbotWidget.vue` 파일의 232~271번째 줄에서
`CHATBOT_IMAGES` 객체의 경로를 수정하면 됩니다.

```javascript
const CHATBOT_IMAGES = {
  widget: {
    'guest': '/assets/chatbot/guest-widget.png',
    // ... 경로를 원하는 대로 수정
  },
  profile: {
    'guest': '/assets/chatbot/guest-profile.png',
    // ... 경로를 원하는 대로 수정
  }
}
```
