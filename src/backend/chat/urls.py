from django.contrib import admin
from django.urls import path,include
from .views import index,get_messages,logout_view

urlpatterns = [
    path('', index, name='home'),
    path('get_messages/<int:sender_id>/', get_messages),
    path('logout_user/<int:user_id>/',logout_view,name='logout_user')
]