// src/api/kakao.js
import api from "@/api/axios"

export const getDirections = (origin, destination) => {
  return api.get("/kakaomap/route/", {
    params: { origin, destination },
  })
}
