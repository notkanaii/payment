# Generated by Django 4.1.7 on 2023-05-12 11:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0024_customer_bank_account"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customer",
            name="card_number",
            field=models.CharField(max_length=30),
        ),
    ]
