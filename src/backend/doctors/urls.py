"""wallet URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
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
from django.contrib import admin
from django.urls import path
from django.urls import path
from . import views
from .views import promo_code_list, offer_list, generate_promo_code, apply_promo_code

urlpatterns = [
    # # Deposit endpoint
    # path('api/wallet/deposit/', views.deposit_view, name='deposit'),
    
    # path('api/login/', login.user_login, name='api_login'),
    path('deposit/', views.deposit, name='api_deposit'),
    path('withdraw/', views.withdraw, name='api_withdraw'),
    path('history/', views.transaction_history, name='api_history'),
    path('api/promo-codes/', promo_code_list, name='promo-code-list'),
    path('api/offers/', offer_list, name='offer-list'),
    path('api/generate-promo-code/', generate_promo_code, name='generate-promo-code'),
    path('api/apply-promo-code/', apply_promo_code, name='apply-promo-code'),
    # # Withdrawal endpoint
    # path('api/wallet/withdraw/', views.withdraw_view, name='withdraw'),

    # # Transaction history endpoint
    # path('api/wallet/history/', views.transaction_history_view, name='transaction_history'),
]