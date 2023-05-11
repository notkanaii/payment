import datetime

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import Customer, Invoice


class DepositTestCase(APITestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            username='testuser',
            email='testuser@example.com',
            password='testpass',
            customer_name='Test User',
            card_number=123456789,
            card_password='testpass',
            id_number='123456789012345678',
            phone=1234567890,
            balance=100000,
            token='token',
            token_time=datetime.datetime.now().isoformat()
        )
        self.url = '/deposit/'

    def test_deposit_expired_token(self):
        self.customer.token_time = '2023-01-11 10:13:22.046348'
        self.customer.save()

        data = {
            'token': self.customer.token,
            'card_number': self.customer.card_number,
            'card_password': self.customer.card_password,
            'money': 100.0,
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

        self.customer.refresh_from_db()
        self.assertEqual(self.customer.balance, 100000.0)

    def test_deposit_successful(self):
        data = {
            'token': self.customer.token,
            'card_number': self.customer.card_number,
            'card_password': self.customer.card_password,
            'money': 100.0,
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.customer.refresh_from_db()
        self.assertEqual(self.customer.balance, 100100.0)

    def test_deposit_wrong_card_info(self):
        data = {
            'token': self.customer.token,
            'card_number': 1234567890123456,
            'card_password': 'wrongpass',
            'money': 100.0,
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

        self.customer.refresh_from_db()
        self.assertEqual(self.customer.balance, 100000.0)


class BalanceApiTestCase(APITestCase):
    def setUp(self):
        self.customer = Customer.objects.create_user(username='test_user', password='test_password',
                                                     customer_name='test_customer', card_number=1234567890123456,
                                                     card_password='test_card_password', id_number='1234567890',
                                                     phone=1234567890, balance=100000, token='token',
                                                     token_time='2023-05-11 10:13:22.046348')
        self.url = reverse('balance')

    def test_balance_valid_token(self):
        data = {
            'token': self.customer.token
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['Balance'], 100000)

    def test_balance_expired_token(self):
        self.customer.token_time = datetime.datetime.now() - datetime.timedelta(days=31)
        self.customer.save()
        data = {
            'token': self.customer.token
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data['Error'], 'Token expired')

    def test_balance_invalid_token(self):
        data = {
            'token': 'invalid_token'
        }
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data['Error'], 'Invalid user')


class StatementTest(APITestCase):
    def setUp(self):
        self.user = Customer.objects.create(
            username="testuser",
            password="testpass",
            customer_name="Test User",
            card_number=1234567890123456,
            card_password="password",
            id_number="123456789012345678",
            phone=1234567890,
            bank_account="1234567890",
            token="testtoken",
            balance=100000,
            status=False,
            token_time=datetime.datetime.now().isoformat()
        )
        self.invoice = Invoice.objects.create(
            total_price="100.00",
            stamp="S1",
            customer=self.user,
            description="Test invoice",
            airline="Test Airline",
            status=False,
            create_time=datetime.datetime.now().isoformat()
        )

    def test_statement_valid_token(self):
        url = reverse("statement")
        data = {"token": "testtoken"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["Invoices"][0]["invoice_id"], self.invoice.invoice_id)
        self.assertEqual(response.data["Invoices"][0]["total_price"], self.invoice.total_price)
        self.assertEqual(response.data["Invoices"][0]["status"], self.invoice.status)
        self.assertEqual(response.data["Invoices"][0]["create_time"], self.invoice.create_time)
        self.assertEqual(response.data["Invoices"][0]["stamp"], self.invoice.stamp)

    def test_statement_expired_token(self):
        self.user.token_time = (datetime.datetime.now() - datetime.timedelta(days=31)).isoformat()
        self.user.save()
        url = reverse("statement")
        data = {"token": "testtoken"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["Error"], "Token expired")

    def test_statement_invalid_token(self):
        url = reverse("statement")
        data = {"token": "invalidtoken"}
        response = self.client.post(url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data["Error"], "Invalid user")


class TransferTestCase(APITestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            username='testuser',
            password='testpassword',
            customer_name='Test User',
            card_number='1234567890123456',
            card_password='testpassword',
            id_number='123456',
            phone='12345678901',
            bank_account='12345678901234567890',
            balance=100000,
            token="testtoken1",
            token_time=datetime.datetime.now().isoformat()
        )
        self.customer2 = Customer.objects.create(
            username='testuser2',
            password='testpassword',
            customer_name='Test User 2',
            card_number='1234567890123456',
            card_password='testpassword',
            id_number='1234567',
            phone='12345678901',
            bank_account='12345678901234567890',
            balance=100000,
            token="testtoken2",
            token_time=datetime.datetime.now().isoformat()
        )

    def test_transfer(self):
        # 转账前的余额
        sender_balance_before = self.customer.balance
        receiver_balance_before = self.customer2.balance

        # 发送转账请求
        data = {
            "token": self.customer.token,
            "username": self.customer2.username,
            "money": 100,
            "card_password": self.customer.card_password
        }
        response = self.client.post('/transfer/', data)

        # 检查响应状态码和消息
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'Message': 'Transfer successful'})

        # 检查转账后的余额
        sender_balance_after = Customer.objects.get(username='testuser').balance
        receiver_balance_after = Customer.objects.get(username='testuser2').balance
        self.assertEqual(sender_balance_after, sender_balance_before - 100)
        self.assertEqual(receiver_balance_after, receiver_balance_before + 100)
