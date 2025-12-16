
import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'

// 지금은 백엔드 기능 위주로 가져와서 프론트는 뼈대만 생성해 두는 것이기 때문에
// 일단 전역에서 import 하는 방식을 사용한다. 
// 쭉 이대로 가도 괜찮고, 나중에 프론트를 손볼 때, 다시 수정해도 된다
import "@/assets/styles/base.css"
import "@/assets/styles/table.css"
import "@/assets/styles/kakaomap.css"

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
