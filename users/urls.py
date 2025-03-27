from django.urls import path
from .views import UserUpdateAPIView, UserDeleteAPIView, UserProfileAPIView

from django.contrib.auth.views import LoginView
from django.contrib.auth.views import LogoutView
from .views import login_api,kakao_login
from .views import kakao_login, RegisterView , ProfileView, CustomAuthToken


urlpatterns = [
 
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", login_api, name="login_api"),
    path("api/kakao/login/", kakao_login, name="kakao_login"),
    path('profile/edit/', UserUpdateAPIView.as_view(), name='edit_profile'),
    path("update/", UserUpdateAPIView.as_view(), name="user_update"),
    path("delete/", UserDeleteAPIView.as_view(), name="user_delete"),
    path("profile/", UserProfileAPIView.as_view(), name="user-profile"),
]
