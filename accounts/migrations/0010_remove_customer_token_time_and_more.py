# Generated by Django 4.1.7 on 2023-05-11 12:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0009_alter_customer_token_time"),
    ]

    operations = [
        migrations.RemoveField(model_name="customer", name="token_time",),
        migrations.RemoveField(model_name="invoice", name="create_time",),
    ]