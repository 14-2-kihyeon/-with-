import requests
from django.conf import settings

BASE_URL = "https://finlife.fss.or.kr/finlifeapi/depositProductsSearch.json"
BASE_URL_SAVING = "https://finlife.fss.or.kr/finlifeapi/savingProductsSearch.json"

def fetch_deposit_products():
    """예금 상품 API 호출"""
    try:
        params = {
            "auth": settings.API_KEY,
            "topFinGrpNo": "020000",
            "pageNo": 1
        }
        
        print(f"[API] 호출: {BASE_URL}")
        print(f"[API] 파라미터: {params}")

        response = requests.get(BASE_URL, params=params, timeout=10)

        if response.status_code != 200:
            print(f"[오류] HTTP 오류: {response.status_code}")
            print(response.text)
            return None

        data = response.json()
        result = data.get("result", {})

        # API 오류 체크
        if result.get("err_cd") != "000":
            print(f"[오류] API 오류: {result.get('err_msg')}")
            return None

        print(f"[성공] 예금 상품 {len(result.get('baseList', []))}개 받음")
        return result

    except requests.exceptions.Timeout:
        print("[오류] API 요청 시간 초과")
        return None
    except Exception as e:
        print(f"[오류] API 호출 실패: {e}")
        return None


def fetch_saving_products():
    """적금 상품 API 호출"""
    try:
        params = {
            "auth": settings.API_KEY,
            "topFinGrpNo": "020000",
            "pageNo": 1  # ✅ 5 → 1로 수정
        }
        
        print(f"[API] 호출: {BASE_URL_SAVING}")

        response = requests.get(BASE_URL_SAVING, params=params, timeout=10)

        if response.status_code != 200:
            print(f"[오류] HTTP 오류: {response.status_code}")
            print(response.text)
            return None

        data = response.json()
        result = data.get("result", {})

        if result.get("err_cd") != "000":
            print(f"[오류] API 오류: {result.get('err_msg')}")
            return None

        print(f"[성공] 적금 상품 {len(result.get('baseList', []))}개 받음")
        return result

    except Exception as e:
        print(f"[오류] API 호출 실패: {e}")
        return None