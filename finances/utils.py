import requests
from django.conf import settings

BASE_URL = "https://finlife.fss.or.kr/finlifeapi/depositProductsSearch.json"

def fetch_deposit_products():
    params = {
        "auth": settings.API_KEY,
        "topFinGrpNo": "020000",
        "pageNo": 1
    }
    response = requests.get(BASE_URL, params=params)
    # API 호출 실패 시 오류 출력
    if response.status_code != 200:
        print("HTTP ERROR:", response.status_code)
        print(response.text)
        return None
    
    data = response.json()
    return data["result"]
