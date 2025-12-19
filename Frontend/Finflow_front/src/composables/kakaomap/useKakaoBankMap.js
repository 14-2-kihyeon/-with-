// src/composables/kakaomap/useKakaoBankMap.js
import { ref } from "vue"
import { useKakaoSdk } from "@/composables/kakaomap/useKakaoSdk"
import { getDirections } from "@/api/kakao"
import bankMapData from "@/assets/data/bank_map_data.json"

export function useKakaoBankMap() {
  const { loadKakaoSdk } = useKakaoSdk()

  const map = ref(null)
  const markers = ref([])          // 은행 마커만
  const polyline = ref(null)

  const originPos = ref(null)      // { lat, lng }
  const originMarker = ref(null)
  const originOverlay = ref(null)

  const mapInfo = ref([])
  const bankInfo = ref([])

  const selectedSido = ref("")
  const selectedGugun = ref("")
  const selectedBank = ref("")

  const sidoList = ref([])
  const gugunList = ref([])
  const bankList = ref([])
  const placeResults = ref([])

  /* ---------- clear helpers ---------- */
  const clearMarkers = () => {
    markers.value.forEach((m) => m.setMap(null))
    markers.value = []
  }

  const clearPolyline = () => {
    if (polyline.value) {
      polyline.value.setMap(null)
      polyline.value = null
    }
  }

  /* ---------- origin marker (고정) ---------- */
  const setOriginMarker = ({ lat, lng }) => {
    if (!map.value) return
    const kakao = window.kakao
    const pos = new kakao.maps.LatLng(lat, lng)

    // 출발지 변경되면 기존 경로는 의미 없으니 제거
    clearPolyline()

    if (originMarker.value) originMarker.value.setMap(null)
    if (originOverlay.value) originOverlay.value.setMap(null)

    const imgSrc =
      "https://t1.daumcdn.net/localimg/localimages/07/mapapidoc/markerStar.png"
    const imgSize = new kakao.maps.Size(24, 35)
    const markerImage = new kakao.maps.MarkerImage(imgSrc, imgSize)

    originMarker.value = new kakao.maps.Marker({
      map: map.value,
      position: pos,
      title: "내 위치(출발지)",
      image: markerImage,
      zIndex: 10,
    })

    originOverlay.value = new kakao.maps.CustomOverlay({
      position: pos,
      content: `<div class="map-origin-label">내 위치</div>`,
      yAnchor: 2.2,
    })
    originOverlay.value.setMap(map.value)

    map.value.setCenter(pos)
  }

  /* ---------- map init ---------- */
  const initMap = (container) => {
    const kakao = window.kakao
    const defaultCenter = new kakao.maps.LatLng(35.1796, 129.0756)
    map.value = new kakao.maps.Map(container, {
      center: defaultCenter,
      level: 5,
    })
  }

  /* ---------- data init ---------- */
  const loadBankMapData = async () => {
    mapInfo.value = bankMapData.mapInfo ?? []
    bankInfo.value = bankMapData.bankInfo ?? []
  }

  const initSelectData = () => {
    sidoList.value = mapInfo.value.map((x) => x.name)
    bankList.value = [...bankInfo.value]
    selectedSido.value = ""
    selectedGugun.value = ""
    selectedBank.value = ""
    gugunList.value = []
  }

  const onSidoChange = () => {
    selectedGugun.value = ""
    const found = mapInfo.value.find((x) => x.name === selectedSido.value)
    gugunList.value = found?.countries ?? []

    // 지역 바뀌면 경로 제거 (이전 경로 유지할 이유 없음)
    clearPolyline()
  }

  /* ---------- origin setters ---------- */
  const requestMyLocation = () => {
    return new Promise((resolve, reject) => {
      if (!navigator.geolocation) return reject(new Error("Geolocation not supported"))

      navigator.geolocation.getCurrentPosition(
        (pos) => {
          originPos.value = {
            lat: pos.coords.latitude,
            lng: pos.coords.longitude,
          }
          setOriginMarker(originPos.value)
          resolve(originPos.value)
        },
        reject,
        { enableHighAccuracy: true, timeout: 8000 }
      )
    })
  }

  const setOriginByKeyword = (keyword) => {
    const kakao = window.kakao
    const places = new kakao.maps.services.Places()

    places.keywordSearch(keyword, (data, status) => {
      if (status !== kakao.maps.services.Status.OK || !data?.length) {
        alert("출발지를 찾을 수 없습니다.")
        return
      }
      const top = data[0]
      originPos.value = { lat: Number(top.y), lng: Number(top.x) }
      setOriginMarker(originPos.value)
    })
  }

  /* ---------- bounds helper (출발+도착+경로가 한 화면에 보이게) ---------- */
  const fitBoundsToRoute = (path, dest) => {
    if (!map.value || !originPos.value || !dest) return
    const kakao = window.kakao

    const bounds = new kakao.maps.LatLngBounds()

    // 출발/도착
    bounds.extend(new kakao.maps.LatLng(originPos.value.lat, originPos.value.lng))
    bounds.extend(new kakao.maps.LatLng(dest.lat, dest.lng))

    // 경로까지 포함하면 더 안정적으로 화면 맞춰짐
    ;(path ?? []).forEach((p) => {
      bounds.extend(new kakao.maps.LatLng(p.lat, p.lng))
    })

    map.value.setBounds(bounds)
  }

  /* ---------- search banks (Places) ---------- */
  const searchBanks = () => {
    if (!map.value) return
    if (!selectedSido.value) return alert("시/도를 선택해주세요.")
    if (!selectedBank.value) return alert("은행을 선택해주세요.")

    clearMarkers()
    clearPolyline()       // ✅ 검색 시 이전 경로 제거
    placeResults.value = []

    const kakao = window.kakao
    const places = new kakao.maps.services.Places()

    const query = `${selectedSido.value} ${selectedGugun.value || ""} ${selectedBank.value}`.trim()

    places.keywordSearch(query, (data, status) => {
      if (status !== kakao.maps.services.Status.OK || !data?.length) {
        alert("검색 결과가 없습니다.")
        return
      }

      placeResults.value = data
      map.value.setCenter(new kakao.maps.LatLng(Number(data[0].y), Number(data[0].x)))

      data.forEach((p) => {
        const lat = Number(p.y)
        const lng = Number(p.x)

        const marker = new kakao.maps.Marker({
          map: map.value,
          position: new kakao.maps.LatLng(lat, lng),
          title: p.place_name,
        })

        kakao.maps.event.addListener(marker, "click", () => {
          drawRouteTo({ lat, lng })   // ✅ 마커 클릭하면 길찾기
        })

        markers.value.push(marker)
      })
    })
  }

  /* ---------- route + polyline ---------- */
  const drawRouteTo = async (dest) => {
    if (!originPos.value) {
      alert("출발지를 먼저 설정해주세요. (내 위치 또는 키워드)")
      return
    }

    try {
      clearPolyline() // ✅ 새 길찾기 시작할 때 기존 경로 제거

      const origin = `${originPos.value.lng},${originPos.value.lat}`
      const destination = `${dest.lng},${dest.lat}`

      const res = await getDirections(origin, destination)

      const path = res.data.path ?? []
      drawPolyline(path)

      // ✅ 출발/도착/경로가 한 화면에 보이도록 자동 줌
      fitBoundsToRoute(path, dest)
    } catch (e) {
      console.error("route error:", e?.response?.data || e)
      alert(e?.response?.data?.detail || "경로를 불러올 수 없습니다.")
    }
  }

  const drawPolyline = (path) => {
    const kakao = window.kakao
    clearPolyline()

    const linePath = (path ?? []).map((p) => new kakao.maps.LatLng(p.lat, p.lng))

    polyline.value = new kakao.maps.Polyline({
      map: map.value,
      path: linePath,
      strokeWeight: 5,
      strokeOpacity: 0.85,
    })
  }

  return {
    loadKakaoSdk,
    initMap,

    loadBankMapData,
    initSelectData,

    selectedSido,
    selectedGugun,
    selectedBank,
    sidoList,
    gugunList,
    bankList,
    onSidoChange,

    requestMyLocation,
    setOriginByKeyword,

    searchBanks,
    placeResults,
  }
}
