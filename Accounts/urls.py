from django.urls import path
from .views import register, account, transactions, getAccount, getAllAccount, createTransaction, home, othertransaction, profile

urlpatterns = [
    path('register/', register, name='register'),
    path('account/', account, name='account'),
    path('transactions/', transactions, name='transactions'),
    path('getaccount/<str:acc_no>/', getAccount, name='getAccount'),
    path('getall/', getAllAccount, name='getall'),
    path('createtransaction/', createTransaction, name='createTransaction'),
    path('home/', home, name='home'),
    path('othertransaction/', othertransaction, name='othertransaction'),
    path('profile/', profile, name='profile'),
]