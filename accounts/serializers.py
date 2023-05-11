import datetime
import secrets

from django.contrib.auth import authenticate, login
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import Customer, Invoice
from django.contrib.auth.hashers import check_password, make_password
from rest_framework.response import Response
from django.utils import timezone


class CustomerSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(validators=[UniqueValidator(queryset=Customer.objects.all())])

    class Meta:
        model = Customer
        fields = (
            "id", "customer_name", "card_number", "card_password", "username", "email", "password", "id_number",
            "phone", "bank_account", "access_token", "balance", "status")

    def create(self, validated_data):
        password = validated_data.pop("password")
        hashed_password = make_password(password)
        customer = Customer.objects.create(
            customer_name=validated_data["customer_name"],
            card_number=validated_data["card_number"],
            card_password=validated_data["card_password"],
            username=validated_data["username"],
            email=validated_data["email"],
            id_number=validated_data["id_number"],
            phone=validated_data["phone"],
            bank_account=validated_data.get("bank_account", None),
            access_token=validated_data.get("access_token", ""),
            balance=validated_data.get("balance", 100000),
            status=validated_data.get("status", False),
            password=hashed_password
        )
        customer.save()
        return customer


class SignInSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class SignOutSerializer(serializers.Serializer):
    access_token = serializers.CharField()


# ------------------------------- DEPOSIT

class DepositSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    card_number = serializers.IntegerField()
    card_password = serializers.CharField()
    balance = serializers.DecimalField(max_digits=10, decimal_places=2)

    def validate(self, data):
        # 验证卡号和密码是否匹配
        try:
            customer = Customer.objects.get(access_token=data['access_token'])
            if customer.card_number != data['card_number'] or customer.card_password != data[
                'card_password']:  # card_number=data['card_number'], card_password=data['card_password']
                raise serializers.ValidationError({'Error': 'Wrong card number or password'})
        except Customer.DoesNotExist:
            raise serializers.ValidationError({'Error': 'Invalid token'})

        # 存储余额
        customer.balance += data['balance']
        customer.save()

        return data

    def create(self, validated_data):
        return Customer()


# -------------------------------GETBALANCE

class BalanceSerializer(serializers.Serializer):
    access_token = serializers.CharField()


# -------------------------------STATEMENT

class InvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invoice
        fields = ['invoice_id', 'total_price', 'status', 'create_time', 'stamp']


class StatementSerializer(serializers.Serializer):
    access_token = serializers.CharField()


# -------------------------------Transfer

class TransferSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    dest_account = serializers.CharField()
    transfer_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    card_password = serializers.CharField()

    def validate(self, data):
        # 验证访问令牌和卡密码是否匹配
        try:
            customer = Customer.objects.get(access_token=data['access_token'], card_password=data['card_password'])

        except ObjectDoesNotExist:
            raise serializers.ValidationError({'Error': 'Wrong token or card_password'})

        # 验证目标账户是否存在
        try:
            dest_customer = Customer.objects.get(username=data['dest_account'])
        except ObjectDoesNotExist:
            raise serializers.ValidationError({'Error': 'Find no receiver'})

        # 验证转账金额是否足够
        if customer.balance < data['transfer_amount']:
            raise serializers.ValidationError({'Error': 'Balance not enough'})

        return data


# ----------------------------CreateInvoice
class CreateInvoiceSerializer(serializers.Serializer):
    # access_token = serializers.CharField()
    airline = serializers.CharField()
    total_price = serializers.FloatField()

    def validate(self, data):
        # access_token = data.get("access_token")
        airline = data.get("airline")
        total_price = data.get("total_price")

        # 检查用户和航空公司是否存在
        try:
            # customer = Customer.objects.get(access_token=access_token, status=True)
            airline_check = Customer.objects.get(username=airline)
        except Customer.DoesNotExist:
            raise serializers.ValidationError("Invalid airline")

        # 检查价格是否合法
        if total_price <= 0:
            raise serializers.ValidationError("Invalid total price")

        while True:
            stamp = "S" + secrets.token_hex(5).upper()
            try:
                Invoice.objects.get(stamp=stamp)
            except Invoice.DoesNotExist:
                break

        # 创建invoice
        invoice = Invoice.objects.create(
            total_price=total_price,
            # customer=customer,
            airline=airline,
            status=False,
            stamp=stamp,
            create_time=datetime.now(),
        )

        data["invoice_id"] = invoice.invoice_id
        data["create_time"] = invoice.create_time
        data["stamp"] = invoice.stamp

        return data


# ----------------------------PayInvoice
class PayInvoiceSerializer(serializers.Serializer):
    invoice_id = serializers.CharField(max_length=100)
    access_token = serializers.CharField(max_length=500)

