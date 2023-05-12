from django.contrib.auth.base_user import BaseUserManager, AbstractBaseUser
from django.db import models
from django.contrib.auth.models import AbstractUser, PermissionsMixin


class CustomerManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

    def get_by_natural_key(self, email):
        """
        Retrieve a user by their natural key (email in this case).
        """
        return self.get(email=email)


class Customer(AbstractBaseUser, PermissionsMixin):
    id = models.AutoField(primary_key=True)
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=254, unique=True)
    id_number = models.CharField(max_length=50)
    phone = models.CharField(max_length=50)
    customer_name = models.CharField(max_length=100, unique=True)
    card_number = models.CharField(max_length=30)
    card_password = models.CharField(max_length=100)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    status = models.BooleanField(default=False)
    token_time = models.CharField(max_length=50, null=True)
    token = models.CharField(max_length=500, blank=True, null=True, default='')
    bank_account = models.CharField(max_length=100, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    objects = CustomerManager()



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
