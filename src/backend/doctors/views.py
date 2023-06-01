from rest_framework import generics
from .models import Wallet
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .wallet import deposit_to_wallet, withdraw_from_wallet, get_transaction_history
from .serializers import WalletSerializer 
from rest_framework.response import Response

from django.http import JsonResponse
from rest_framework.views import APIView

from django.contrib.sessions.models import Session
from ..practice.models import PracticeStaff
from ..practice.serializers import PracticeStaffSerializer
from django.utils import timezone
from ..base import response
from ..accounts.models import User
class WalletDetailAPIView(generics.RetrieveAPIView):
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def deposit(request):
    amount = request.data.get('amount')
    if amount is not None:
        amount = float(amount)
        deposit_to_wallet(request.user, amount)
        return Response({f'message': 'Deposit successful {}'.format(amount)})
    else:
        return Response({'message': 'Invalid amount'}, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def withdraw(request):
    amount = request.data.get('amount')
    if amount is not None:
        amount = float(amount)
        try:
            withdraw_from_wallet(request.user, amount)
            return Response({'message': 'Withdrawal successful  {}'.format(amount)})
        except ValueError as e:
            return Response({'message': str(e)}, status=400)
    else:
        return Response({'message': 'Invalid amount'}, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transaction_history(request):
    transactions = get_transaction_history(request.user)
    history = []
    for transaction in transactions:
        history.append({
            'amount': transaction.amount,
            'transaction_type': transaction.transaction_type,
            'timestamp': transaction.timestamp
        })
    return Response({'transactions': history})

#####
### promocode_history
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import PromoCode, Offer
from .serializers import PromoCodeSerializer, OfferSerializer
import random

@api_view(['GET'])
def promo_code_list(request):
    promo_codes = PromoCode.objects.filter(active=True)
    serializer = PromoCodeSerializer(promo_codes, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def offer_list(request):
    offers = Offer.objects.filter(active=True)
    serializer = OfferSerializer(offers, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def generate_promo_code(request):
    user = request.user
    code = PromoCode.generate_code()
    discount_percentage = request.data.get('discount_percentage', 10)
    discount = random.randint(1, 100) * discount_percentage / 100
    active = request.data.get('active', True)
    promo_code = PromoCode(user=user,code=code, discount=discount, active=active,used=False)
    promo_code.save()
    serializer = PromoCodeSerializer(promo_code)
    return Response(serializer.data, status=201)

################################
from django.contrib.auth.decorators import login_required

# @api_view(['POST'])
# @login_required
# def generate_promo_code(request):
#     user = request.user
#     code = PromoCode.generate_code()
#     discount_percentage = random.randint(1, 20)
#     discount = discount_percentage / 100
#     active = True
#     promo_code = PromoCode(user=user, code=code, discount=discount, active=active, used=False)
#     promo_code.save()
#     serializer = PromoCodeSerializer(promo_code)
#     return Response(serializer.data, status=201)


@api_view(['POST'])
@login_required
def apply_promo_code(request):
    user = request.user
    code = request.data.get('code')
    try:
        promo_code = PromoCode.objects.get(code=code, user=user, active=True, used=False)
        promo_code.used = True
        promo_code.save()
        applied_discount = promo_code.discount if promo_code.discount >= 0.1 else 0.1
        return Response({'applied_discount': applied_discount}, status=200)
    except PromoCode.DoesNotExist:
        return Response({'detail': 'Invalid promo code'}, status=400)



class LiveDoctor(APIView):
    def get(self, request, *args, **kwargs):
        sessions = Session.objects.filter(expire_date__gte=timezone.now())
        uid_list = []
        # Build a list of user ids from that query
        for session in sessions:
            data = session.get_decoded()
            uid_list.append(data.get('_auth_user_id', None))
        livedoctor = PracticeStaff.objects.filter(user__in=uid_list)
        ser=PracticeStaffSerializer(livedoctor,many=True)
        return response.Ok({'live_doctor':ser.data})
    
    
    

