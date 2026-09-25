from django.db import models

# Create your models here.
class Customer(models.Model):
    cust_id=models.CharField(max_length=30)
    first_name=models.CharField(max_length=30)
    last_name=models.CharField(max_length=30)
    dob=models.DateField()
    gender=models.CharField(max_length=10)
    phone=models.IntegerField()
    email=models.EmailField(max_length=40)
    address=models.CharField(max_length=60)
    city=models.CharField(max_length=20)
    state=models.CharField(max_length=20)
    pincode=models.IntegerField()
    aadhar=models.IntegerField()
    pan=models.CharField(max_length=20)
    created_at=models.DateField()
    status=models.CharField(max_length=20)

    def __str__(self):
        return self.first_name


class Accounts(models.Model):
    acc_id=models.CharField(max_length=30)
    acc_no=models.CharField(max_length=30)
    acc_holder=models.CharField(max_length=30)
    cust_id=models.CharField(max_length=30)
    acc_type=models.CharField(max_length=30)
    balance=models.CharField(max_length=30,default=0)
    created_at=models.DateField()

    def __str__(self):
        return self.acc_holder


class Transactions(models.Model):
    transaction_id=models.CharField(max_length=10)
    acc_no=models.CharField(max_length=30)
    acc_name=models.CharField(max_length=30)
    transaction_type=models.CharField(max_length=30)
    amount=models.CharField(max_length=30)
    current_balance=models.CharField(max_length=30)
    balance_after=models.CharField(max_length=20)
    transaction_date=models.DateField()

    def __str__(self):
        return self.acc_name


class Othertransactions(models.Model):
    acc_no=models.CharField(max_length=30)
    name=models.CharField(max_length=30)
    bank=models.CharField(max_length=20,default=None)
    transaction_amount=models.CharField(max_length=30,default=None)
    balance=models.CharField(max_length=20)
    transaction_date=models.DateField()

    def __str__(self):
        return self.name