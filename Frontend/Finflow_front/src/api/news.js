// src/api/news.js
import api from "@/api/axios";

export const newsApi = {
  search: (q) => api.get("/naver/news/search/", { params: { q } }),
  list: () => api.get("/naver/news/"),
  detail: (id) => api.get(`/naver/news/${id}/`),
  toggleBookmark: (id) => api.post(`/naver/news/${id}/bookmark/`),
  summarize: (id) => api.post(`/naver/news/${id}/summary/`),
};
