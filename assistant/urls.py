from django.urls import path
from . import views

app_name = 'assistant'

urlpatterns = [
    path('', views.index_view, name='index'),
    path('api/chat/', views.chat_api_view, name='chat_api'),
]
