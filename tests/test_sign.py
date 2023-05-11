import json

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from accounts.models import Customer
from rest_framework.test import APITestCase
from accounts.serializers import CustomerSerializer


class test_Signup(TestCase):
    def setUp(self):
        self.client = APIClient()
        hashed_password = make_password("2019110004")
        self.valid_payload = {
            "email": "zjj@test.com",
            "password": "2019110004",
            "card_number": "2019110004",
            "card_password": "2019110004",
            "username": "zjj",
            "id_number": "2019110005",
            "balance": "10000",
            "customer_name": "zjj",
            "phone": "2019110004"
        }

    def test_signup_valid_payload(self):
        response = self.client.post(reverse('signup'), data=self.valid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Customer.objects.count(), 1)


class TestSignIn(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = '/signin/'
        self.valid_payload = {
            "email": "test@example.com",
            "password": "123456",
        }
        self.customer = Customer.objects.create(email="test@example.com", password=make_password("123456"),
                                                username="testname", card_number=2019110004, phone="2019110004")

    def test_signin_valid_credentials(self):
        data = {
            "email": "test@example.com", "password": "123456",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_signin_invalid_credentials(self):
        data = {
            'email': 'wrong@example.com',
            'password': "wrongpassword",
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
