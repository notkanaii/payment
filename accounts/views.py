from datetime import timedelta, datetime
from decimal import Decimal

from django.contrib.auth import login
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.utils.timezone import make_aware
from rest_framework import status

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import DepositSerializer, BalanceSerializer, StatementSerializer, TransferSerializer, \
    CreateInvoiceSerializer, SignOutSerializer, PayInvoiceSerializer, InvoiceSerializer

from .models import Customer, Invoice
from .serializers import SignInSerializer
from .serializers import CustomerSerializer
from django.contrib.auth.hashers import check_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone


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
@permission_classes([AllowAny])
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
                token = generate_token(user)
                user.access_token = str(token['access'])
                user.status = True
                user.save()
                return Response(token, status=status.HTTP_200_OK)
            else:
                return Response({"Error": "Invalid email or password"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        else:
            return Response({"Error": "Invalid user"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


# -----------------------------------------signout
@api_view(["POST"])
def signout(request):
    serializer = SignOutSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    access_token = serializer.validated_data["access_token"]
    if access_token is not None:
        users = Customer.objects.filter(access_token=access_token)
        if users.exists():
            user = users.first()
            if user is not None:
                user.access_token = ''
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
    if serializer.is_valid():
        serializer.save()
        return Response({'Message': 'Deposit successful'})
    else:
        return Response(serializer.errors)


# -----------------------------------------balance
@api_view(['POST'])
def balance(request):
    serializer = BalanceSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    access_token = serializer.validated_data["access_token"]
    users = Customer.objects.filter(access_token=access_token)
    if users.exists():
        user = users.first()
        balance = user.balance
        return Response({"Balance": balance}, status=status.HTTP_200_OK)
    else:
        return Response({"Error": "Invalid user"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


# -----------------------------------------statement
@api_view(['POST'])
def statement(request):
    serializer = StatementSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    access_token = serializer.validated_data["access_token"]
    users = Customer.objects.filter(access_token=access_token)
    if users.exists():
        user = users.first()
        invoices = user.invoices.all()
        invoice_serializer = InvoiceSerializer(invoices, many=True)
        return Response({"Invoices": invoice_serializer.data}, status=status.HTTP_200_OK)
    else:
        return Response({"Error": "Invalid user"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)


# -----------------------------------------transfer
@api_view(['POST'])
def transfer(request):
    serializer = TransferSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    access_token = serializer.validated_data["access_token"]
    dest_account = serializer.validated_data["dest_account"]
    transfer_amount = serializer.validated_data["transfer_amount"]
    card_password = serializer.validated_data["card_password"]

    # 获取发送方和接收方客户对象
    try:
        sender = Customer.objects.get(access_token=access_token, card_password=card_password)
        receiver = Customer.objects.get(username=dest_account)
    except ObjectDoesNotExist:
        return Response({'Error': 'Wrong user'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    try:
        sender != receiver
    except ObjectDoesNotExist:
        return Response({'Error': 'Sender and receiver are the same'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # 确保发送方有足够的余额
    if sender.balance < transfer_amount:
        return Response({'Error': 'Balance not enough'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # 执行转账
    sender.balance -= transfer_amount
    receiver.balance += transfer_amount
    sender.save()
    receiver.save()

    return Response({'Message': 'Transfer successful'}, status=status.HTTP_200_OK)


# -----------------------------------------create invoice
@api_view(['POST'])
@transaction.atomic()
def createinvoice(request):
    serializer = CreateInvoiceSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    # access_token = serializer.validated_data["access_token"]
    invoice_id = serializer.validated_data["invoice_id"]
    create_time = serializer.validated_data["create_time"]
    stamp = serializer.validated_data["stamp"]

    invoice = Invoice.objects.get(invoice_id=invoice_id)
    invoice.description = f"Invoice {invoice_id} created at {create_time} stamp:{stamp}"
    invoice.stamp = stamp
    invoice.save()

    return Response({
        "invoice_id": invoice_id,
        "create_time": create_time,
        "stamp": stamp,
    }, status=status.HTTP_201_CREATED)


# -----------------------------------------pay invoice
@api_view(['POST'])
def payinvoice(request):
    serializer = PayInvoiceSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    invoice_id = serializer.validated_data['invoice_id']
    access_token = serializer.validated_data['access_token']

    # Validate the access token
    customer = Customer.objects.filter(access_token=access_token).first()

    if not customer:
        return Response({'Error': 'Invalid access token'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # Retrieve the invoice
    invoice = Invoice.objects.filter(invoice_id=invoice_id).first()
    if not invoice:
        return Response({'Error': 'Invoice not found'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    airline = Customer.objects.filter(username=invoice.airline).first()
    if not invoice:
        return Response({'Error': 'Invalid airline'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # Verify that the invoice has not been paid
    if invoice.status:
        return Response({'Error': 'Invoice has already been paid'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    c_time = datetime.fromisoformat(invoice.create_time)
    expiration_time = c_time + timedelta(minutes=15)
    if timezone.now() > expiration_time:
        invoice.delete()
        return Response({'Error': 'Invoice has expired'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # 验证转账金额是否足够
    if customer.balance < Decimal(invoice.total_price):
        return Response({'Error': 'Balance not enough'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # Update the invoice status
    invoice.status = True
    invoice.customer = customer
    customer.balance -= Decimal(invoice.total_price)
    invoice.save()
    customer.save()

    # Generate a stamp to verify payment completion
    stamp = invoice.stamp

    return Response({'Stamp': stamp}, status=status.HTTP_200_OK)
