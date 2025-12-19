import pandas as pd
from django.http import JsonResponse
from django.shortcuts import render

def get_price_data(request):
    try:
        # xlsx 파일 경로 지정
        asset_type = request.GET.get('asset_type')  # 'gold' 또는 'silver'
        
        if asset_type == 'gold':
            file_path = 'gold_silver/data/Gold_prices.xlsx'
        elif asset_type == 'silver':
            file_path = 'gold_silver/data/Silver_prices.xlsx'
        else:
            return JsonResponse({'status': 'error', 'message': '자산 유형이 올바르지 않습니다.'}, status=400)
        
        price_data = pd.read_excel(file_path)

        # 요청 파라미터로 날짜를 받기
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        if not start_date or not end_date:
            return JsonResponse({'status': 'error', 'message': '시작일과 종료일을 선택해주세요.'}, status=400)

        # 날짜 범위로 데이터를 필터링
        price_data['Date'] = pd.to_datetime(price_data['Date'])
        price_data = price_data[(price_data['Date'] >= start_date) & (price_data['Date'] <= end_date)]

        # 날짜와 가격만 필터링하여 반환
        price_data_dict = price_data[['Date', 'Close/Last']].to_dict(orient='records')
        return JsonResponse({'status': 'success', 'data': price_data_dict}, safe=False)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
