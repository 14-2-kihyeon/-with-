- 완료 후 예상 Frontend 경로 
```
src/
  api/
    axios.js          // baseURL, interceptor, refresh
    auth.js           // login/logout/register API 함수만
    finances.js
    posts.js
    naver.js
  stores/
    auth.js
  router/
    index.js
  views/
    LoginView.vue
    SignupView.vue
    HomeView.vue
    MyPageView.vue
    // 이후: PostsListView, PostsDetailView, DepositView, SavingView, NewsView, MapView
  components/
    common/
      NavBar.vue
      Toast.vue (선택)
```

# 특이사항 체크

### git add 수행 후 경고 문구
![줄바꿈 경고](./README전용%20picture/git%20경고%20문구/git%20add%20수행%20후%20경고%20문구.PNG)
```
이 경고는 에러가 아니라 줄바꿈(EOL) 변환 안내이다.
지금 파일들은 LF(유닉스 줄바꿈)으로 저장되어 있는데,
나는 Windows환경이라서 다음에 git 파일을 건드릴 때, CRLF(윈도우 줄바꿈)으로 바뀔 수 있다는 경고이다.

커밋/푸시 자체는 그대로 가능하다
하지만 줄바꿈이 제멋대로 바뀌어서 diff가 더러워지는 문제를 막으려면 설정을 해주는 게 좋다

diff는 마지막 관통 라이브때 배웠다.
jsdiff -> javascript로 텍스트 구분을 구현한 것
이전 텍스트와 새 텍스트를 받아서 두 텍스트의 차이를 구분
```

### 이 경고 문구에 대한 해결법은 일단 메모 후 나중에 다시 알아볼 것

![줄바꿈 에러 추천](./README전용%20picture/git%20경고%20문구/줄바꿈%20에러%20해결.PNG)
---
![줄바꿈 에러 선택](./README전용%20picture/git%20경고%20문구/줄바꿈%20에러%20선택.PNG)



