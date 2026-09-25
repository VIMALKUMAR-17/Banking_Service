from django.contrib import admin
from .models import Customer,Accounts,Transactions,Othertransactions

# Register your models here.
admin.site.register(Customer)
admin.site.register(Accounts)
admin.site.register(Transactions)
admin.site.register(Othertransactions)
