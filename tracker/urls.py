from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),

    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),

    path('send/', views.send_message, name='send_message'),
    path('inbox/', views.inbox, name='inbox'),
    path('outbox/', views.outbox, name='outbox'),
    path('message/<int:message_id>/', views.message_detail, name='message_detail'),

    path('impose/', views.impose_audio, name='impose'),
    path('extract/', views.extract_audio, name='extract'),
]