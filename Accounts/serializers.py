from rest_framework import serializers
from .models import Accounts,Transactions


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model=Accounts
        fields="__all__"


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model=Transactions
        fields="__all__"
