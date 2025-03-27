from django.urls import path
from .views import get_address_info_view, get_soil_data, crop_recommendation_view

urlpatterns = [
    path('address/', get_address_info_view, name='address_info'), 
    path('soildata/', get_soil_data, name='soil_data'), 
    path('recommendation/', crop_recommendation_view, name='crop_recommendation'), 

]
