from django.db import models
from django.contrib.auth.models import AbstractUser


class Customer(AbstractUser):
    id = models.AutoField(primary_key=True)
    customer_name = models.CharField(max_length=100, unique=True)
    card_number = models.BigIntegerField()
    card_password = models.CharField(max_length=100)
    id_number = models.CharField(max_length=100, unique=True)
    phone = models.BigIntegerField()
    bank_account = models.CharField(max_length=100, blank=True, null=True)
    access_token = models.CharField(max_length=500, blank=True, null=True, default='')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=100000)
    status = models.BooleanField(default=False)
    token_time = models.CharField(max_length=50, null=True, default='')

    def __str__(self):
        return self.username


class Invoice(models.Model):
    invoice_id = models.AutoField(primary_key=True)
    total_price = models.CharField(max_length=255)
    stamp = models.CharField(max_length=255)
    # stamp = 'S' + str(invoice_id)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, related_name='invoices')
    description = models.TextField()
    airline = models.CharField(max_length=50, default="Unknown")
    status = models.BooleanField(default=False)
    create_time = models.CharField(max_length=50)

    def __str__(self):
        return self.invoice_id
