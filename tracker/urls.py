from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('impose/', views.impose_audio, name='impose'),
    path('extract/', views.extract_audio, name='extract'),
]