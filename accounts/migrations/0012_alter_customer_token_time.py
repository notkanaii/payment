# Generated by Django 4.1.7 on 2023-05-11 12:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0011_customer_token_time_invoice_create_time"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customer",
            name="token_time",
            field=models.CharField(max_length=50, null=True),
        ),
    ]