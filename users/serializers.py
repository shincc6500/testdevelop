from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Profile


User = get_user_model()

class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=False)  # ✅ 이름 필드 추가

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'first_name']  # ✅ 포함

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', '')  # ✅ 이름 저장
        )
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['birthdate', 'region', 'crops', 'equipment']
# serializers.py


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()  # 유저와 연결된 프로필 정보도 포함

    class Meta:
        model = User
        fields = ['id', 'username', 'email','first_name', 'password', 'profile']

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)

        # 유저 정보 업데이트
        if 'password' in validated_data:
            instance.set_password(validated_data['password'])
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 프로필 정보 업데이트
        if profile_data:
            profile = instance.profile
            for attr in ['birthdate', 'region', 'crops', 'equipment']:
                if attr in profile_data:
                    setattr(profile, attr, profile_data[attr])  # 전달된 값만 수정
            profile.save()

        return instance
# serializers.py
# 42~46번째는 패스워드를 업데이트 하는데 인스탠스객체에 업데이트, 49~53번째는 프로필 정보를 업데이트 하는데 인스탠스 객체에 업데이트 1
