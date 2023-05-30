from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
class Wallet(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

class Transaction(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=10)
    timestamp = models.DateTimeField(auto_now_add=True)

################################################################
###promocode
from django.db import models
import random
import string

from django.contrib.auth.models import User

class PromoCode(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    code = models.CharField(max_length=10, unique=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    active = models.BooleanField(default=True)
    used = models.BooleanField(default=False)

   

    def __str__(self):
        return self.code
    

    @classmethod
    def generate_code(cls):
        code_length = 8
        characters = string.ascii_uppercase + string.digits
        code = ''.join(random.choice(characters) for _ in range(code_length))
        return code


class Offer(models.Model):
    name = models.CharField(max_length=100)
    discount_percentage = models.PositiveIntegerField()
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name