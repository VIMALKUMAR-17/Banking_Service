from django.shortcuts import render, redirect
from .models import Customer,Accounts,Transactions,Othertransactions
from django.utils import timezone
import random
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .serializers import AccountSerializer,TransactionSerializer
from django.contrib.auth.hashers import make_password,check_password
import requests

def register(request):
    if request.method == 'POST':
        cust_id = request.POST.get('cust_id')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        dob = request.POST.get('dob')
        gender = request.POST.get('gender')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        pincode = request.POST.get('pincode')
        aadhar = request.POST.get('aadhar')
        pan = request.POST.get('pan')
        created_at = request.POST.get('created_at')
        status = request.POST.get('status')
        today = timezone.localdate()

        if not cust_id:
            return render(request, 'registration.html', {'cust_error': '* Customer ID is required...','form_data': request.POST,"cust_id":cust_id,"today":today,"gender":gender,"status":status})
        if not first_name:
            return render(request, 'registration.html', {'first_name_error': '* First name is required...','form_data': request.POST,"cust_id":cust_id,"today":today,"gender":gender,"status":status})
        if not last_name:
            return render(request, 'registration.html', {'last_name_error': '* Last name is required...','form_data': request.POST,"cust_id":cust_id,"today":today,"gender":gender,"status":status})
        if not dob:
            return render(request, 'registration.html', {'dob_error': '* Date of birth is required...','form_data': request.POST,"cust_id":cust_id,"today":today,"gender":gender,"status":status})
        if not gender:
            return render(request, 'registration.html', {'gender_error': '* Gender is required...','form_data': request.POST,"cust_id":cust_id,"today":today,"gender":gender,"status":status})
        if not phone:
             return render(request, 'registration.html', {'phone_error': '* Phone Number is required...','form_data': request.POST,"cust_id":cust_id,"today":today,"gender":gender,"status":status})
        if not email:
            return render(request, 'registration.html', {'email_error': '* Email ID is required...','form_data': request.POST,"cust_id":cust_id,"today":today,"gender":gender,"status":status})
        if not address:
            return render(request, 'registration.html', {'address_error': '* Address is required...','form_data': request.POST,"cust_id":cust_id,"today":today,"gender":gender,"status":status})
        if not city:
            return render(request, 'registration.html', {'city_error': '* City is required...','form_data': request.POST,"cust_id":cust_id,"today":today,"gender":gender,"status":status})
        if not state:
            return render(request, 'registration.html', {'state_error': '* State is required...','form_data': request.POST,"cust_id":cust_id,"today":today,"gender":gender,"status":status})
        if not pincode:
            return render(request, 'registration.html', {'pincode_error': '* Pincode is required...','form_data': request.POST,"cust_id":cust_id,"today":today,"gender":gender,"status":status})
        if not aadhar:
             return render(request, 'registration.html', {'aadhar_error': '* Aadhar Number is required...','form_data': request.POST,"cust_id":cust_id,"today":today,"gender":gender,"status":status})
        if not pan:
             return render(request, 'registration.html', {'pan_error': '* Pan Number is required...','form_data': request.POST,"cust_id":cust_id,"today":today,"gender":gender,"status":status,"focus":"pan"})
        if not created_at:
            return render(request, 'registration.html', {'created_error': '* Created at is required...','form_data': request.POST,"cust_id":cust_id,"today":today,"gender":gender,"status":status})
        if not status:
            return render(request, 'registration.html', {'status_error': '* Status is required...','form_data': request.POST,"cust_id":cust_id,"today":today,"gender":gender,"status":status})


        
        if Customer.objects.filter(cust_id=cust_id).exists():
            return render(request,'registration.html',{'cust_error': '* Customer ID already exists...','form_data': request.POST,"cust_id":cust_id,"today":today,"gender":gender,"status":status})
        if Customer.objects.filter(aadhar=aadhar).exists():
            return render(request,'registration.html',{'aadhar_error':'* Aadhar number Already exists...','form_data':request.POST,"cust_id":cust_id,"today":today,"gender":gender,"status":status})
        if Customer.objects.filter(email=email).exists():
            return render(request,'registration.html',{'email_error': '* Email already exists...','form_data': request.POST,"cust_id":cust_id,"today":today,"gender":gender,"status":status})
        if Customer.objects.filter(pan=pan).exists():
            return render(request,'registration.html',{'pan_error': '* PAN number already exists...','form_data': request.POST,"cust_id":cust_id,"today":today,"gender":gender,"status":status})
        Customer.objects.create(
            cust_id=cust_id,
            first_name=first_name,
            last_name=last_name,
            dob=dob,
            gender=gender,
            phone=phone,
            email=email,
            address=address,
            city=city,
            state=state,
            pincode=pincode,
            aadhar=aadhar,
            pan=pan,
            created_at=created_at,
            status=status
        )
        return redirect('register')
    last_customer = Customer.objects.order_by("-id").first()
    if last_customer:
        number=int(last_customer.cust_id)+1
    else:
        number=100001
    today = timezone.localdate()
    return render(request, 'registration.html',{"cust_id":number,"today":today})




def account(request):
    last_customer = Accounts.objects.order_by("-id").first()
    if last_customer:
        last_number = int(last_customer.acc_id.replace("ACC", ""))
        number = f"ACC{last_number + 1:04d}"
    else:
        number = "ACC0001"
    acc=""
    today=timezone.localdate()
    if request.method == "POST":
        acc_id = request.POST.get("acc_id")
        acc_no = request.POST.get("acc_no")
        cust_id = request.POST.get("cust_id")
        acc_type = request.POST.get("acc_type")
        balance = request.POST.get("balance")
        created_at = request.POST.get("created_at")
        action = request.POST.get("action")


        if action == "check":
            if not Customer.objects.filter(cust_id=cust_id).exists():
                return render(request,"accounts.html",{"error": "* Customer ID does not exist","form_data": request.POST,"today": today,"number": number,"acc": acc})
            while True:
                acc = random.randint(100000, 999999)
                if not Accounts.objects.filter(acc_no=acc).exists():
                    break
            customer = Customer.objects.get(cust_id=cust_id)
            holder_name = customer.first_name
            return render(request,"accounts.html",{"holder_name": holder_name,"form_data": request.POST,"today": today,"number": number,"acc": acc})
        if action == "save":
            if not Customer.objects.filter(cust_id=cust_id).exists():
                return render(request,"accounts.html",{"error": "* Customer ID does not exist","today": today,"number": number,"acc": acc,"form_data": request.POST})
            customer = Customer.objects.get(cust_id=cust_id)
            holder_name = customer.first_name
            Accounts.objects.create(
                acc_id=acc_id,
                acc_no=acc_no,
                acc_holder=holder_name,
                cust_id=cust_id,
                acc_type=acc_type,
                balance=balance,
                created_at=created_at
            )
            return redirect("account")
    return render(request,"accounts.html",{"today": today,"number": number,"acc": acc})


def transactions(request):
    lastcustomer=Transactions.objects.order_by("-id").first()
    today = timezone.localdate()
    if lastcustomer:
        number=int(lastcustomer.transaction_id)+1
    else:
        number=1001
    if request.method=='POST':
        transaction_id=request.POST.get('transaction_id')
        acc_no=request.POST.get('acc_no')
        acc_name=request.POST.get('acc_name')
        transaction_type=request.POST.get('transaction_type')
        current_balance=request.POST.get('current_balance')
        amount=request.POST.get('amount')
        balance_after=request.POST.get('balance_after')
        transaction_date=request.POST.get('transaction_date')
        action=request.POST.get('action')

        if action=='check':
            if not acc_no:
                return render(request,'transactions.html',{'error':'* Account Number Required',"forms":request.POST,"number":number,"today":today,"acc_no":acc_no})
            if not Accounts.objects.filter(acc_no=acc_no).exists():
                return render(request,'transactions.html',{"error":"* Account number Mismatch","forms":request.POST,"number":number,"today":today,"acc_no":acc_no})
            acc=Accounts.objects.get(acc_no=acc_no)
            holder_name=acc.acc_holder
            balances=acc.balance
            return render(request,'transactions.html',{"forms":request.POST,'name':holder_name,"today":today,"acc_no":acc_no,"number":number,'balances':balances})
        elif action=="save":
            acc=Accounts.objects.get(acc_no=acc_no)
            acc.balance = balance_after
            acc.save()
            Transactions.objects.create(
            transaction_id=transaction_id,
            acc_no=acc_no,
            acc_name=acc_name,
            current_balance=current_balance,
            transaction_type=transaction_type,
            amount=amount,
            balance_after=balance_after,
            transaction_date=transaction_date,
        )  
            return redirect('transactions')
    return render(request,'transactions.html',{"number":number,"today":today})

@api_view(['GET'])
def getAccount(request,acc_no):
    try:
        account=Accounts.objects.get(acc_no=acc_no)
        serializer=AccountSerializer(account)
        return Response(serializer.data)
    except:
        return Response(
            {'error':"Account not found"}
        )


@api_view(['GET'])
def getAllAccount(request):
    try:
        account=Accounts.objects.all()
        serializer=AccountSerializer(account,many=True)
        return Response(serializer.data)
    except:
        return Response(
            {'error':"Account not found"}
        )


@api_view(['POST'])
def createTransaction(request):
    try:
        acc_no=request.data.get('acc_no')
        transaction_type=request.data.get('transaction_type')
        amount=request.data.get('amount')
        account = Accounts.objects.get(acc_no=acc_no)
        current_balance=float(account.balance)
        amount=float(amount)
        if transaction_type.lower()=='deposit':
            balance_after=current_balance+amount
        elif transaction_type.lower()=='withdraw':
            if amount>current_balance:
                return Response({'error':'Insufficient Balance'})
            balance_after=current_balance-amount
        else:
            return Response({'error':'Invalid Transaction Type'})
        lastcustomer=Transactions.objects.order_by("-id").first()
        today = timezone.localdate()
        if lastcustomer:
            number=int(lastcustomer.transaction_id)+1
        else:
            number=1001
        acc=Accounts.objects.get(acc_no=acc_no)
        name=acc.acc_holder
        transaction=Transactions.objects.create(
            transaction_id=number,
            acc_no=acc_no,
            acc_name=name,
            current_balance=current_balance,
            transaction_type=transaction_type,
            amount=amount,
            balance_after=balance_after,
            transaction_date=today
        )
        account.balance=balance_after
        account.save()
        serializer=TransactionSerializer(transaction)
        return Response({'message':'Transaction Successful','transaction':serializer.data})
    except Accounts.DoesNotExist:
        return Response({'error':"Account not found"})

def home(request):
    return render(request,'home.html')

def login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if (username == 'Vimal_17' and password == '12345') or \
           (username == 'Rohith_18' and password == '54321'):

            request.session['username'] = username

            return redirect('profile')

        else:
            return render(
                request,
                'login.html',
                {'error': '* Invalid Username And Password'}
            )

    return render(request, 'login.html')


def othertransaction(request):
    if request.method == 'POST':
        acc = request.POST.get('acc_no')
        action = request.POST.get('action')
        amount = request.POST.get('amount')
        bank = request.POST.get('banks')

        if not acc:
            return render(request, 'otherTransaction.html', {'acc_error': "* Enter the Account Number..", 'forms': request.POST})

        if bank == 'abc_bank':
            url1 = f"http://192.168.1.9:8000/getaccount/{acc}/"
            url2 = 'http://192.168.1.9:8000/transactionapi/'
        elif bank == 'vk_bank':
            url1 = f"http://127.0.0.1:8000/getaccount/{acc}/"
            url2 = 'http://127.0.0.1:8000/createtransaction/'
        else:
            return render(request, 'otherTransaction.html', {'bank_error': '* Please select the bank...', 'forms': request.POST})
        if action == 'check':
            try:
                response = requests.get(url1)                            
                data = response.json()
                if str(acc) != str(data.get('acc_no')):
                    return render(request, 'otherTransaction.html', {'acc_error': 'Account not found.', 'forms': request.POST})

                if bank == 'abc_bank':
                    response1 = requests.get(f'http://192.168.1.9:8000/getcustomer/{data["cust_id"]}/')
                    data1 = response1.json()
                    acc_name = data1.get('first_name')
                else: 
                    acc_name = data.get('acc_holder')
                balance = data.get('balance')
                return render(request, 'otherTransaction.html', {'Name': acc_name, 'forms': request.POST, 'balance': balance})
            except requests.exceptions.RequestException:
                return render(request, 'otherTransaction.html', {'error': 'Network error. Could not connect to bank server.', 'forms': request.POST})
        if action == 'withdraw':
            if not amount:
                return render(request, 'otherTransaction.html', {'forms': request.POST, 'with_error': '* Enter the Amount ...'})

            try:
                acc_response = requests.get(url1)

                if acc_response.status_code != 200:
                    return render(request, 'otherTransaction.html', {'error': 'Account not found.', 'forms': request.POST})

                datas = acc_response.json()
                
                if bank == 'abc_bank':
                    response1 = requests.get(f'http://192.168.1.9:8000/getcustomer/{datas["cust_id"]}/')
                    datas1 = response1.json()
                    acc_name = datas1.get('first_name')
                else:
                    acc_name = datas.get('acc_holder')
                bal = float(datas.get('balance', 0))
                if float(amount) > bal:
                    return render(request, 'otherTransaction.html', {'bal_error': '* Insufficient Balance...', 'forms': request.POST})
                payload = {'acc_no': acc, 'amount': amount, 'transaction_type': 'Withdraw'}
                headers = {'Content-Type': 'application/json'}
                response = requests.post(url2, json=payload, headers=headers)
                if response.status_code == 200:                    
                    new_balance = bal - float(amount) 
                    Othertransactions.objects.create(
                        acc_no=acc,
                        name=acc_name,
                        bank=bank,
                        transaction_amount=amount,
                        balance=new_balance,
                        transaction_date=timezone.localdate()
                    )
                    return render(request, 'otherTransaction.html', {'message': 'Withdraw Successful...', 'forms': request.POST})
                else:
                    return render(request, 'otherTransaction.html', {'message_error': 'Transaction rejected by server...', 'forms': request.POST})

            except requests.exceptions.RequestException:
                return render(request, 'otherTransaction.html', {'message_error': 'Network error. Transaction rejected...', 'forms': request.POST})

    return render(request, 'otherTransaction.html')