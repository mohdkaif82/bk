"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from .routers import restricted_router,product_router,cart_router
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import url
from django.contrib import admin
from django.urls import path, include
from django.views.static import serve
from backend.doctors.views import (
    WalletDetailAPIView,
   
)
from backend.practice.viewsets import DoctorSearchAPIView
from rest_framework import routers
router = routers.DefaultRouter()
# from backend.accounts.viewsets import SignupView
urlpatterns = [
    path('admin/', admin.site.urls),
    path('chat/',include('backend.chat.urls')), 
    path('',include('backend.doctors.urls')),
    path('wallet/balance-detail/<int:pk>', WalletDetailAPIView.as_view(), name='wallet-detail'),
    path('api/doctors/', DoctorSearchAPIView.as_view(), name='doctor_search'),
    path('erp-api/password_reset/', include('django_rest_passwordreset.urls')),
    path('erp-api/', include(restricted_router.urls)),
    path('erp-api/', include(product_router.urls)),
    path('erp-api/', include(cart_router.urls)),
    
    url(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]+static(settings.MEDIA_URL,document_root=settings.MEDIA_ROOT)
