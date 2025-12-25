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

  const destOverlay = ref(null)    // 도착 마커
  const selectedDestMarker = ref(null) // 선택된 도착지의 기존 마커 (숨김 처리용)

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

  const clearDestMarker = () => {
    if (destOverlay.value) {
      destOverlay.value.setMap(null)
      destOverlay.value = null
    }
  }

  /* ---------- origin marker (고정) ---------- */
  const setOriginMarker = ({ lat, lng }) => {
    if (!map.value) return
    const kakao = window.kakao
    const pos = new kakao.maps.LatLng(lat, lng)

    // 출발지 변경되면 기존 경로는 의미 없으니 제거
    clearPolyline()
    clearDestMarker()

    if (originMarker.value) originMarker.value.setMap(null)
    if (originOverlay.value) originOverlay.value.setMap(null)

    // 네이버 지도 스타일의 출발 마커 (초록색 핀 모양)
    const content = `
      <div style="
        position: relative;
        width: 48px;
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <!-- 핀 몸체 -->
        <div style="
          position: absolute;
          top: 0;
          width: 48px;
          height: 48px;
          background: #03C75A;
          border: 4px solid white;
          border-radius: 50% 50% 50% 0;
          transform: rotate(-45deg);
          box-shadow: 0 3px 12px rgba(0, 0, 0, 0.3);
        "></div>

        <!-- 텍스트 -->
        <div style="
          position: absolute;
          top: 8px;
          margin-top : 8px;
          width: 100%;
          text-align: center;
          font-size: 13px;
          font-weight: bold;
          color: white;
          z-index: 1;
          text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        ">출발</div>
      </div>
    `

    originOverlay.value = new kakao.maps.CustomOverlay({
      position: pos,
      content: content,
      yAnchor: 0.5,
      zIndex: 10,
    })
    originOverlay.value.setMap(map.value)

    map.value.setCenter(pos)
  }

  /* ---------- destination marker (도착) ---------- */
  const setDestMarker = ({ lat, lng }) => {
    if (!map.value) return
    const kakao = window.kakao
    const pos = new kakao.maps.LatLng(lat, lng)

    // 기존 도착 마커 제거
    clearDestMarker()

    // 네이버 지도 스타일의 도착 마커 (빨간색 핀 모양)
    const content = `
      <div style="
        position: relative;
        width: 48px;
        height: 60px;
        display: flex;
        align-items: center;
        justify-content: center;
      ">
        <!-- 핀 몸체 -->
        <div style="
          position: absolute;
          top: 0;
          width: 48px;
          height: 48px;
          background: #FF5733;
          border: 4px solid white;
          border-radius: 50% 50% 50% 0;
          transform: rotate(-45deg);
          box-shadow: 0 3px 12px rgba(0, 0, 0, 0.3);
        "></div>

        <!-- 텍스트 -->
        <div style="
          position: absolute;
          top: 8px;
          margin-top: 8px;
          width: 100%;
          text-align: center;
          font-size: 13px;
          font-weight: bold;
          color: white;
          z-index: 1;
          text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        ">도착</div>
      </div>
    `

    destOverlay.value = new kakao.maps.CustomOverlay({
      position: pos,
      content: content,
      yAnchor: 0.5,
      zIndex: 10,
    })
    destOverlay.value.setMap(map.value)
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
    clearDestMarker()     // ✅ 검색 시 도착 마커도 제거
    placeResults.value = []

    const kakao = window.kakao
    const places = new kakao.maps.services.Places()

    const query = `${selectedSido.value} ${selectedGugun.value || ""} ${selectedBank.value}`.trim()

    places.keywordSearch(query, (data, status) => {
      if (status !== kakao.maps.services.Status.OK || !data?.length) {
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

        // 인포윈도우 생성 (주소 표시)
        const infowindow = new kakao.maps.InfoWindow({
          content: `<div style="padding:8px 12px;font-size:12px;white-space:nowrap;">${p.address_name || p.road_address_name || p.place_name}</div>`,
        })

        // 마우스 오버 이벤트 - 주소 표시
        kakao.maps.event.addListener(marker, "mouseover", () => {
          infowindow.open(map.value, marker)
        })

        // 마우스 아웃 이벤트 - 주소 숨김
        kakao.maps.event.addListener(marker, "mouseout", () => {
          infowindow.close()
        })

        // 클릭 이벤트 - 길찾기
        kakao.maps.event.addListener(marker, "click", () => {
          drawRouteTo({ lat, lng, name: p.place_name })   // ✅ 마커 클릭하면 길찾기
        })

        markers.value.push(marker)
      })
    })
  }

  /* ---------- route + polyline ---------- */
  const drawRouteTo = async (dest) => {
    if (!originPos.value) {
      return
    }

    try {
      clearPolyline() // ✅ 새 길찾기 시작할 때 기존 경로 제거

      const origin = `${originPos.value.lng},${originPos.value.lat}`
      const destination = `${dest.lng},${dest.lat}`

      const res = await getDirections(origin, destination)

      const path = res.data.path ?? []
      drawPolyline(path)

      // ✅ 도착 마커 표시
      setDestMarker({ lat: dest.lat, lng: dest.lng })

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
