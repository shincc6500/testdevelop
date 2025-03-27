# views.py
from django.http import JsonResponse
from django.shortcuts import render
from .utils import address_info,soilexam,SoilExamRAG
from .models import CropRecommendation,Adressinformation

def get_address_info_view(request):
    address = request.GET.get('address', '전라남도 해남군 산이면 덕송리 751')  # 디폴트 값 설정
    type = request.GET.get('type', 'PARCEL')  # 디폴트 값 설정
    
    if not address:
        return JsonResponse({"error": "주소를 입력해 주세요."}, status=400)
    
    add_info = address_info(type, address)
    if not add_info:
        return JsonResponse({"error": "유효하지 않은 주소입니다."}, status=400)
    if add_info:
        Adressinformation.objects.create(
            pnucode=add_info['id'],
            address=add_info['address'],
            point=add_info['point']
        )
    
    return JsonResponse({"address_information": add_info})

def get_soil_data(request):
    address = request.GET.get('address', '전라남도 해남군 산이면 덕송리 751')  # 디폴트 값 설정
    type = request.GET.get('type', 'PARCEL')  # 디폴트 값 설정
    
    if not address:
        return JsonResponse({"error": "주소를 입력해 주세요."}, status=400)
    
    add_info = address_info(type, address)
    PNU_Code = add_info['id']
    if not PNU_Code:
        return JsonResponse({"error": "PNU_Code를 찾을 수 없습니다."}, status=400)
    
    rag_system = SoilExamRAG(PNU_Code=PNU_Code)
    soil_data = rag_system.fetch_soil_data()
    if not soil_data :
        return JsonResponse({"message": "토지 정보를 얻지 못하였습니다."}, status=404)
    
    return JsonResponse({"soil_data": soil_data})

def crop_recommendation_view(request):
    address = request.GET.get('address', '전라남도 해남군 산이면 덕송리 751')  # 디폴트 값 설정
    type = request.GET.get('type', 'PARCEL')  # 디폴트 값 설정
    
    if not address:
        return JsonResponse({"error": "주소를 입력해 주세요."}, status=400)
    
    add_info = address_info(type, address)
    PNU_Code = add_info['id']
    if not PNU_Code:
        return JsonResponse({"error": "PNU_Code를 찾을 수 없습니다."}, status=400)
    
    rag_system = SoilExamRAG(PNU_Code=PNU_Code)
    recommendations = rag_system.get_recommendation()
    if not recommendations:
        return JsonResponse({"message": "토지 정보를 얻지 못하였습니다."}, status=404)
    
    for rec in recommendations:
        CropRecommendation.objects.create(
            crop=rec["crop"],
            reason=rec["reason"],
            crop_info=rec["crop_info"]
        )
    
    return JsonResponse({"recommendations": recommendations})