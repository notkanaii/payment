# Generated by Django 4.1.7 on 2023-05-11 11:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0007_alter_customer_card_number"),
    ]

    operations = [
        migrations.AddField(
            model_name="customer",
            name="token_time",
            field=models.CharField(
                default="2023-05-11 04:18:23.395877+00:00", max_length=50
            ),
            preserve_default=False,
        ),
    ]
