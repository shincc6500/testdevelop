from django.db import models
from django.contrib.auth.models import AbstractUser, User
from django.conf import settings
from django.dispatch import receiver
from django.db.models.signals import post_save

class CustomUser(AbstractUser):
    pass
    # email = models.EmailField(unique=True)  # 이메일 필드
    # preferred_crop = models.CharField(max_length=50)  # 선호 작물 필드

    # def __str__(self):
    #     return self.username
    

class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,  # ✅ 여기가 핵심
        on_delete=models.CASCADE,
        related_name="profile"    
        )
    birthdate = models.DateField(null=True, blank=True)
    region = models.CharField(max_length=100, blank=True)
    crops = models.CharField(max_length=255, blank=True)
    equipment = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.user.username

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)