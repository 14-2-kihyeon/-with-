# vue - Front 뼈대 구조

![프론트 뼈대 구조](./README전용%20picture/frontend%20구조/Frontend%20구조%20뼈대.PNG)
---
- src/api/
```
역할 : "백엔드에 요청 보내는 방법"을 한 곳에 모아두는 영역
axios.js : JWT(Access) 토큰과 refresh발급 << 거의 모든 작업에서 이루어짐
그래서 이런 공통 네트워크 규칙을 한 번에 관리해서 반복 작업을 줄인다
>> 솔직히 반쯤만 이해가 된다

finances.js : 예금/적금처럼 특정 도메인에 대한 API함수만 모아두기
사실 그림상으로는 stores에 배치가 맞긴함
근데 이 파일의 코드는  예금/적금이 백엔드에서 다른 금융감독원의 데이터를 가져와 GET 방식만 사용하기 때문에 상태 관리(stores)에 의미적(?)으로는 부합하지 않음 / 추가로 gpt가 추천(이유를 봤는데 기어기..)
```
<br>
<br>

- src/assets/styles
```
역할: 스타일을 목적별로 분리해서 유지보수 쉽게
base.css, table.css, finances.css

base.css, table.css는 지금 main.js에서 import해서 사용중

지금 3개의 css파일이 존재하는데 base는 말 그대로 프로젝트 전역을 담당(글꼴, 폰트 등등)
table.css는 예금, 적금을 조회할때 사용했는데, 표 안에 데이터를 넣고, 나중에 표를 또 사용할 가능성이 있기에 전역에 빼둔 것

finances.css는 예금, 적금 전용 css / 도메인 별로 css를 나누어 써야 유지보수가 쉽기 때문 
저기 밑의 router-index.js 구조를 살펴본 후 아래의 FinLayout 그림을 살펴보면 css파일을 import하는 방식이 다르다
```

![assets-css](./README전용%20picture/frontend%20구조/main-js.PNG)

<br>

- FinLayout -> css scoped -> import 방식
![import-finances.css](./README전용%20picture/frontend%20구조/finances%20import.PNG)

<br>
<br>





- src/layouts/
```
역할 : 여러 페이지에서 반복되는 "공통 레이아웃"을 담당 
우리가 지금까지 알고 있던 MainView와 같은 것

MainView가 있는데 왜 굳이 MainView 위에 MainLayout을 만드나요 ?
일단 아래 그림의 라우터 구조 파악이 중요

MainLayout 하위 
    main뷰
    auth 관련
    posts 관련
    finances 관련 하위
        예금, 적금


이를 중첩 라우터 구조라 함 -> 이 구조의 장점은

1. 공통 UI를 한 번만 정의할 수 있다(css같은 ??)
2. URL 구조를 "도메인 단위로 묶기 쉽다"
3. 팀 협업이 쉽다. 각 도메인별로 나뉘어 있기에 맡은 부분만 건드릴 수가 있다
4. 

```
![라우터-인덱스](./README전용%20picture/frontend%20구조/라우터-인덱스.PNG)


<br>
<br>
<br>

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



