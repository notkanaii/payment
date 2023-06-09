# Generated by Django 4.1.7 on 2023-05-11 04:49

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0004_invoice_create_time"),
    ]

    operations = [
        migrations.AlterField(
            model_name="invoice",
            name="customer",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="invoices",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
