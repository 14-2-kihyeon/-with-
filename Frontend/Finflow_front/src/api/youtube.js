// src/api/youtube.js
import api from "@/api/axios"

// 검색 (q 필수, channelId 선택)
export const searchYoutube = (q, channelId) => {
  const params = { q }
  if (channelId) params.channelId = channelId
  return api.get("/youtube/search/", { params })
}

// 상세
export const getYoutubeVideoDetail = (videoId) => {
  return api.get(`/youtube/videos/${videoId}/`)
}
