import datetime
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import Customer, Invoice


class TestInvoiceAPI(APITestCase):

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
        self.airline = Customer.objects.create(
            username='testairline',
            password='testpassword',
            customer_name='Test Airline',
            card_number='1234567890123456',
            card_password='testpassword',
            id_number='1234567',
            phone='12345678901',
            bank_account='12345678901234567890',
            balance=100000,
            token="testtoken2",
            token_time=datetime.datetime.now().isoformat()
        )

    def test_create_invoice(self):
        url = '/createinvoice/'
        data = {
            'airline_id': 'testairline',
            'total_price': 100.00,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_invoice_invalid_airline(self):
        url = '/createinvoice/'
        data = {
            'airline': 'invalidairline',
            'total_price': 100.00,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_invoice_invalid_price(self):
        url = '/createinvoice/'
        data = {
            'airline': 'testairline',
            'total_price': -100.00,
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)



class PayInvoiceTestCase(APITestCase):
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
        self.expired_customer = Customer.objects.create(
            username='testuser2',
            password='testpassword',
            customer_name='Test User2',
            card_number='1234567890123456',
            card_password='testpassword',
            id_number='1234567',
            phone='12345678901',
            bank_account='12345678901234567890',
            balance=100000,
            token="testtoken2",
            token_time=(datetime.datetime.now() - datetime.timedelta(days=31)).isoformat()
        )
        self.invoice = Invoice.objects.create(total_price='100', airline='testuser2', create_time=datetime.datetime.now())

    def test_payinvoice(self):
        url = '/payinvoice/'
        data = {'invoice_id': self.invoice.invoice_id, 'token': self.customer.token}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Invoice.objects.get(invoice_id=self.invoice.invoice_id).status, True)
        self.assertEqual(Invoice.objects.get(invoice_id=self.invoice.invoice_id).customer, Customer.objects.get(username='testuser'))
        self.assertEqual(Customer.objects.get(username='testuser').balance, Decimal('99900.00'))

    def test_invalid_token(self):
        url = '/payinvoice/'
        data = {'invoice_id': self.invoice.invoice_id, 'token': 'invalidtoken'}
        with self.assertRaises(Customer.DoesNotExist):
            self.client.post(url, data, format='json')

    def test_expired_token(self):
        url = '/payinvoice/'
        data = {'invoice_id': self.invoice.invoice_id, 'token': self.expired_customer.token}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data['Error'], 'Token expired')
        self.assertEqual(Customer.objects.get(username='testuser2').token, '')

    def test_no_token(self):
        url = '/payinvoice/'
        self.customer.token = ''
        self.customer.save()
        data = {'invoice_id': self.invoice.invoice_id, 'token': self.customer.token}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_invoice(self):
        url = '/payinvoice/'
        data = {'invoice_id': 9999, 'token': self.customer.token}
        with self.assertRaises(Invoice.DoesNotExist):
            self.client.post(url, data, format='json')

    def test_invalid_airline(self):
        self.invoice.airline = 'Invalid Airline'
        self.invoice.save()
        url = '/payinvoice/'
        data = {'invoice_id': self.invoice.invoice_id, 'token': self.customer.token}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data['Error'], 'Invalid airline')

    def test_expired_invoice(self):
        self.invoice.create_time = (datetime.datetime.now() - datetime.timedelta(minutes=20)).isoformat()
        self.invoice.save()
        url = '/payinvoice/'
        data = {'invoice_id': self.invoice.invoice_id, 'token': self.customer.token}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data['Error'], 'Invoice has expired')