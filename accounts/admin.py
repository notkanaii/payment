from django.contrib import admin

# Register your models here.
from .models import Customer, Invoice

admin.site.register(Customer)
admin.site.register(Invoice)