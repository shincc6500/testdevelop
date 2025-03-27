from django.contrib.auth import authenticate, login, logout, get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken

from .serializers import UserRegisterSerializer, UserSerializer, ProfileSerializer
from users.models import Profile

import requests



KAKAO_CLIENT_ID = "a6971a25bb35dc1113d81b5713a3ccc7"  # ✅ 여기에 본인의 카카오 REST API 키 입력
KAKAO_REDIRECT_URI = "http://127.0.0.1:8000/accounts/kakao/login/callback/"  # ✅ 카카오 로그인 리디렉트 URL

User = get_user_model()

@api_view(['POST'])

def kakao_login(request):
    """
    프론트엔드에서 카카오 OAuth2 인증 후 access_token을 전달받아 로그인 처리하는 API
    """
    kakao_code = request.data.get("code")
    if not kakao_code:
        return Response({"error": "인증 코드가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

    # 카카오 액세스 토큰 요청
    kakao_token_url = "https://kauth.kakao.com/oauth/token"
    data = {
        'grant_type': 'authorization_code',
        'client_id': '',
        'redirect_uri': 'http://127.0.0.1:8000/accounts/kakao/callback/',
        'code': kakao_code  # 받은 인증 코드
    }
    kakao_access_token = request.data.get("access_token")

    if not kakao_access_token:
        return Response({"error": "Access Token이 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

    kakao_user_info_url = "https://kapi.kakao.com/v2/user/me"
    headers = {"Authorization": f"Bearer {kakao_access_token}"}
    response = requests.get(kakao_user_info_url, headers=headers)
    if response.status_code != 200:
         return Response({"error": "실패", "details": response.json()}, status=response.status_code)

    # if response.status_code != 200:
    #     return Response({"error": "카카오 사용자 정보를 가져오는 데 실패했습니다."}, status=response.status_code)

    kakao_data = response.json()
    kakao_id = kakao_data.get("id")
    kakao_email = kakao_data.get("kakao_account", {}).get("email")

    if not kakao_email:
        return Response({"error": "이메일 정보가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

    user, created = User.objects.get_or_create(username=f"kakao_{kakao_id}", defaults={"email": kakao_email})

    # 로그인 처리 및 토큰 발급
    token, _ = Token.objects.get_or_create(user=user)
    #로그인 함수 그래야지 로그인세션 유지
    return Response({
        "message": "카카오 로그인 성공!",
        "user_id": user.id,
        "token": token.key
    }, status=status.HTTP_200_OK)

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    def post(self, request):
        user_data = {
            "username": request.data.get("username"),
            "email": request.data.get("email"),
            "password": request.data.get("password"),
            "first_name": request.data.get("first_name"),  # ✅ 이름 받기
        }

        profile_data = request.data.get("profile", {})

        user_serializer = UserRegisterSerializer(data=user_data)
        if user_serializer.is_valid():
            user = user_serializer.save()

            profile = Profile.objects.get(user=user)
            profile.birthdate = profile_data.get("birthdate")
            profile.region = profile_data.get("region")
            profile.crops = profile_data.get("crops", "")
            profile.equipment = profile_data.get("equipment", "")
            profile.save()

            return Response({"message": "회원가입 성공!", "user_id": user.id}, status=201)

        return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
def login_api(request):
    username = request.data.get("username")
    password = request.data.get("password")

    user = authenticate(username=username, password=password)
    if user is not None:
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            "message": "로그인 성공!",
            "token": token.key,
            "user_id": user.id,
            "username": user.username
        }, status=status.HTTP_200_OK)
    else:
        return Response({"message": "아이디 또는 비밀번호가 올바르지 않습니다."}, status=status.HTTP_401_UNAUTHORIZED)

class ProfileView(APIView):
    """
    사용자의 프로필 페이지를 조회하는 API 뷰
    """
    def get(self, request):
        try:
            # 사용자의 프로필을 가져옵니다
            profile = request.user.profile
        except Profile.DoesNotExist:
            # 프로필이 존재하지 않으면 예외 처리
            return Response({"message": "프로필이 없습니다. 프로필을 만드세요!"}, status=status.HTTP_404_NOT_FOUND)
        
        # 프로필이 존재하면 직렬화하여 반환
        serializer = ProfileSerializer(profile)
        return Response(serializer.data) 
    

class UserUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)  # 부분 업데이트 가능
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 회원 탈퇴 (DB 기록은 유지, 비활성화)
class UserDeleteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        user.is_active = False  # 계정을 비활성화 (DB 기록 유지)
        user.save()
        return Response({"message": "회원 탈퇴가 완료되었습니다."}, status=status.HTTP_200_OK)



class UserProfileAPIView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile = user.profile

        user_data = {
            "first_name": user.first_name,  # ✅ 이름 추가
            "username": user.username,
            "email": user.email,
            "birthdate": profile.birthdate,
            "region": profile.region,
            "crops": profile.crops,
            "equipment": profile.equipment,
        }
        return Response(user_data, status=200)


class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        token = Token.objects.get(key=response.data['token'])
        return Response({
            'token': token.key,
            'user_id': token.user_id,
            'username': token.user.username
        })
