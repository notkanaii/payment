# Generated by Django 4.1.7 on 2023-05-11 11:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0008_customer_token_time"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customer",
            name="token_time",
            field=models.CharField(default="", max_length=50, null=True),
        ),
    ]
