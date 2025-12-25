# Alert를 Modal로 변경 가이드

## 생성된 파일

1. **AlertModal.vue** - 재사용 가능한 모달 컴포넌트
   - 위치: `src/components/common/AlertModal.vue`

2. **useAlert.js** - Alert composable
   - 위치: `src/composables/useAlert.js`

## 사용 방법

### 1. 기본 구조

```vue
<template>
  <div>
    <!-- AlertModal 추가 -->
    <AlertModal
      v-model="showAlert"
      :icon="alertConfig.icon"
      :title="alertConfig.title"
      :message="alertConfig.message"
      :confirm-text="alertConfig.confirmText"
      :cancel-text="alertConfig.cancelText"
      :show-cancel="alertConfig.showCancel"
      :hint="alertConfig.hint"
      @confirm="alertConfig.onConfirm"
      @cancel="alertConfig.onCancel"
    />

    <!-- 기존 컨텐츠 -->
  </div>
</template>

<script setup>
import AlertModal from "@/components/common/AlertModal.vue"
import { useAlert } from "@/composables/useAlert"

// Alert composable 사용
const { showAlert, alertConfig, alert, success, error, warning, confirm } = useAlert()

// 기존 코드에서 alert() 호출을 아래와 같이 변경
</script>
```

### 2. alert() 대체 예시

#### Before (기존 코드)
```javascript
alert("로그인에 성공했습니다!")
```

#### After (변경 후)
```javascript
success("로그인에 성공했습니다!")
```

### 3. confirm() 대체 예시

#### Before
```javascript
if (confirm("정말 삭제하시겠습니까?")) {
  // 삭제 로직
}
```

#### After
```javascript
const result = await confirm("정말 삭제하시겠습니까?")
if (result) {
  // 삭제 로직
}
```

### 4. useAlert() 메서드

- `alert(message, options)` - 기본 알림
- `success(message, options)` - 성공 메시지 (✅ 아이콘)
- `error(message, options)` - 오류 메시지 (⚠️ 아이콘)
- `warning(message, options)` - 경고 메시지 (⚠️ 아이콘)
- `info(message, options)` - 정보 메시지 (ℹ️ 아이콘)
- `confirm(message, options)` - 확인/취소 선택 (Promise 반환)

### 5. Options 파라미터

```javascript
{
  icon: '🎉',              // 아이콘 (이모지)
  title: '알림',           // 제목
  confirmText: '확인',     // 확인 버튼 텍스트
  cancelText: '취소',      // 취소 버튼 텍스트
  showCancel: false,       // 취소 버튼 표시 여부
  hint: '힌트 메시지',     // 하단 힌트
  onConfirm: () => {},     // 확인 시 콜백
  onCancel: () => {}       // 취소 시 콜백
}
```

---

## 파일별 변경 사항

### ✅ 완료된 파일

1. **SignupView.vue** - 회원가입 완료 메시지

---

## 🔄 변경 대기 파일 (13개)

### 1. MyPageView.vue
```javascript
// Line 찾기: alert(
// 예상 위치: 프로필 저장, 탈퇴 등

// Before
alert("프로필이 저장되었습니다.")

// After
success("프로필이 저장되었습니다.")
```

### 2. InvestmentSurveyView.vue
```javascript
// 설문 제출 완료 시

// Before
alert("설문이 완료되었습니다!")

// After
success("설문이 완료되었습니다!", {
  icon: '🎉',
  title: '설문 완료',
  onConfirm: () => {
    // 다음 페이지로 이동
  }
})
```

### 3. RecommendationsView.vue
```javascript
// 추천 상품 북마크 등

// Before
alert("상품이 저장되었습니다.")

// After
success("상품이 저장되었습니다.")
```

### 4. PostCreateView.vue
```javascript
// 게시글 작성 완료

// Before
alert("게시글이 작성되었습니다.")
router.push(...)

// After
success("게시글이 작성되었습니다.", {
  onConfirm: () => {
    router.push(...)
  }
})
```

### 5. PostEditView.vue
```javascript
// 게시글 수정 완료

// Before
alert("게시글이 수정되었습니다.")

// After
success("게시글이 수정되었습니다.")
```

### 6. PostDetailView.vue
```javascript
// 게시글 삭제 확인

// Before
if (confirm("정말 삭제하시겠습니까?")) {
  await deletePost()
}

// After
const result = await confirm("정말 삭제하시겠습니까?", {
  icon: '🗑️',
  title: '게시글 삭제',
  confirmText: '삭제',
  cancelText: '취소'
})
if (result) {
  await deletePost()
}
```

### 7. ChatbotWidget.vue
```javascript
// 챗봇 오류 메시지

// Before
alert("챗봇 서비스에 문제가 발생했습니다.")

// After
error("챗봇 서비스에 문제가 발생했습니다.")
```

### 8. ChannelsView.vue (YouTube)
```javascript
// 채널 구독/구독 취소

// Before
alert("구독이 완료되었습니다.")

// After
success("구독이 완료되었습니다!", {
  icon: '🔔'
})
```

### 9. SavedVideosView.vue
```javascript
// 저장된 영상 삭제

// Before
if (confirm("영상을 삭제하시겠습니까?")) {
  deleteVideo()
}

// After
const result = await confirm("영상을 삭제하시겠습니까?")
if (result) {
  deleteVideo()
}
```

### 10. VideoDetailView.vue
```javascript
// 영상 저장

// Before
alert("나중에 볼 영상에 추가되었습니다.")

// After
success("나중에 볼 영상에 추가되었습니다!", {
  icon: '📌'
})
```

### 11. BankMapView.vue
```javascript
// 이미 커스텀 모달 사용 중 - 변경 불필요
// 다만 다른 alert가 있다면 변경
```

### 12. FinHomeView.vue
```javascript
// 상품 저장, 비교 등

// Before
alert("관심 상품에 추가되었습니다.")

// After
success("관심 상품에 추가되었습니다!", {
  icon: '⭐'
})
```

---

## 빠른 적용 템플릿

모든 파일에 아래를 추가:

### Template에 추가
```vue
<AlertModal
  v-model="showAlert"
  :icon="alertConfig.icon"
  :title="alertConfig.title"
  :message="alertConfig.message"
  :confirm-text="alertConfig.confirmText"
  :cancel-text="alertConfig.cancelText"
  :show-cancel="alertConfig.showCancel"
  :hint="alertConfig.hint"
  @confirm="alertConfig.onConfirm"
  @cancel="alertConfig.onCancel"
/>
```

### Script에 추가
```javascript
import AlertModal from "@/components/common/AlertModal.vue"
import { useAlert } from "@/composables/useAlert"

const { showAlert, alertConfig, alert, success, error, warning, confirm } = useAlert()
```

---

## 스타일 특징

- 📍 **아이콘 애니메이션**: 펄스 효과 (2초 주기)
- 🎨 **그라데이션 버튼**: 보라색 그라데이션
- ✨ **슬라이드 업**: 30px 아래에서 올라오며 페이드인
- 🌫️ **블러 배경**: backdrop-filter로 배경 흐림 효과
- 📱 **반응형**: 모바일에서도 잘 보임 (width: 90%, max-width: 420px)

---

## 마이그레이션 체크리스트

- [x] AlertModal.vue 생성
- [x] useAlert.js composable 생성
- [x] SignupView.vue 변경 완료
- [ ] MyPageView.vue
- [ ] InvestmentSurveyView.vue
- [ ] RecommendationsView.vue
- [ ] PostCreateView.vue
- [ ] PostEditView.vue
- [ ] PostDetailView.vue
- [ ] ChatbotWidget.vue
- [ ] ChannelsView.vue
- [ ] SavedVideosView.vue
- [ ] VideoDetailView.vue
- [ ] FinHomeView.vue

---

## 테스트 사항

각 파일 변경 후 확인:
1. ✅ 모달이 잘 표시되는가?
2. ✅ 버튼 클릭 시 동작하는가?
3. ✅ 애니메이션이 부드러운가?
4. ✅ ESC 키로 닫히는가? (배경 클릭)
5. ✅ 모바일에서도 잘 보이는가?
