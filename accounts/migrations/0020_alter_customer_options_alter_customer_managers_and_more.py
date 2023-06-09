# Generated by Django 4.1.7 on 2023-05-12 08:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0019_alter_customer_phone"),
    ]

    operations = [
        migrations.AlterModelOptions(name="customer", options={},),
        migrations.AlterModelManagers(name="customer", managers=[],),
        migrations.RemoveField(model_name="customer", name="date_joined",),
        migrations.RemoveField(model_name="customer", name="first_name",),
        migrations.RemoveField(model_name="customer", name="is_active",),
        migrations.RemoveField(model_name="customer", name="is_staff",),
        migrations.RemoveField(model_name="customer", name="last_name",),
        migrations.AlterField(
            model_name="customer",
            name="email",
            field=models.EmailField(max_length=254, unique=True),
        ),
        migrations.AlterField(
            model_name="customer",
            name="username",
            field=models.CharField(max_length=50, unique=True),
        ),
    ]
