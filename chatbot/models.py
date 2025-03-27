from django.db import models
import json

class CropRecommendation(models.Model):
    crop = models.CharField(max_length=100)
    reason = models.TextField()
    crop_info = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.crop

class Adressinformation(models.Model):
    pnucode = models.CharField(max_length=20)
    address = models.JSONField()
    point = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.pnucode


