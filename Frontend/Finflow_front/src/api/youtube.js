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

// 나중에 볼 영상 토글
export const toggleWatchLater = (videoId, videoData) => {
  return api.post(`/accounts/youtube/videos/${videoId}/watch-later/`, videoData)
}

// 채널 구독 토글
export const toggleChannelSubscribe = (channelId, channelData) => {
  return api.post(`/accounts/youtube/channels/${channelId}/subscribe/`, channelData)
}

// 나중에 볼 영상 목록 조회
export const getWatchLaterList = () => {
  return api.get("/accounts/youtube/watch-later/")
}

// 구독한 채널 목록 조회
export const getYoutubeSubscriptions = () => {
  return api.get("/accounts/youtube/subscriptions/")
}
