from datetime import timedelta, datetime
from decimal import Decimal

from django.contrib.auth import login
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from rest_framework import status

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import DepositSerializer, BalanceSerializer, StatementSerializer, TransferSerializer, \
    CreateInvoiceSerializer, SignOutSerializer, PayInvoiceSerializer, InvoiceSerializer

from .models import Customer, Invoice
from .serializers import SignInSerializer
from .serializers import CustomerSerializer
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken


def generate_token(user):
    refresh = RefreshToken.for_user(user)
    token = {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }
    return token


# -----------------------------------------signup
@api_view(["POST"])
def signup(request):
    serializer = CustomerSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"Message": "Sign up success"}, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_503_SERVICE_UNAVAILABLE)


# -----------------------------------------signin
@api_view(["POST"])
def signin(request):
    serializer = SignInSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"]
    password = serializer.validated_data["password"]
    if email and password:
        users = Customer.objects.filter(email=email)
        if users.exists():
            user = users.first()
            password_correct = check_password(password, user.password)
            if password_correct:
                login(request, user)
                token_generated = False
                while not token_generated:
                    token = generate_token(user)
                    # Check if the generated token already exists in the database
                    if not Customer.objects.filter(token=str(token['access'])).exists():
                        user.token = str(token['access'])
                        user.token_time = str(datetime.now())
                        user.status = True
                        user.save()
                        token_generated = True
                return Response({'token': token['access']}, status=status.HTTP_200_OK)
            else:
                return Response({"Message": "Invalid password"}, status=status.HTTP_404_NOT_FOUND)
        else:
            return Response({"Message": "Invalid user"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


# -----------------------------------------signout
@api_view(["POST"])
def signout(request):
    serializer = SignOutSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    token = serializer.validated_data["token"]
    if token is not None:
        users = Customer.objects.filter(token=token)
        if users.exists():
            user = users.first()
            if user is not None:
                user.token = ''
                user.status = False
                user.save()
                return Response({"Message": "Log out"}, status=status.HTTP_200_OK)
        else:
            return Response({"Message": "Invalid user"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


# -----------------------------------------deposit
@api_view(['POST'])
def deposit(request):
    serializer = DepositSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    token = serializer.validated_data["token"]
    money = serializer.validated_data["money"]
    card_password = serializer.validated_data["card_password"]
    card_number = serializer.validated_data["card_number"]

    customer = Customer.objects.get(token=token)
    if customer.token_time != '':
        customer_time = datetime.fromisoformat(customer.token_time)
        expiration_time = customer_time + timedelta(days=30)
        if datetime.now() > expiration_time:
            customer.token = ''
            customer.save()
            return Response({'Message': 'Token expired'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    else:
        return Response({'Message': 'No token'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    if serializer.is_valid():
        customer = Customer.objects.get(token=token)
        if customer.card_number != card_number or customer.card_password != card_password:  # card_number=data['card_number'], card_password=data['card_password']
            return Response({'Message': 'Wrong password or card number'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 存储余额
        customer.balance += money
        customer.save()
        return Response({'Message': 'Deposit successful'}, status=status.HTTP_200_OK)
    else:
        return Response(serializer.errors)


# -----------------------------------------balance
@api_view(['POST'])
def getbalance(request):
    serializer = BalanceSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    token = serializer.validated_data["token"]
    users = Customer.objects.filter(token=token)
    if users.exists():
        user = users.first()
        if user.token_time != '':
            customer_time = datetime.fromisoformat(user.token_time)
            expiration_time = customer_time + timedelta(days=30)
            if datetime.now() > expiration_time:
                user.token = ''
                return Response({'Message': 'Token expired'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        else:
            return Response({'Message': 'No token'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        balance = user.balance
        return Response({"Balance": balance}, status=status.HTTP_200_OK)
    else:
        return Response({"Message": "Invalid user"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


# -----------------------------------------statement
@api_view(['POST'])
def statement(request):
    serializer = StatementSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    token = serializer.validated_data["token"]
    users = Customer.objects.filter(token=token)
    if users.exists():
        user = users.first()
        if user.token_time != '':
            customer_time = datetime.fromisoformat(user.token_time)
            expiration_time = customer_time + timedelta(days=30)
            if datetime.now() > expiration_time:
                user.token = ''
                return Response({'Message': 'Token expired'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        else:
            return Response({'Message': 'No token'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        invoices = user.invoices.all()
        invoice_serializer = InvoiceSerializer(invoices, many=True)
        return Response({"Invoices": invoice_serializer.data}, status=status.HTTP_200_OK)
    else:
        return Response({"Message": "Invalid user"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


# -----------------------------------------transfer
@api_view(['POST'])
def transfer(request):
    serializer = TransferSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    token = serializer.validated_data["token"]
    username = serializer.validated_data["username"]
    money = serializer.validated_data["money"]
    card_password = serializer.validated_data["card_password"]

    customer = Customer.objects.get(token=token)
    if customer.token_time != '':
        customer_time = datetime.fromisoformat(customer.token_time)
        expiration_time = customer_time + timedelta(days=30)
        if datetime.now() > expiration_time:
            customer.token = ''
            customer.save()
            return Response({'Message': 'Token expired'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    else:
        return Response({'Message': 'No token'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # 获取发送方和接收方客户对象
    try:
        sender = Customer.objects.get(token=token, card_password=card_password)
        receiver = Customer.objects.get(username=username)
    except ObjectDoesNotExist:
        return Response({'Message': 'Wrong user'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    try:
        sender != receiver
    except ObjectDoesNotExist:
        return Response({'Message': 'Sender and receiver are the same'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # 确保发送方有足够的余额
    if sender.balance < money:
        return Response({'Message': 'Balance not enough'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # 执行转账
    sender.balance -= money
    receiver.balance += money
    sender.save()
    receiver.save()

    return Response({'Message': 'Transfer successful'}, status=status.HTTP_200_OK)


# -----------------------------------------create invoice
@api_view(['POST'])
@transaction.atomic()
def createinvoice(request):
    serializer = CreateInvoiceSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    invoice_id = serializer.validated_data["invoice_id"]
    create_time = serializer.validated_data["create_time"]
    stamp = serializer.validated_data["stamp"]
    airline_id = serializer.validated_data["airline_id"]

    try:
        # customer = Customer.objects.get(token=token, status=True)
        airline_check = Customer.objects.get(username=airline_id)
    except Customer.DoesNotExist:
        return Response({'Message': "Invalid airline"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    invoice = Invoice.objects.get(invoice_id=invoice_id)
    invoice.description = f"Invoice {invoice_id} created at {create_time} stamp:{stamp}"
    invoice.stamp = stamp
    invoice.save()
    return Response({'Message': {'stamp': stamp, 'invoice_id': invoice_id}}, status=status.HTTP_201_CREATED)


# -----------------------------------------pay invoice
@api_view(['POST'])
def payinvoice(request):
    serializer = PayInvoiceSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    invoice_id = serializer.validated_data['invoice_id']
    token = serializer.validated_data['token']

    customer = Customer.objects.get(token=token)

    # Validate the access token

    if not customer:
        return Response({'Message': 'Invalid access token'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    if customer.token_time != '':
        customer_time = datetime.fromisoformat(customer.token_time)
        expiration_time = customer_time + timedelta(days=30)
        if datetime.now() > expiration_time:
            customer.token = ''
            customer.save()
            return Response({'Message': 'Token expired'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    else:
        return Response({'Message': 'No token'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # Retrieve the invoice
    invoice = Invoice.objects.get(invoice_id=invoice_id)
    if not invoice:
        return Response({'Message': 'Invoice not found'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    airline = Customer.objects.filter(username=invoice.airline).first()
    if not airline:
        return Response({'Message': 'Invalid airline'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # Verify that the invoice has not been paid
    if invoice.status:
        return Response({'Message': 'Invoice has already been paid'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    c_time = datetime.fromisoformat(invoice.create_time)
    expiration_time = c_time + timedelta(minutes=15)
    if datetime.now() > expiration_time:
        invoice.delete()
        return Response({'Message': 'Invoice has expired'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # 验证转账金额是否足够
    if customer.balance < Decimal(invoice.total_price):
        return Response({'Message': 'Balance not enough'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # Update the invoice status
    invoice.status = True
    invoice.customer = customer
    customer.balance -= Decimal(invoice.total_price)
    invoice.save()
    customer.save()

    # Generate a stamp to verify payment completion
    stamp = invoice.stamp
    Message = {'stamp': stamp, 'invoice_id': invoice_id}
    return Response({'stamp': stamp}, status=status.HTTP_200_OK)
