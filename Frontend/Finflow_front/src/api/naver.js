// src/api/naver.js
import api from "@/api/axios" // 너가 이미 쓰고 있는 axios 인스턴스 파일 경로 기준

export const naverApi = {
  search(q) {
    return api.get("/naver/news/search/", { params: { q } }).then(r => r.data)
  },
  list() {
    return api.get("/naver/news/").then(r => r.data)
  },
  detail(id) {
    return api.get(`/naver/news/${id}/`).then(r => r.data)
  },
  toggleBookmark(id) {
    return api.post(`/naver/news/${id}/bookmark/`).then(r => r.data)
  },
  summarize(id) {
    return api.post(`/naver/news/${id}/summary/`).then(r => r.data)
  },
}
