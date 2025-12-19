let _sdkPromise = null

export function useKakaoSdk() {
  const loadKakaoSdk = () => {
    if (_sdkPromise) return _sdkPromise

    _sdkPromise = new Promise((resolve, reject) => {
      // 이미 로드된 경우
      if (window.kakao?.maps) return resolve(window.kakao)

      const appkey = import.meta.env.VITE_KAKAO_JS_KEY
      if (!appkey) return reject(new Error("VITE_KAKAO_JS_KEY가 없습니다."))

      const script = document.createElement("script")
      script.src = `//dapi.kakao.com/v2/maps/sdk.js?appkey=${appkey}&autoload=false&libraries=services`
      script.onload = () => window.kakao.maps.load(() => resolve(window.kakao))
      script.onerror = () => reject(new Error("Kakao Map SDK 로드 실패"))
      document.head.appendChild(script)
    })

    return _sdkPromise
  }

  return { loadKakaoSdk }
}
