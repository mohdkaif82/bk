from decimal import Decimal
from .models import Wallet, Transaction

def deposit_to_wallet(user, amount):
    wallet = Wallet.objects.get(user=user)
    wallet.balance += Decimal(str(amount))
    wallet.save()

    transaction = Transaction.objects.create(user=user, amount=Decimal(str(amount)), transaction_type='deposit')
    transaction.save()

def withdraw_from_wallet(user, amount):
    wallet = Wallet.objects.get(user=user)
    if wallet.balance >= Decimal(str(amount)):
        print(wallet.balance ,"Decimal")
        wallet.balance -= Decimal(str(amount))
        wallet.save()

        transaction = Transaction.objects.create(user=user, amount=Decimal(str(amount)), transaction_type='withdraw')
        transaction.save()
    else:
        raise ValueError("Sorry Insufficient balance in the wallet.")

def get_transaction_history(user):
    transactions = Transaction.objects.filter(user=user).order_by('-timestamp')
    return transactions
